#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宏观流动性抓取(FRED, 无需key) → data/macro.json
境外 runner 运行; 供 BTC 框架接入宏观维度(M2/DXY/美股)
"""
import urllib.request, json, datetime, os, io, csv

FRED="https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SERIES={"m2":"M2SL","dxy":"DTWEXBGS","spx":"SP500","ndx":"NASDAQCOM"}

def fetch(sid):
    req=urllib.request.Request(FRED.format(sid),headers={"User-Agent":"Mozilla/5.0"})
    txt=urllib.request.urlopen(req,timeout=60).read().decode("utf-8","ignore")
    rows=[]; r=csv.reader(io.StringIO(txt)); next(r)
    for row in r:
        if len(row)<2: continue
        d,v=row[0],row[1]
        if v in ("","." ,"NA"): continue
        try: rows.append([d,float(v)])
        except Exception: pass
    return rows

def summ(rows,n=500):
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
    for k,sid in SERIES.items():
        try:
            out["series"][k]=summ(fetch(sid)); print(k,"ok",out["series"][k].get("latest"),out["series"][k].get("latest_date"))
        except Exception as e:
            print(k,"ERR",str(e)[:100]); out["series"][k]={"error":str(e)[:100]}
    os.makedirs("data",exist_ok=True)
    with open("data/macro.json","w") as f: json.dump(out,f,ensure_ascii=False)
    print("saved data/macro.json")

if __name__=="__main__": main()
