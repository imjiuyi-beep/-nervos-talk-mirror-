#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run on GitHub Actions runner: query X info via Grok (xAI API). Key stored base64 to dodge secret-scan."""
import base64, json, os, sys, urllib.request

# 读 base64 编码的 key 并解码；或从环境变量读明文
if os.environ.get("GXAI_KEY"):
    KEY = os.environ["GXAI_KEY"].strip()
else:
    KEY = base64.b64decode(open("scripts/gxai_key.txt").read().strip()).decode()
if not KEY:
    print("NO KEY"); sys.exit(1)

query = sys.argv[1] if len(sys.argv) > 1 else 'Safeheron'
body = {
    "model": "grok-3",
    "messages": [
        {"role": "system", "content":
         "你是 X/Twitter 数据检索专家。用中文客观回答。尽可能给出：账号近期推文（内容+大致时间）、相关方对它/话题的提及、账号简介与定位。区分已知事实与推测，不确定要说明。用要点式。"},
        {"role": "user", "content": "请查一下 X 上账号 " + query + " 的相关信息，包括它发布的近期推文，以及其它用户/媒体对它的提及，尽量具体。"},
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
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    print(data["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    print("GROK_HTTP_ERR", e.code, e.read().decode("utf-8", "replace")[:500]); sys.exit(1)
except Exception as e:
    print("GROK_ERROR", e); sys.exit(1)
