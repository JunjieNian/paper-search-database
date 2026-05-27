from uuid import uuid4

from vector_store import embed_texts, get_client

client = get_client()
collection_name = f"my_collection_{uuid4().hex[:8]}"
collection = client.create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"},
)

documents = [
    "The capital of Brazil is Brasilia.",
    "The capital of France is Paris.",
    "Horses and cows are both animals",
]
collection.add(
    ids=["id0", "id1", "id2"],
    documents=documents,
    embeddings=embed_texts(documents),
)

collection = client.get_collection(name=collection_name)

print(collection.get("id0"))
print(collection.get("id3"))

query_embeddings = embed_texts([
    "What is the capital of France?",
    "What is the capital of Brazil?",
])
print(collection.query(query_embeddings=query_embeddings, n_results=2))

client.delete_collection(name=collection_name)
print(f"测试完成，已清理 {collection_name}")
