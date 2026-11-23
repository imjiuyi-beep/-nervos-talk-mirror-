#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宏观流动性抓取 → data/macro.json
Yahoo Finance chart API (对datacenter相对友好): DXY/SPX/NDX
M2: FRED对datacenter屏蔽,暂无免费可达源, 保留占位
"""
import urllib.request, json, datetime, os

YF={"dxy":"DX-Y.NYB","spx":"^GSPC","ndx":"^IXIC"}

def fetch_yahoo(sym):
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=10y&interval=1d"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    d=json.loads(urllib.request.urlopen(req,timeout=45).read().decode())
    r=d["chart"]["result"][0]
    ts=r.get("timestamp") or []
    close=r["indicators"]["quote"][0].get("close") or []
    rows=[]
    for t,c in zip(ts,close):
        if c is None: continue
        rows.append([datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),float(c)])
    return rows

def summ(rows,n=2600):
    if not rows: return {"error":"empty"}
    recent=rows[-n:]; latest=rows[-1]
    out={"latest_date":latest[0],"latest":latest[1],"series":recent}
    if len(rows)>252:
        old=rows[-253][1]
        if old: out["yoy_pct"]=round((latest[1]/old-1)*100,2)
    if len(rows)>90:
        old=rows[-91][1]
        if old: out["chg90_pct"]=round((latest[1]/old-1)*100,2)
    vals=[v for _,v in rows]
    out["pct_all"]=round(sum(1 for x in vals if x<latest[1])/len(vals)*100,1)
    return out

def main():
    out={"updated":datetime.datetime.utcnow().isoformat()+"Z","series":{}}
    for k,sym in YF.items():
        try:
            out["series"][k]=summ(fetch_yahoo(sym)); print(k,"ok",out["series"][k].get("latest"),out["series"][k].get("latest_date"),"pts",len(out["series"][k].get("series",[])))
        except Exception as e:
            print(k,"ERR",str(e)[:120]); out["series"][k]={"error":str(e)[:120]}
    out["series"]["m2"]={"error":"no free datacenter-accessible source (FRED blocked)"}
    os.makedirs("data",exist_ok=True)
    with open("data/macro.json","w") as f: json.dump(out,f,ensure_ascii=False)
    print("saved data/macro.json")

if __name__=="__main__": main()
