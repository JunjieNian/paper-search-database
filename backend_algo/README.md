# 后端（算法层）：FastAPI

算法层负责对话、向量检索和推荐，不需要连关系数据库。

## 环境

后端使用 conda 管理环境：
```shell
conda create -n fastapi python=3.12
pip install -r requirements.txt
```

## 启动

先配置阿里百炼 / DashScope 的 OpenAI 兼容环境变量：
```shell
export VLLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export DASHSCOPE_API_KEY="你的百炼 API Key"
export LLM_MODEL="qwen-flash"
export EMBEDDING_MODEL="text-embedding-v4"
export EMBEDDING_DIMENSIONS="1024"
```

默认使用本地持久化 Chroma，不需要单独执行 `chroma run`。
向量数据会保存在项目根目录的 `chroma_data/`，也可以在 `backend_algo/.env` 里设置：
```shell
CHROMA_CLIENT_MODE=persistent
CHROMA_PERSIST_DIR=../chroma_data
```

启动：
```shell
uvicorn main:app --port 8003
```

文档页面：`http://127.0.0.1:8003/docs`

如果你想继续使用独立 Chroma 服务，可额外配置：
```shell
CHROMA_CLIENT_MODE=http
CHROMA_HOST=localhost
CHROMA_PORT=8002
```

如果你从本地 `all-MiniLM-L6-v2` 切到 `text-embedding-v4`，需要先删除旧索引目录再重建：
```shell
rm -rf ../chroma_data
```
