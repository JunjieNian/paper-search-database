# Academic Paper Search & Recommend System

基于 Vue + FastAPI + ChromaDB + vLLM 的学术论文搜索与推荐系统。

## 架构

```
Frontend (Vue 3 + Element Plus)    :5173
    |
    | /api/* proxy
    v
Backend (FastAPI)                  :8000
    |
    | HTTP
    v
Algorithm Layer (FastAPI)          :8003
    |
    +---> vLLM (Qwen2.5-3B)       :11434   # LLM 对话
    +---> ChromaDB                 :8002    # 向量检索
```

## 前置依赖

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- NVIDIA GPU (运行 vLLM)

## 配置

所有配置通过环境变量设置，不设则使用默认值：

### MySQL (backend)

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MYSQL_USER` | `root` | 数据库用户名 |
| `MYSQL_PASSWORD` | *(空)* | 数据库密码 |
| `MYSQL_HOST` | `127.0.0.1` | 数据库地址 |
| `MYSQL_PORT` | `3306` | 数据库端口 |
| `MYSQL_DATABASE` | `test` | 数据库名 |
| `ALGO_URL` | `http://localhost:8003` | 算法层地址 |

### vLLM / LLM (backend_algo)

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `VLLM_BASE_URL` | `http://localhost:11434/v1` | vLLM OpenAI 兼容端点 |
| `VLLM_API_KEY` | `vllm` | vLLM API Key |
| `LLM_MODEL` | `qwen2.5-3b` | vLLM 中的模型名 |

## 启动步骤

### 1. 下载 LLM 模型

从 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-3B-Instruct) 或 [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) 下载 Qwen2.5-3B-Instruct 模型到本地。

### 2. 启动 vLLM

```bash
pip install vllm

# 将 /path/to/Qwen2.5-3B-Instruct 替换为实际模型路径
# 将 CUDA_VISIBLE_DEVICES 设为空闲 GPU 编号
CUDA_VISIBLE_DEVICES=0 vllm serve /path/to/Qwen2.5-3B-Instruct \
  --port 11434 \
  --api-key vllm \
  --served-model-name qwen2.5-3b \
  --gpu-memory-utilization 0.3 \
  --max-model-len 4096
```

验证：

```bash
curl http://localhost:11434/v1/models -H "Authorization: Bearer vllm"
```

### 3. 启动 ChromaDB

```bash
pip install chromadb

chroma run --host localhost --port 8002 --path ./chroma_data
```

### 4. 启动算法层

```bash
cd backend_algo
pip install fastapi uvicorn requests numpy chromadb

uvicorn main:app --host 0.0.0.0 --port 8003
```

### 5. 创建 MySQL 数据库

```sql
CREATE DATABASE IF NOT EXISTS test CHARACTER SET utf8mb4;
```

### 6. 启动业务层

```bash
cd backend
pip install fastapi uvicorn sqlalchemy pymysql pyjwt passlib[bcrypt] requests

# 如需自定义数据库连接:
# export MYSQL_PASSWORD=yourpassword
# export MYSQL_DATABASE=yourdb

uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7. 导入种子数据

```bash
cd backend
python seed_papers.py
```

这会向 MySQL 写入 120 篇 CS/AI 论文，并通过算法层索引到 ChromaDB。

### 8. 启动前端

```bash
cd frontend
npm install
npm run dev -- --host
```

### 9. 访问

浏览器打开 `http://localhost:5173`

## 功能

- **论文搜索**: 基于向量检索的语义搜索，支持搜索历史
- **论文推荐**: 根据用户浏览记录，基于 embedding 质心的协同过滤推荐
- **AI 对话**: 基于 Qwen2.5 的学术问答
- **论文详情**: 查看摘要、关键词，跳转 Google Scholar
- **用户系统**: 注册、登录、JWT 认证
