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

## 可选 Rerank

如果你想在搜索阶段启用真正的二阶段重排，可在 `backend_algo/.env` 中设置：
```shell
RERANK_ENABLED=true
RERANK_PROVIDER=qwen
RERANK_MODEL=qwen3-rerank
RERANK_RECALL_K=60
RERANK_ENDPOINT=https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank
RERANK_INSTRUCT="Retrieve semantically similar academic paper abstracts relevant to the query."
RERANK_MAX_DOCUMENT_CHARS=1200
```

说明：
- `RERANK_ENABLED=false` 时，系统保持当前的一阶段向量检索。
- `RERANK_PROVIDER=qwen` 时，算法层会先向量召回，再调用 DashScope Rerank API 进行精排。
- 搜索请求也支持可选字段 `use_rerank`、`rerank_provider`、`recall_k`，可按请求覆盖默认配置。

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
