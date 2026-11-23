import json,urllib.request,datetime
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(r,timeout=20).read().decode()
out={"updated":datetime.datetime.utcnow().isoformat()+"Z"}
try:
    d=json.loads(get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"))
    out["funding_rate"]=float(d["data"][0]["fundingRate"]); out["funding_time"]=d["data"][0]["fundingTime"]
except Exception as e: out["funding_err"]=str(e)[:100]
try:
    d=json.loads(get("https://bitcoin-data.com/v1/mvrv/last"))
    out["mvrv"]=d.get("mvrv"); out["mvrv_date"]=d.get("d")
except Exception as e: out["mvrv_err"]=str(e)[:100]
try:
    d=json.loads(get("https://bitcoin-data.com/v1/realized-price/last"))
    out["realized_price"]=d.get("realizedPrice") or d.get("realized-price") or d.get("price")
except Exception as e: out["rp_err"]=str(e)[:60]
open("data/metrics.json","w").write(json.dumps(out,ensure_ascii=False,indent=1))
print(json.dumps(out))
