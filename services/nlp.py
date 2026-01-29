import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"

embedder = SentenceTransformer("BAAI/bge-m3", device=device)

reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device=device)
