"""
并发压测实验
使用 asyncio + aiohttp 模拟并发搜索请求
测试系统在不同并发级别下的吞吐量和延迟
"""
import sys
import os
import time
import json
import asyncio

import aiohttp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import ground_truth as gt_module


# 并发级别
CONCURRENCY_LEVELS = [1, 5, 10, 20, 50]
# 每级别总请求数
REQUESTS_PER_LEVEL = 50


async def _login(session: aiohttp.ClientSession) -> str:
    """登录获取 token (使用默认测试用户)"""
    data = aiohttp.FormData()
    data.add_field("username", "admin")
    data.add_field("password", "admin")
    async with session.post(
        f"{config.BACKEND_URL}/token", data=data
    ) as resp:
        if resp.status == 200:
            result = await resp.json()
            return result["access_token"]
    return ""


async def _search_request(session: aiohttp.ClientSession, token: str,
                          query: str) -> dict:
    """发送一次搜索请求，返回延迟和状态"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query, "page": 1, "page_size": 10}

    t0 = time.perf_counter()
    try:
        async with session.post(
            f"{config.BACKEND_URL}/search",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            elapsed = (time.perf_counter() - t0) * 1000
            status = resp.status
            return {"latency_ms": elapsed, "status": status, "success": status == 200}
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return {"latency_ms": elapsed, "status": 0, "success": False, "error": str(e)}


async def _run_concurrent_batch(token: str, queries: list,
                                concurrency: int, total_requests: int) -> list:
    """运行一组并发请求"""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async with aiohttp.ClientSession() as session:
        async def bounded_request(query):
            async with semaphore:
                return await _search_request(session, token, query)

        tasks = []
        for i in range(total_requests):
            query = queries[i % len(queries)]
            tasks.append(bounded_request(query))

        results = await asyncio.gather(*tasks)

    return list(results)


async def _async_run():
    """异步运行并发测试"""
    queries = gt_module.get_query_list()[:20]  # 取 20 个查询

    # 登录
    try:
        async with aiohttp.ClientSession() as session:
            token = await _login(session)
    except Exception as e:
        print(f"  [WARNING] 无法连接后端服务: {e}")
        token = ""

    if not token:
        print("  [WARNING] 无法登录，跳过并发测试")
        print("  请确保 backend 运行中且存在 admin/admin 用户")
        return {}

    results = {}

    for concurrency in CONCURRENCY_LEVELS:
        print(f"\n  Concurrency={concurrency}, "
              f"total_requests={REQUESTS_PER_LEVEL}...")

        t0 = time.perf_counter()
        batch_results = await _run_concurrent_batch(
            token, queries, concurrency, REQUESTS_PER_LEVEL,
        )
        wall_time = (time.perf_counter() - t0) * 1000

        latencies = [r["latency_ms"] for r in batch_results]
        successes = sum(1 for r in batch_results if r["success"])

        results[f"c{concurrency}"] = {
            "concurrency": concurrency,
            "total_requests": REQUESTS_PER_LEVEL,
            "success_count": successes,
            "success_rate": successes / REQUESTS_PER_LEVEL,
            "wall_time_ms": float(wall_time),
            "throughput_rps": REQUESTS_PER_LEVEL / (wall_time / 1000),
            "avg_latency_ms": float(np.mean(latencies)),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "p99_latency_ms": float(np.percentile(latencies, 99)),
            "max_latency_ms": float(np.max(latencies)),
        }

    return results


def run():
    """运行并发压测"""
    print("=" * 60)
    print("实验 9: 并发压测")
    print("=" * 60)

    results = asyncio.run(_async_run())

    if not results:
        return {}

    # 打印
    print("\n" + "-" * 90)
    print(f"{'Concurrency':<13} {'Success%':<10} {'Throughput':<12} "
          f"{'Avg(ms)':<10} {'P50(ms)':<10} {'P95(ms)':<10} {'P99(ms)':<10}")
    print("-" * 90)
    for label, vals in results.items():
        print(f"{vals['concurrency']:<13} "
              f"{vals['success_rate']:<10.1%} "
              f"{vals['throughput_rps']:<12.1f} "
              f"{vals['avg_latency_ms']:<10.1f} "
              f"{vals['p50_latency_ms']:<10.1f} "
              f"{vals['p95_latency_ms']:<10.1f} "
              f"{vals['p99_latency_ms']:<10.1f}")
    print("-" * 90)

    # 保存
    output_path = os.path.join(config.RESULTS_DIR, "concurrent_test.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")

    return results


if __name__ == "__main__":
    run()
