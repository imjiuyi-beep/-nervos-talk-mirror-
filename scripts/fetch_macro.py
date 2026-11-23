#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宏观流动性抓取 → data/macro.json
DXY/SPX/NDX 走 stooq(数据中心友好); M2 走 FRED(加长超时+重试, 可能被datacenter屏蔽则标记error)
"""
import urllib.request, json, datetime, os, io, csv, time

STOOQ={"dxy":"dx.f","spx":"^spx","ndx":"^ndx"}
FRED_ID={"m2":"M2SL"}

def _get(url,timeout=60):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req,timeout=timeout).read().decode("utf-8","ignore")

def fetch_stooq(sym):
    txt=_get(f"https://stooq.com/q/d/l/?s={sym}&i=d",60)
    rows=[]; r=csv.reader(io.StringIO(txt)); next(r)
    for row in r:
        if len(row)<5: continue
        try: rows.append([row[0],float(row[4])])
        except Exception: pass
    return rows

def fetch_fred(sid):
    txt=_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",120)
    rows=[]; r=csv.reader(io.StringIO(txt)); next(r)
    for row in r:
        if len(row)<2: continue
        if row[1] in ("","." ,"NA"): continue
        try: rows.append([row[0],float(row[1])])
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
    for k,sym in STOOQ.items():
        try:
            out["series"][k]=summ(fetch_stooq(sym)); print(k,"ok",out["series"][k].get("latest"),out["series"][k].get("latest_date"))
        except Exception as e:
            print(k,"ERR",str(e)[:100]); out["series"][k]={"error":str(e)[:100]}
    for k,sid in FRED_ID.items():
        ok=False
        for attempt in range(2):
            try:
                out["series"][k]=summ(fetch_fred(sid)); print(k,"ok",out["series"][k].get("latest"),out["series"][k].get("latest_date")); ok=True; break
            except Exception as e:
                print(k,"attempt",attempt,"ERR",str(e)[:80]); time.sleep(3)
        if not ok: out["series"][k]={"error":"fred unreachable from datacenter"}
    os.makedirs("data",exist_ok=True)
    with open("data/macro.json","w") as f: json.dump(out,f,ensure_ascii=False)
    print("saved data/macro.json")

if __name__=="__main__": main()
