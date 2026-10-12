#!/usr/bin/env bash
# 抓取 Nervos Talk（talk.nervos.org）到仓库 data/ 目录
# 在 GitHub Actions 境外 runner 上运行，绕过本地网络对墙外域名的限制
set -e
mkdir -p data
# 1) 最新帖子列表（Discourse JSON，前 30 条）
curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/latest.json?per_page=30" -o data/latest.json || true
# 2) 最新帖子 RSS
curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/latest.rss" -o data/latest.rss || true
# 3) 固定关键专题
for t in 10936 10193 10732 10342; do
  curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/t/${t}.json" -o "data/topic_${t}.json" || true
done
# 4) 从 latest.json 动态提取所有 topic id 抓全文（覆盖新帖，自动镜像）
python3 - <<'PY' > /tmp/topic_ids.txt
import json
try:
    d = json.load(open('data/latest.json'))
    ids = [t['id'] for t in d.get('topic_list', {}).get('topics', []) if t.get('id')]
    print('\n'.join(str(i) for i in ids))
except Exception:
    pass
PY
while IFS= read -r t; do
  if [ -n "$t" ]; then
    curl -sS -m 40 -A "Mozilla/5.0" "https://talk.nervos.org/t/${t}.json" -o "data/topic_${t}.json" || true
  fi
done < /tmp/topic_ids.txt
echo "fetched files:"
ls data
