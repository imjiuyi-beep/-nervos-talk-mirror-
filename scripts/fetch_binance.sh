#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data
python3 - <<'PYINNER'
import json, urllib.request, time
syms = ["CKBUSDT","BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","TRXUSDT"]
sources = ["https://data-api.binance.vision/api/v3/ticker/24hr", "https://api.binance.com/api/v3/ticker/24hr"]
out={}; errs=[]
for s in syms:
    got=False
    for base in sources:
        try:
            with urllib.request.urlopen(base+"?symbol="+s, timeout=15) as r:
                d=json.load(r)
                out[s]={"price":d.get("lastPrice"),"changePct":d.get("priceChangePercent"),
                        "high24h":d.get("highPrice"),"low24h":d.get("lowPrice"),
                        "vol24h":d.get("volume"),"quoteVol24h":d.get("quoteVolume"),"time":time.time()}
                got=True; break
        except Exception as e:
            errs.append(base+":"+type(e).__name__+":"+str(e))
    if not got:
        out[s]={"error":"all sources failed","time":time.time()}
out["_errors"]=errs[:3]
with open("data/binance_prices.json","w") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
print("errors:", errs[:3])
PYINNER
echo "done"
