# 后端（算法层）：FastAPI

算法层负责对话、向量检索和推荐，不需要连关系数据库。

## 环境

后端使用conda管理环境：
```shell
conda create -n fastapi python=3.12
pip install -r requirements.txt
```

## 数据库

无

## 启动

先配置阿里百炼 / DashScope 的 OpenAI 兼容环境变量：
```shell
export VLLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export DASHSCOPE_API_KEY="你的百炼 API Key"
export LLM_MODEL="qwen-flash"            # 演示版推荐
export EMBEDDING_MODEL="text-embedding-v4"
export EMBEDDING_DIMENSIONS="1024"
```

向量数据库：
```shell
chroma run --path ../chroma_data --host localhost --port 8002
```

启动：
```shell
uvicorn main:app --port 8003
```

文档页面：`http://127.0.0.1:8003/docs`

如果你从本地 `all-MiniLM-L6-v2` 切到 `text-embedding-v4`，需要先删除旧索引目录再重建：
```shell
rm -rf ../chroma_data
```
