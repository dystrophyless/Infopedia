from sentence_transformers import SentenceTransformer, CrossEncoder

embedder: SentenceTransformer = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
reranker: CrossEncoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
