import numpy as np
from config import EMBEDDING_DIMENSIONS
from vector_store import embed_texts

sentences = [
    "What is the capital of France?",
    "The capital of Brazil is Brasilia.",
    "The capital of France is Paris.",
    "Horses and cows are both animals",
]

embeddings_raw = embed_texts(sentences)

for emb in embeddings_raw:
    print(len(emb))  # 打印向量维度（默认 1024）
print()

embeddings = [np.array(emb) for emb in embeddings_raw]

for i in range(0, 1):
    for j in range(1, 4):
        print(sentences[i])
        print(sentences[j])
        print('distance:', np.sum((embeddings[i] - embeddings[j])**2))
        print()

print(f"expected dimensions: {EMBEDDING_DIMENSIONS}")
