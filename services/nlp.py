from sentence_transformers import SentenceTransformer, CrossEncoder
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

embedder = SentenceTransformer("BAAI/bge-m3", device=device)

reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device=device)
