#!/usr/bin/env python3
"""
Molt Church 存档工具
自动抓取 molt.church 全站数据并保存为本地存档
支持增量更新
"""

import json
import os
import time
import hashlib
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

# 配置
BASE_URL = "https://molt.church"
ARCHIVE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ARCHIVE_DIR, "data")
HTML_DIR = os.path.join(ARCHIVE_DIR, "html")
LOG_FILE = os.path.join(ARCHIVE_DIR, "sync_log.json")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)


def fetch_json(url):
    """获取 JSON 数据"""
    try:
        req = Request(url, headers={"User-Agent": "MoltChurchArchiver/1.0"})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ❌ 获取失败 {url}: {e}")
        return None


def fetch_html(url):
    """获取 HTML 内容"""
    try:
        req = Request(url, headers={"User-Agent": "MoltChurchArchiver/1.0"})
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
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


def save_html(content, filename):
    """保存 HTML 内容"""
    filepath = os.path.join(HTML_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ 已保存: {filename}")
    return filepath


def load_log():
    """加载同步日志"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {"syncs": [], "last_sync": None}


def save_log(log):
    """保存同步日志"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def archive_status():
    """存档网站状态"""
    print("\n📊 获取网站状态...")
    data = fetch_json(f"{BASE_URL}/api/status")
    if data:
        save_json(data, "status.json")
        # 保存历史快照
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_json(data, f"status_{timestamp}.json")
    return data


def archive_prophets():
    """存档先知列表"""
    print("\n🦀 获取先知列表...")
    data = fetch_json(f"{BASE_URL}/api/prophets")
    if data:
        save_json(data, "prophets.json")
        print(f"  📋 共 {len(data.get('prophets', []))} 位先知")
    return data


def archive_blessed():
    """存档受祝福者列表"""
    print("\n✨ 获取受祝福者列表...")
    data = fetch_json(f"{BASE_URL}/api/blessed")
    if data:
        save_json(data, "blessed.json")
    return data


def archive_canon():
    """存档全部经文（分页获取）"""
    print("\n📖 获取经文（Great Book）...")
    all_verses = []
    page = 1
    per_page = 50

    while True:
        data = fetch_json(f"{BASE_URL}/api/canon?page={page}&per_page={per_page}")
        if not data or not data.get("the_great_book"):
            break

        verses = data["the_great_book"]
        all_verses.extend(verses)
        print(f"  📜 第 {page} 页: {len(verses)} 条经文")

        if len(verses) < per_page:
            break
        page += 1
        time.sleep(0.5)  # 礼貌请求

    if all_verses:
        save_json({
            "success": True,
            "total": len(all_verses),
            "the_great_book": all_verses
        }, "canon_full.json")
        print(f"  📚 共 {len(all_verses)} 条经文")

    return all_verses


def archive_html_pages():
    """存档 HTML 页面"""
    print("\n🌐 获取 HTML 页面...")

    pages = {
        "index.html": f"{BASE_URL}/",
        "gallery.html": f"{BASE_URL}/gallery.html",
    }

    for filename, url in pages.items():
        content = fetch_html(url)
        if content:
            save_html(content, filename)


def generate_summary(status, prophets, verses):
    """生成存档摘要"""
    print("\n📝 生成存档摘要...")

    summary = f"""# Molt Church 存档摘要
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 网站状态
- 先知数量: {status.get('prophets_filled', 'N/A')}/64
- 受祝福者: {status.get('blessed_count', 'N/A')}
- 会众规模: {status.get('congregation_size', 'N/A')}
- 经文总数: {status.get('canon_size', 'N/A')}

## 64 位先知
"""
    if prophets:
        for p in prophets.get("prophets", []):
            summary += f"{p['prophet_number']}. **{p['name']}** - 加入于 {p['joined_at'][:10]}\n"

    summary += f"\n## 经文统计\n"
    if verses:
        # 按类型统计
        types = {}
        for v in verses:
            t = v.get("scripture_type", "unknown")
            types[t] = types.get(t, 0) + 1

        for t, count in sorted(types.items(), key=lambda x: -x[1]):
            summary += f"- {t}: {count} 条\n"

        # 按作者统计
        authors = {}
        for v in verses:
            a = v.get("prophet_name", "unknown")
            authors[a] = authors.get(a, 0) + 1

        summary += f"\n## 经文作者排行（前 10）\n"
        for a, count in sorted(authors.items(), key=lambda x: -x[1])[:10]:
            summary += f"- {a}: {count} 条\n"

    filepath = os.path.join(ARCHIVE_DIR, "SUMMARY.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"  ✅ 已保存: SUMMARY.md")

    return summary


def run_archive():
    """执行完整存档"""
    print("=" * 60)
    print("🦀 Molt Church 存档工具")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    log = load_log()

    # 存档各部分
    status = archive_status()
    prophets = archive_prophets()
    blessed = archive_blessed()
    verses = archive_canon()
    archive_html_pages()

    # 生成摘要
    if status:
        generate_summary(status, prophets, verses)

    # 更新日志
    sync_record = {
        "time": datetime.now().isoformat(),
        "status": {
            "prophets": status.get("prophets_filled", 0) if status else 0,
            "congregation": status.get("congregation_size", 0) if status else 0,
            "canon": status.get("canon_size", 0) if status else 0,
        }
    }
    log["syncs"].append(sync_record)
    log["last_sync"] = sync_record["time"]
    save_log(log)

    print("\n" + "=" * 60)
    print("✅ 存档完成！")
    print(f"📁 存档目录: {ARCHIVE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    run_archive()
