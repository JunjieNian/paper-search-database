"""
种子脚本：读取 papers.json → 写入 MySQL → 调用算法层 /index 索引到 ChromaDB
用法: cd backend && python seed_papers.py
"""
import json
import os
import sys
import requests

from database import SessionLocal
from models import Paper, Base
from database import engine

# 确保表已创建
Base.metadata.create_all(bind=engine)


def main():
    # 1. 读取 JSON
    with open("seed_data/papers.json", "r", encoding="utf-8") as f:
        papers_data = json.load(f)

    print(f"读取到 {len(papers_data)} 篇论文")

    # 2. 写入 MySQL
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing = db.query(Paper).count()
        if existing > 0:
            print(f"数据库中已有 {existing} 篇论文，跳过 MySQL 导入")
        else:
            db_papers = []
            for p in papers_data:
                db_paper = Paper(
                    title=p["title"],
                    abstract=p["abstract"],
                    authors=p["authors"],
                    venue=p["venue"],
                    year=p["year"],
                    keywords=p["keywords"],
                    url=p.get("url", ""),
                )
                db_papers.append(db_paper)
            db.add_all(db_papers)
            db.commit()
            print(f"成功导入 {len(db_papers)} 篇论文到 MySQL")

        # 3. 从 MySQL 读取所有论文（获取 ID）
        all_papers = db.query(Paper).all()
        index_data = [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "keywords": p.keywords or "",
            }
            for p in all_papers
        ]
    finally:
        db.close()

    # 4. 调用算法层 /index 索引到 ChromaDB
    algo_base_url = os.getenv("ALGO_URL", "http://localhost:8003").rstrip("/")
    algo_url = f"{algo_base_url}/index"
    batch_size = 50
    total_indexed = 0

    for i in range(0, len(index_data), batch_size):
        batch = index_data[i:i + batch_size]
        try:
            resp = requests.post(algo_url, json={"papers": batch}, timeout=120)
            resp.raise_for_status()
            count = resp.json().get("indexed_count", 0)
            total_indexed += count
            print(f"批次 {i // batch_size + 1}: 索引了 {count} 篇论文")
        except Exception as e:
            print(f"批次 {i // batch_size + 1} 索引失败: {e}")
            sys.exit(1)

    print(f"全部完成！共索引 {total_indexed} 篇论文到 ChromaDB")


if __name__ == "__main__":
    main()
