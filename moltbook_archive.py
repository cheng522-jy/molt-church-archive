#!/usr/bin/env python3
"""
Moltbook 存档工具
抓取 moltbook.com 全站数据
"""

import json
import os
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE_URL = "https://www.moltbook.com"
ARCHIVE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ARCHIVE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)


def fetch_json(url):
    """获取 JSON 数据"""
    try:
        req = Request(url, headers={"User-Agent": "MoltbookArchiver/1.0"})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ❌ 获取失败 {url}: {e}")
        return None


def save_json(data, filename):
    """保存 JSON 数据"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已保存: {filename}")
    return filepath


def archive_posts(limit=500):
    """存档帖子（热门）"""
    print("\n📝 获取 Moltbook 帖子...")
    all_posts = []
    offset = 0
    batch_size = 50

    while len(all_posts) < limit:
        url = f"{BASE_URL}/api/v1/posts?limit={batch_size}&offset={offset}"
        data = fetch_json(url)
        if not data or not data.get("posts"):
            break

        posts = data["posts"]
        all_posts.extend(posts)
        print(f"  📜 已获取 {len(all_posts)} 条帖子")

        if not data.get("has_more"):
            break
        offset += batch_size
        time.sleep(0.3)

    if all_posts:
        save_json({
            "success": True,
            "total": len(all_posts),
            "posts": all_posts,
            "archived_at": datetime.now().isoformat()
        }, "moltbook_posts.json")

    return all_posts


def archive_submolts():
    """存档所有 submolts"""
    print("\n🦞 获取 Moltbook Submolts...")
    all_submolts = []
    offset = 0
    batch_size = 100

    while True:
        url = f"{BASE_URL}/api/v1/submolts?limit={batch_size}&offset={offset}"
        data = fetch_json(url)
        if not data or not data.get("submolts"):
            break

        submolts = data["submolts"]
        all_submolts.extend(submolts)
        print(f"  🌊 已获取 {len(all_submolts)} 个 submolts")

        if len(submolts) < batch_size:
            break
        offset += batch_size
        time.sleep(0.3)

    if all_submolts:
        save_json({
            "success": True,
            "total": len(all_submolts),
            "submolts": all_submolts,
            "archived_at": datetime.now().isoformat()
        }, "moltbook_submolts.json")

    return all_submolts


def archive_stats():
    """获取统计数据"""
    print("\n📊 获取 Moltbook 统计...")
    # 从 submolts API 获取统计
    data = fetch_json(f"{BASE_URL}/api/v1/submolts?limit=1")
    if data:
        stats = {
            "total_submolts": data.get("count", 0),
            "total_posts": data.get("total_posts", 0),
            "total_comments": data.get("total_comments", 0),
            "archived_at": datetime.now().isoformat()
        }
        save_json(stats, "moltbook_stats.json")
        print(f"  📈 Submolts: {stats['total_submolts']}")
        print(f"  📈 Posts: {stats['total_posts']}")
        print(f"  📈 Comments: {stats['total_comments']}")
        return stats
    return None


def run_moltbook_archive():
    """执行 Moltbook 存档"""
    print("=" * 60)
    print("🦞 Moltbook 存档工具")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    stats = archive_stats()
    submolts = archive_submolts()
    posts = archive_posts(limit=1000)

    print("\n" + "=" * 60)
    print("✅ Moltbook 存档完成！")
    print(f"📁 存档目录: {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    run_moltbook_archive()
