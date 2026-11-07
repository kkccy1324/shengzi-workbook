"""End-to-end check of the built site and the single-file offline version.

Run from the repo root after tools/build.py:  python3 tools/check.py
Needs: playwright (Python) and a Chrome/Chromium; set CHROME=/path/to/chrome if not at /usr/bin/google-chrome.
"""
import asyncio, functools, http.server, os, sys, tempfile, threading, zipfile

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
PORT = 8790


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=DOCS)
    srv = http.server.ThreadingHTTPServer(('localhost', PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def check_page(pg, errs, label):
    await pg.wait_for_function("typeof dictState !== 'undefined' && dictState !== 'loading'", timeout=30000)
    await pg.locator('#chars').fill('我們 上學 風雨 樂')
    await pg.wait_for_timeout(1500)
    state = await pg.evaluate('dictState')
    status = (await pg.locator('#status').inner_text()).replace('\n', ' | ')
    chips = await pg.locator('.zc').count()
    async with pg.expect_download(timeout=30000) as dl:
        await pg.locator('#pdf').click()
    size = os.path.getsize(await (await dl.value).path())
    ok = state == 'ready' and chips == 7 and size > 10000 and not errs
    print(f'[{"OK" if ok else "FAIL"}] {label}: dict={state} chars={chips} pdf={size}B status={status} errors={errs}')
    return ok


async def main():
    srv = serve()
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME)

        ctx = await browser.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://localhost:{PORT}/')
        await pg.wait_for_function("document.getElementById('offline-msg').textContent.startsWith('已可離線')", timeout=60000)
        results.append(await check_page(pg, errs, 'site online'))
        await ctx.set_offline(True)
        await pg.reload()
        results.append(await check_page(pg, errs, 'site offline (service worker)'))
        await ctx.close()

        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(os.path.join(DOCS, 'shengzi-offline.zip')) as z:
                name = z.namelist()[0]
                z.extractall(tmp)
            ctx = await browser.new_context(accept_downloads=True, offline=True)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://' + os.path.join(tmp, name))
            results.append(await check_page(pg, errs, 'single-file offline'))
            await ctx.close()
        await browser.close()
    srv.shutdown()
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    asyncio.run(main())
