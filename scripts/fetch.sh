#!/usr/bin/env bash
# 抓取 Nervos Talk（talk.nervos.org）到仓库 data/ 目录
# 在 GitHub Actions 境外 runner 上运行，绕过本地网络对墙外域名的限制
set -e
mkdir -p data
# 1) 最新帖子列表（Discourse JSON，前 30 条）——固定名覆盖，便于读取最新
curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/latest.json?per_page=30" -o "data/latest.json" || true
# 2) 最新帖子 RSS
curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/latest.rss" -o "data/latest.rss" || true
# 3) 关键专题（可后续追加：重要帖子/板块 id）
for t in 10936 10193 10732 10342; do
  curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/t/${t}.json" -o "data/topic_${t}.json" || true
done
# 4) 带时间戳存档（便于追踪历史增量）
TS=$(date -u +%Y%m%d%H%M)
cp data/latest.json "data/archive_${TS}.json" 2>/dev/null || true
echo "fetched files: $(ls data | wc -l)"
