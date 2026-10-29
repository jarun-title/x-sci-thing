import asyncio, sys
from playwright.async_api import async_playwright
ARGS=["--no-sandbox","--use-gl=angle","--use-angle=swiftshader","--ignore-gpu-blocklist","--in-process-gpu","--single-process","--no-zygote","--headless=shell","--allow-file-access-from-files"]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/tmp/chromium", args=ARGS)
        pg = await b.new_page(viewport={"width":1100,"height":900})
        errs=[]; pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file:///home/claude/test3d/index.html"); await pg.wait_for_timeout(1500)
        for t in [2,6,10,13.5,16,22,26,31]:
            await pg.evaluate(f"window.__seek({t})"); await pg.wait_for_timeout(300)
            await pg.locator("#stage").screenshot(path=f"/home/claude/test3d/t{t}.png")
        print("errors:", errs[:5]); await b.close()
asyncio.run(main())
