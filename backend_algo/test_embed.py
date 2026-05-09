import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

ef = DefaultEmbeddingFunction()

sentences = [
    "What is the capital of France?",
    "The capital of Brazil is Brasilia.",
    "The capital of France is Paris.",
    "Horses and cows are both animals",
]

embeddings_raw = ef(sentences)

for emb in embeddings_raw:
    print(len(emb))  # 打印向量维度 (384)
print()

embeddings = [np.array(emb) for emb in embeddings_raw]

for i in range(0, 1):
    for j in range(1, 4):
        print(sentences[i])
        print(sentences[j])
        print('distance:', np.sum((embeddings[i] - embeddings[j])**2))
        print()
