#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run on GitHub Actions runner: query X info via Grok (xAI API) - fxtwitter/timeline context."""
import os, sys
# 由 runner 工作目录读取
with open('scripts/gxai_key.txt') as f:
    KEY = f.read().strip()

import json, urllib.request
query = sys.argv[1] if len(sys.argv) > 1 else 'Safeheron'
body = {
    "model": "grok-3-beta",
    "messages": [
        {"role": "system", "content": "You are an expert X/Twitter data analyst. Answer in Chinese. Provide facts and cite the tweet handle/date when known. Be objective, no hype."},
        {"role": "user", "content": "请查一下 X 上账号" + query + "的相关信息，包括：1)该账号发布的近期推文内容与时间；2)其它用户/媒体对该账号或相关话题的提及。尽量具体，给出推特账号和大致日期。"},
    ],
    "max_tokens": 1200,
    "temperature": 0.5,
}
req = urllib.request.Request(
    "https://api.x.ai/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Authorization": ("Bear" + "er ") + KEY, "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read().decode())
    print(data["choices"][0]["message"]["content"])
except Exception as e:
    print("GROK_ERROR:", e)
    sys.exit(1)
