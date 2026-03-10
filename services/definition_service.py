import asyncio
import logging
import math
from collections.abc import Callable

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_search import get_definition_candidates
from database.models import Definition

logger = logging.getLogger(__name__)


def _scaled_sigmoid(x: float, temperature: float = 0.5) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x * temperature))
    except (OverflowError, ValueError):
        return 0.0 if x < 0 else 1.0


class DefinitionService:
    def __init__(self, embedder, reranker):
        self.embedder = embedder
        self.reranker = reranker

    async def find_best(
        self,
        session: AsyncSession,
        *,
        query: str,
        top_k: int = 30,
        alpha: float = 0.75,
        combined_threshold: float = 0.55,
        margin_threshold: float = 0.05,
        exact_fallback_threshold: float = 0.85,
        use_adaptive_alpha: bool = True,
        min_candidates_for_decision: int = 3,
        on_stage: Callable | None = None,
    ) -> Definition | None:
        async def stage(name: str):
            if on_stage:
                await on_stage(name)

        # --- 1. Эмбеддинг ---
        await stage("embedding")

        try:
            # безопасный вызов encode в отдельном потоке
            def encode_sync(q):
                return self.embedder.encode(
                    q,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )

            qvec = await asyncio.to_thread(encode_sync, query)

        except Exception:
            logger.exception("Ошибка эмбеддинга")
            return None

        qvec = np.asarray(qvec).ravel()
        if np.isnan(qvec).any():
            return None

        await asyncio.sleep(0)  # даём шанс event loop переключиться

        # --- 2. SQL поиск ---
        await stage("searching")
        try:
            rows = await get_definition_candidates(session, qvec.tolist(), top_k=top_k)
        except Exception:
            logger.exception("Ошибка SQL")
            return None
        if not rows:
            return None
        await asyncio.sleep(0)

        # --- остальной код без изменений ---
        candidates, texts = [], []
        for definition, _ in rows:
            emb_raw = definition.embedding
            if emb_raw is None:
                continue
            emb_array = np.asarray(emb_raw, dtype=float).ravel()
            if emb_array.size == 0:
                continue
            exact_sim = float(np.dot(qvec, emb_array))
            candidates.append((definition, exact_sim))
            texts.append(definition.text)

        if len(candidates) < min_candidates_for_decision:
            return None

        # --- 3. Реранкинг ---
        await stage("reranking")
        try:
            rerank_raw = await asyncio.to_thread(
                self.reranker.predict,
                [(query, t) for t in texts],
            )
            rerank_raw = np.asarray(rerank_raw, dtype=float).ravel()
        except Exception:
            logger.exception("Ошибка реранкера")
            rerank_raw = np.zeros(len(candidates))
        await asyncio.sleep(0)

        exact_norm = np.clip([c[1] for c in candidates], 0.0, 1.0)
        rerank_norm = np.array([_scaled_sigmoid(x) for x in rerank_raw])

        if use_adaptive_alpha:
            top_vec_idx = np.argsort(exact_norm)[-5:][::-1]
            top_rer_idx = np.argsort(rerank_norm)[-5:][::-1]
            intersection = len(set(top_vec_idx) & set(top_rer_idx))
            adaptive_alpha = max(alpha * (0.5 + 0.5 * (intersection / 5.0)), 0.50)
        else:
            adaptive_alpha = alpha

        query_words = set(query.lower().split())
        keyword_bonus = np.zeros(len(candidates))
        for i, (definition, _) in enumerate(candidates):
            try:
                term_name = definition.source.term.name.lower()
                def_text = definition.text.lower()
                t_int = len(query_words & set(term_name.split()))
                d_int = len(query_words & set(def_text.split()))
                keyword_bonus[i] = min(
                    ((t_int * 2.5 + d_int) / (len(query_words) * 3.5)) * 0.1,
                    0.1,
                )
            except:
                pass

        combined = (
            (adaptive_alpha * rerank_norm)
            + ((1.0 - adaptive_alpha) * exact_norm)
            + keyword_bonus
        )
        enriched = []
        for i, (definition, _) in enumerate(candidates):
            enriched.append(
                {
                    "definition": definition,
                    "exact_norm": float(exact_norm[i]),
                    "rerank_raw": float(rerank_raw[i]),
                    "rerank_norm": float(rerank_norm[i]),
                    "combined": float(combined[i]),
                    "keyword_bonus": float(keyword_bonus[i]),
                },
            )

        enriched_sorted = sorted(enriched, key=lambda x: x["combined"], reverse=True)
        unique_terms = []
        seen_ids = set()
        for item in enriched_sorted:
            tid = item["definition"].source.term.id
            if tid not in seen_ids:
                unique_terms.append(item)
                seen_ids.add(tid)

        if len(unique_terms) > 1:
            best_by_rerank = max(unique_terms[:10], key=lambda x: x["rerank_raw"])
            current_top = unique_terms[0]

            if best_by_rerank["rerank_raw"] > 0.85 and best_by_rerank != current_top:
                logger.debug("--- Rerank Rescue Triggered ---")
                logger.debug(
                    "Moving `%s` (raw: %.4f) above `%s` (raw: %.4f)",
                    best_by_rerank["definition"].source.term.name,
                    best_by_rerank["rerank_raw"],
                    current_top["definition"].source.term.name,
                    current_top["rerank_raw"],
                )
                unique_terms.remove(best_by_rerank)
                unique_terms.insert(0, best_by_rerank)

        if not unique_terms:
            return None
        best = unique_terms[0]
        second = unique_terms[1] if len(unique_terms) > 1 else None
        margin = best["combined"] - second["combined"] if second else 1.0

        # --- 4. Финальная стадия ---
        await stage("deciding")
        await asyncio.sleep(0)

        logger.debug("Query: %r | Alpha: %.2f", query, adaptive_alpha)
        logger.debug("Top Candidates:")
        for idx, info in enumerate(unique_terms[:10], start=1):
            logger.debug(
                " #%02d: %s | exact:%.4f | rerank_raw:%.4f | combined:%.4f",
                idx,
                info["definition"].source.term.name[:30],
                info["exact_norm"],
                info["rerank_raw"],
                info["combined"],
            )

        if best["rerank_raw"] > 0.83:
            logger.debug(
                "Decision: Принято по высокому реранку (%.4f)",
                best["rerank_raw"],
            )
            return best["definition"]

        if second and second["rerank_raw"] > (best["rerank_raw"] + 0.15):
            logger.debug("Decision: Override в пользу #2")
            return second["definition"]

        if best["combined"] > combined_threshold:
            if margin >= margin_threshold or best["combined"] > 0.63:
                logger.debug(
                    "Decision: Принято по Combined/Margin (%.4f)",
                    best["combined"],
                )
                return best["definition"]

        logger.debug(
            "Decision: Отклонено (Margin: %.4f, Combined: %.4f)",
            margin,
            best["combined"],
        )
        return None

    async def get_search_result(
        self,
        session: AsyncSession,
        *,
        query: str,
        on_stage: Callable | None = None,
    ) -> tuple[Definition, dict] | tuple[None, None]:
        definition: Definition = await self.find_best(
            session,
            query=query,
            on_stage=on_stage,
        )

        if not definition:
            return None, None

        info: dict = {
            "term": definition.source.term.name,
            "source": definition.source.name,
            "text": definition.text,
            "topic": definition.topic.name,
            "page": definition.page,
        }

        return definition, info
