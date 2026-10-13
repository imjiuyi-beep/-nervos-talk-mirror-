#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data
python3 - <<'PY'
import json, urllib.request, time
syms = ["CKBUSDT","BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","TRXUSDT"]
out={}
for s in syms:
    try:
        with urllib.request.urlopen(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=15) as r:
            d=json.load(r)
            out[s]={"price":d.get("lastPrice"),"changePct":d.get("priceChangePercent"),
                    "high24h":d.get("highPrice"),"low24h":d.get("lowPrice"),
                    "vol24h":d.get("volume"),"quoteVol24h":d.get("quoteVolume"),"time":time.time()}
    except Exception as e:
        out[s]={"error":str(e),"time":time.time()}
with open("data/binance_prices.json","w") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
PY
echo "binance prices updated: $(date -u +%F\ %T)"
