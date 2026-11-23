import re,json,time,datetime
from playwright.sync_api import sync_playwright
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox","--disable-blink-features=AutomationControlled","--disable-dev-shm-usage"])
    ctx=b.new_context(user_agent=UA,viewport={"width":1280,"height":900},locale="en-US")
    pg=ctx.new_page()
    pg.goto("https://farside.co.uk/btc/",wait_until="domcontentloaded",timeout=90000)
    for i in range(10):
        time.sleep(4)
        if "just a moment" not in pg.content().lower() and "challenge" not in pg.content().lower(): break
    txt=pg.inner_text("body")
    b.close()
lines=[l.strip() for l in txt.split("\n")]
date_re=re.compile(r"^(\d{1,2} \w{3} \d{4})$")
rows=[];i=0
while i<len(lines):
    m=date_re.match(lines[i])
    if m:
        j=i+1;val=None
        while j<len(lines) and j<i+6:
            s=lines[j].replace(" ","")
            if re.match(r"^\(?-?[0-9]+(\.[0-9]+)?\)?$",s):
                val=float(s.replace("(","-").replace(")",""));break
            j+=1
        if val is not None: rows.append({"date":m.group(1),"total_m":val})
    i+=1
out={"updated":datetime.datetime.utcnow().isoformat()+"Z","rows":rows[:40],
     "sum_7d":round(sum(r["total_m"] for r in rows[:7]),1),
     "sum_14d":round(sum(r["total_m"] for r in rows[:14]),1),
     "pos_14d":sum(1 for r in rows[:14] if r["total_m"]>0)}
open("data/etf.json","w").write(json.dumps(out,ensure_ascii=False,indent=1))
print(json.dumps(out,ensure_ascii=False)[:400])
