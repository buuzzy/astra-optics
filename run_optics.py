"""astra-optics 验收脚本：真浏览器跑渲染，测帧率、抓报错、四个场景连拍"""
import asyncio, json
from playwright.async_api import async_playwright

OUT = "/Users/nakocai/Documents/Projects/astra-review2"
URL = "file:///Users/nakocai/Documents/Projects/astra-review2/index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--use-gl=angle", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        errors, logs = [], []
        page.on("console", lambda m: logs.append(f"{m.type}: {m.text[:120]}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        await page.goto(URL)
        await page.wait_for_timeout(5000)

        state = await page.evaluate("""() => ({
            errorPanel: !document.getElementById('error').hidden,
            errorText: document.getElementById('error').textContent.slice(0,300),
            fps: document.getElementById('fps').textContent,
            scale: document.getElementById('scale').textContent,
            resolution: document.getElementById('resolution').textContent,
            dpr: document.getElementById('dpr').textContent,
            status: document.getElementById('status').textContent,
        })""")
        print("初始状态:", json.dumps(state, ensure_ascii=False))
        await page.screenshot(path=f"{OUT}/t1-开场全景.png")

        # 拖拽环绕
        await page.mouse.move(720, 450)
        await page.mouse.down()
        for i in range(12):
            await page.mouse.move(720 + i * 18, 450 - i * 4, steps=2)
            await page.wait_for_timeout(40)
        await page.mouse.up()
        await page.wait_for_timeout(1200)
        await page.screenshot(path=f"{OUT}/t2-环绕视角.png")

        # 滚轮推近三棱镜
        for _ in range(6):
            await page.mouse.wheel(0, -240)
            await page.wait_for_timeout(120)
        await page.wait_for_timeout(1200)
        state2 = await page.evaluate("""() => ({
            fps: document.getElementById('fps').textContent,
            scale: document.getElementById('scale').textContent,
        })""")
        print("推近后:", json.dumps(state2, ensure_ascii=False))
        await page.screenshot(path=f"{OUT}/t3-推近三棱镜.png")

        # 关光束对比
        await page.click("#beam")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUT}/t4-关光束对比.png")
        await page.click("#beam")

        # 稳定帧率采样（再跑 3 秒取面板值）
        await page.wait_for_timeout(3000)
        state3 = await page.evaluate("""() => ({
            fps: document.getElementById('fps').textContent,
            scale: document.getElementById('scale').textContent,
            resolution: document.getElementById('resolution').textContent,
        })""")
        print("稳定后:", json.dumps(state3, ensure_ascii=False))
        print("JS报错:", errors if errors else "无")
        print("控制台异常:", logs if logs else "无")
        await browser.close()

asyncio.run(main())
