import json
import reranker

results = reranker.rerank(
    query="What is the capital of France?",
    documents=[
        "The capital of Brazil is Brasilia.",
        "The capital of France is Paris.",
        "Horses and cows are both animals",
    ],
    top_n=2,
)

print("Rerank results:")
print(json.dumps(results, indent=2))
