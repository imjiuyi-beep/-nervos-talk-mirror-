import os, time, json, urllib.request
from playwright.sync_api import sync_playwright

url = os.environ.get("FETCH_URL", "https://www.google.com")
name = os.environ.get("FETCH_NAME", "page")

# ---------- 1) JSON/纯API类 URL：直接 HTTP 抓，不走浏览器 ----------
if "publish.twitter.com/oembed" in url or url.endswith(".json") or "/api/" in url:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
        open(f"data/{name}_text.txt", "w", encoding="utf-8").write(body[:60000])
        open(f"data/{name}_page.html", "w", encoding="utf-8").write(body[:60000])
        print(f"fetched(api) {url}")
        raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"api fetch failed: {e}, fallback to browser")

# ---------- 2) 浏览器抓取（含 Cloudflare/X 增强） ----------
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
is_x = "x.com" in url or "twitter.com" in url

with sync_playwright() as p:
    b = p.chromium.launch(args=[
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
    ])
    ctx = b.new_context(
        user_agent=UA,
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        timezone_id="America/New_York",
    )
    # stealth: 隐藏 webdriver 痕迹
    ctx.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    """)
    pg = ctx.new_page()
    pg.goto(url, wait_until="domcontentloaded", timeout=90000)

    # Cloudflare/X challenge 等待：X 更严，等更久（最多 90s）
    max_wait = 18 if is_x else 8
    for i in range(max_wait):
        time.sleep(5)
        c = pg.content().lower()
        if "just a moment" not in c and "challenge" not in c and "security verification" not in c:
            break
        # X 登录墙：未登录也能看到部分内容，尝试关掉弹窗
        try:
            for sel in ["[data-testid='app-bar-close']", "[aria-label='Close']", "[data-testid='sheetDialogClose']"]:
                btn = pg.query_selector(sel)
                if btn:
                    btn.click()
                    time.sleep(2)
                    break
        except Exception:
            pass

    html = pg.content()
    open(f"data/{name}_page.html", "w", encoding="utf-8").write(html)
    try:
        txt = pg.inner_text("body")
    except Exception:
        txt = ""
    open(f"data/{name}_text.txt", "w", encoding="utf-8").write(txt[:30000])
    b.close()
print(f"fetched {url}")
