# Academic Paper Search & Recommend System

基于 **Vue 3 + FastAPI + MySQL + ChromaDB + Qwen** 的学术论文语义搜索与个性化推荐系统。

系统采用三层微服务架构（界面层 / 业务层 / 算法层），融合向量语义检索、Embedding 质心推荐、可选 Reranker 精排、以及 LLM 驱动的学术问答。

---

## 前置依赖

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

## 快速启动

```bash
# 一键启动全部服务（前端 + 业务层 + 算法层）
bash start_all.sh

# 一键停止
bash stop_all.sh
```

> MySQL 需预先启动。

## 新机器从零启动

1. **克隆仓库并安装依赖**

```bash
git clone git@github.com:JunjieNian/paper-search-database.git
cd paper-search-database

python3 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt
pip install -r backend_algo/requirements.txt
cd frontend && npm install && cd ..
```

2. **复制配置模板并填写**

```bash
cp backend/.env.example backend/.env
cp backend_algo/.env.example backend_algo/.env
cp frontend/.env.development.example frontend/.env.development.local
```

- `backend/.env`：填写 `MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`、`SECRET_KEY`
- `backend_algo/.env`：填写 `DASHSCOPE_API_KEY`

3. **创建 MySQL 数据库**

```sql
CREATE DATABASE paper_search CHARACTER SET utf8mb4;
```

4. **启动服务**（三个终端或使用 `start_all.sh`）

```bash
# 终端 1 — 算法层
cd backend_algo && python -m uvicorn main:app --host 0.0.0.0 --port 8003

# 终端 2 — 业务后端
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 终端 3 — 前端
cd frontend && npm run dev -- --host 0.0.0.0
```

或一键启动：

```bash
bash start_all.sh
```

5. **导入种子数据**（120 篇来自 OpenAlex 的真实论文）

```bash
cd backend && python seed_papers.py
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 业务层 API 文档 | http://localhost:8000/docs |
| 算法层 API 文档 | http://localhost:8003/docs |

## 运行实验

```bash
cd experiments
pip install -r requirements.txt
python run_all.py
```

结果保存在 `experiments/results/` 目录（JSON 格式）。

## 项目结构

```
mysql_fastapi_vue_project/
├── frontend/                  # Vue 3 + Element Plus 前端
├── backend/                   # FastAPI + MySQL 业务层
├── backend_algo/              # FastAPI + ChromaDB 算法层
├── experiments/               # 算法分析实验（8 组）
├── report/                    # 项目报告（LaTeX）
├── start_all.sh / stop_all.sh # 一键启停脚本
└── README.md
```

详细的系统设计、数据库设计、算法说明、实验结果及用户手册请参见 `report/main.pdf`。

## License

MIT
