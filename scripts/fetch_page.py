import os, time
from playwright.sync_api import sync_playwright

url = os.environ.get("FETCH_URL", "https://www.google.com")
name = os.environ.get("FETCH_NAME", "page")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    pg = b.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    for _ in range(8):
        time.sleep(5)
        c = pg.content().lower()
        if "just a moment" not in c and "challenge" not in c:
            break
    html = pg.content()
    open(f"data/{name}_page.html", "w", encoding="utf-8").write(html)
    try:
        txt = pg.inner_text("body")
    except Exception:
        txt = ""
    open(f"data/{name}_text.txt", "w", encoding="utf-8").write(txt[:30000])
    b.close()
print(f"fetched {url}")
