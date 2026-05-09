import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

default_ef = DefaultEmbeddingFunction()

# 注意：需要先启动向量数据库，参考README.md
client = chromadb.HttpClient(host='localhost', port=8002)

# 创建collection，指定embedding_function
collection = client.create_collection(name="my_collection", embedding_function=default_ef)

# 插入数据
collection.add(ids=[
    "id0",
    "id1",
    "id2",
], documents=[
    "The capital of Brazil is Brasilia.",
    "The capital of France is Paris.",
    "Horses and cows are both animals",
])

# 这句这里是可以不写的，这里写是提醒get_collection时同样需要指定embedding_function
collection = client.get_collection(name="my_collection", embedding_function=default_ef)

print(collection.get('id0'))
print(collection.get('id3'))

print(collection.query(query_texts=[
    "What is the capital of France?",
    "What is the capital of Brazil?",
], n_results=2))  # 向量检索，批量的，可以输入多个query，对每个query检索n_results个结果

# 清理测试 collection
client.delete_collection(name="my_collection")
print("测试完成，已清理 my_collection")

# 其他操作请参考文档：
# https://docs.trychroma.com/docs/overview/introduction
