import json
import asyncio
from playwright.async_api import async_playwright

SESSION_FILE = "session.json"
OUTPUT_FILE = "products.json"
LOGIN_URL = "https://<iden-challenge-url>/login"  # replace with real login url

USERNAME = "your-username"
PASSWORD = "your-password"

async def save_session(context):
    session = await context.storage_state()
    with open(SESSION_FILE, "w") as f:
        f.write(json.dumps(session))

async def load_session(playwright):
    if not os.path.exists(SESSION_FILE):
        return None
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state=SESSION_FILE)
    return context

async def run():
    async with async_playwright() as p:
        # try loading existing session
        context = await load_session(p)
        if context:
            page = await context.new_page()
        else:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # login flow
            await page.goto(LOGIN_URL)
            await page.fill("input[name='username']", USERNAME)
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button[type='submit']")
            await page.wait_for_selector("text=Dashboard")  # wait until logged in
            await save_session(context)

        # navigate to product table
        await page.goto("https://<iden-challenge-url>/products")  # replace with actual

        products = []
        while True:
            rows = await page.query_selector_all(".product-row")  # adjust selector
            for row in rows:
                data = {
                    "id": await row.query_selector_eval(".id", "el => el.innerText"),
                    "name": await row.query_selector_eval(".name", "el => el.innerText"),
                    "category": await row.query_selector_eval(".category", "el => el.innerText"),
                    "price": await row.query_selector_eval(".price", "el => el.innerText"),
                    "last_updated": await row.query_selector_eval(".updated", "el => el.innerText"),
                    "rating": await row.query_selector_eval(".rating", "el => el.innerText"),
                }
                products.append(data)

            # handle pagination
            next_btn = await page.query_selector("button.next")
            if next_btn and await next_btn.is_enabled():
                await next_btn.click()
                await page.wait_for_timeout(1000)
            else:
                break

        # save JSON
        with open(OUTPUT_FILE, "w") as f:
            json.dump(products, f, indent=2)

        print(f"✅ Exported {len(products)} products to {OUTPUT_FILE}")

asyncio.run(run())
