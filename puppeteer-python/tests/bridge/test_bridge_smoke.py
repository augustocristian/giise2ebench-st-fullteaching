"""Smoke test of the Python-Node Puppeteer bridge.

It never touches the FullTeaching SUT: it drives a ``data:`` URL and a throw-away HTTP(S) server
started on 127.0.0.1 by the tests themselves.
"""
import http.server
import shutil
import ssl
import subprocess
import threading
from urllib.parse import quote

import pytest

from fullteaching_e2e.browser import (
    Browser,
    BridgeProtocolError,
    ElementTimeoutError,
    Page,
    TestId,
)

PAGE_HTML = """<!doctype html><html><head><title>Bridge page</title></head><body>
<div id="box"><ul id="list">
  <li class="item" data-n="1">One</li>
  <li class="item" data-n="2">Two <span hidden>secret</span></li>
  <li class="item" data-n="3">Three</li>
</ul></div>
<button id="btn" data-testid="the-button" onclick="this.dataset.clicks = (+this.dataset.clicks || 0) + 1">Click me</button>
<button id="dbl" ondblclick="this.dataset.done = 'yes'">Double</button>
<input id="name" type="text">
<select id="sel"><option value="a">Alpha</option><option value="b">Beta</option></select>
<input id="file" type="file" style="display:none" onchange="document.title = this.files[0].name">
<button id="ask" onclick="window.answer = confirm('sure?')">Ask</button>
<div id="late"></div>
<script>setTimeout(() => { document.getElementById('late').textContent = 'loaded later'; }, 300);</script>
</body></html>"""
DATA_URL = "data:text/html;charset=utf-8," + quote(PAGE_HTML)

MEDIA_HTML = """<!doctype html><html><body><video id="v" autoplay muted playsinline></video><script>
navigator.mediaDevices.getUserMedia({ video: true, audio: true })
  .then((stream) => { window.tracks = stream.getTracks().length; document.getElementById('v').srcObject = stream; })
  .catch((error) => { window.mediaError = String(error); });
</script></body></html>"""

VIDEO_PLAYING = ("() => { const v = document.getElementById('v'); "
                 "return !!v && !v.paused && v.readyState >= 2 && v.currentTime > 0; }")


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - name fixed by http.server
        routes = {
            "/": (200, "<title>Home</title><a id='next' href='/next'>next</a>"),
            "/next": (200, "<title>Next</title><p id='p'>second page</p>"),
            "/media": (200, MEDIA_HTML),
        }
        status, body = routes.get(self.path, (404, "<title>Not found</title>"))
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def _serve(context: ssl.SSLContext | None = None):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    if context is not None:
        server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="module")
def local_url():
    server = _serve()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
async def demo(page: Page) -> Page:
    await page.goto(DATA_URL)
    return page


async def test_launch_and_evaluate(browser: Browser, demo: Page):
    assert browser.version
    assert await demo.title() == "Bridge page"
    assert await demo.evaluate("(a, b) => a + b", 2, 3) == 5
    assert await demo.evaluate("async (name) => { await Promise.resolve(); return `hi ${name}`; }", "bridge") == "hi bridge"
    assert await demo.evaluate_expression("var answer = 40; answer + 2") == 42


async def test_css_and_xpath_locators(demo: Page):
    items = demo.locator("#list .item")
    assert await items.count() == 3
    assert await items.nth(1).attribute("data-n") == "2"
    assert await items.last().text() == "Three"
    assert await items.all_texts() == ["One", "Two secret", "Three"]
    assert await items.nth(1).inner_text() == "Two"
    assert await demo.locator(TestId.of("the-button")).text() == "Click me"
    assert [await item.text() for item in await items.all()] == ["One", "Two secret", "Three"]

    assert await demo.xpath("//li[@class='item']").count() == 3
    assert await demo.locator("xpath=//li[contains(., 'Three')]").attribute("data-n") == "3"
    assert await demo.xpath("//ul[@id='list']").within_xpath("//li").count() == 3
    assert await demo.locator("#box").within_xpath(".//li[2]").text() == "Two secret"
    assert await demo.locator("#box").within("li").nth(0).text() == "One"
    assert await demo.xpath("//li[@data-n='99']").count() == 0
    assert await demo.xpath("//li[@data-n='99']").nth(0).count() == 0


async def test_click_fill_type_select_and_evaluate(demo: Page, tmp_path):
    button = demo.locator("#btn")
    await button.click()
    await button.js_click()
    assert await button.attribute("data-clicks") == "2"
    await demo.locator("#dbl").double_click()
    assert await demo.locator("#dbl").attribute("data-done") == "yes"

    name = demo.locator("#name")
    await name.fill("someone")
    assert await name.input_value() == "someone"
    await name.fill("")
    assert await name.input_value() == ""
    await name.type("abc", delay_ms=5)
    await name.press("Backspace")
    assert await name.input_value() == "ab"

    select = demo.locator("#sel")
    assert await select.select("b") == ["b"]
    assert await select.input_value() == "b"
    assert await select.select_by_text("Alpha") == "a"
    assert await select.input_value() == "a"
    assert await select.evaluate("(el, suffix) => el.value + suffix", "!") == "a!"

    upload = tmp_path / "upload.txt"
    upload.write_text("content", encoding="utf-8")
    await demo.locator("#file").upload_file(upload)
    assert await demo.title() == "upload.txt"


async def test_waits(demo: Page):
    late = demo.locator("#late")
    await late.wait_for("attached")
    await late.wait_for_text("loaded", exact=False)
    await late.wait_for_text("loaded later", exact=True)
    await demo.wait_for_function("(text) => document.getElementById('late').textContent === text", "loaded later")
    assert await demo.wait_for_function("() => document.title") == "Bridge page"
    await demo.locator("#missing").wait_for("hidden")
    await demo.locator("#missing").wait_for("detached")
    # Whitespace is normalised on both sides, so non-breaking spaces (Quill's output) match plain ones.
    await demo.evaluate(r"() => { document.getElementById('late').textContent = ' New\u00a0Title\n'; }")
    await late.wait_for_text("New Title", exact=True)
    await late.wait_for_text("New   Title")
    await demo.evaluate("() => document.getElementById('late').remove()")
    await late.wait_for("detached")


async def test_dialog_policy(demo: Page):
    await demo.set_dialog_policy("accept")
    await demo.locator("#ask").click()
    assert await demo.evaluate("() => window.answer") is True
    await demo.set_dialog_policy("dismiss")
    await demo.locator("#ask").click()
    assert await demo.evaluate("() => window.answer") is False
    kinds = [entry["kind"] for entry in await demo.diagnostics()]
    assert kinds.count("dialog.confirm") == 2


async def test_navigation_status_and_history(page: Page, local_url: str):
    assert await page.goto(f"{local_url}/") == 200
    assert await page.goto(f"{local_url}/missing") == 404
    assert await page.fetch_status(f"{local_url}/next") == 200
    assert await page.fetch_status(f"{local_url}/missing") == 404
    assert await page.fetch_status("http://127.0.0.1:1/unreachable") == 0
    await page.goto(f"{local_url}/")
    await page.locator("#next").click()
    await page.wait_for_url("/next")
    assert await page.title() == "Next"
    await page.go_back()  # the status is None when Chrome restores the page from its cache
    assert await page.title() == "Home"
    await page.go_forward()
    assert await page.url() == f"{local_url}/next"
    await page.reload()
    assert await page.locator("#p").text() == "second page"


async def test_contexts_are_isolated_and_simultaneous(browser: Browser, local_url: str):
    teacher = await browser.new_page(media_origin=local_url)
    students = [await browser.new_page(media_origin=local_url) for _ in range(2)]
    pages = [teacher, *students]
    try:
        for current in pages:
            await current.goto(f"{local_url}/")
        await teacher.evaluate("() => { document.cookie = 'role=teacher'; }")
        assert any(cookie["name"] == "role" for cookie in await teacher.cookies())
        for student in students:
            assert await student.cookies() == []
        await teacher.clear_cookies()
        assert await teacher.cookies() == []
        for index, current in enumerate(pages):
            await current.evaluate("(n) => { document.title = 'user' + n; }", index)
        assert [await current.title() for current in pages] == ["user0", "user1", "user2"]
        await students[0].bring_to_front()
    finally:
        for current in pages:
            await current.close()


async def test_fake_media_devices_and_video_playing(browser: Browser, local_url: str):
    current = await browser.new_page(media_origin=local_url)
    try:
        await current.goto(f"{local_url}/media")
        await current.wait_for_function("() => window.tracks !== undefined || window.mediaError !== undefined")
        assert await current.evaluate("() => window.mediaError") is None
        assert await current.evaluate("() => window.tracks") == 2
        await current.wait_for_function(VIDEO_PLAYING, timeout_ms=15_000)
    finally:
        await current.close()


async def test_grant_permissions_on_a_context(browser: Browser):
    context = await browser.new_context()
    try:
        await context.grant_permissions("https://example.invalid", ["camera", "microphone"])
        await context.grant_permissions("https://example.invalid")
    finally:
        await context.close()


async def test_self_signed_https_is_accepted(browser: Browser, tmp_path):
    openssl = shutil.which("openssl")
    if openssl is None:
        pytest.skip("openssl is not available to create a self-signed certificate")
    key, cert = tmp_path / "key.pem", tmp_path / "cert.pem"
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
                    "-out", str(cert), "-days", "1", "-subj", "/CN=127.0.0.1",
                    "-addext", "subjectAltName=IP:127.0.0.1"],
                   check=True, capture_output=True)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    server = _serve(tls)
    current = await browser.new_page()
    try:
        assert await current.goto(f"https://127.0.0.1:{server.server_port}/") == 200
        assert await current.title() == "Home"
    finally:
        await current.close()
        server.shutdown()
        server.server_close()


async def test_screenshot_viewport_and_diagnostics(demo: Page, tmp_path):
    await demo.set_viewport(400, 600)
    await demo.locator("#ask").scroll_into_view()
    shot = await demo.screenshot(tmp_path / "shots" / "page.png")
    assert shot.is_file() and shot.stat().st_size > 0
    await demo.evaluate("() => console.error('bridge-diagnostic-probe')")
    assert any("bridge-diagnostic-probe" in entry["text"] for entry in await demo.diagnostics())
    assert await demo.diagnostics() == []


async def test_timeout_and_protocol_error_paths(demo: Page):
    missing = demo.locator("#does-not-exist", timeout_ms=500)
    with pytest.raises(ElementTimeoutError):
        await missing.click()
    with pytest.raises(ElementTimeoutError):
        await missing.wait_for("visible")
    with pytest.raises(ElementTimeoutError):
        await missing.wait_for_text("never")
    with pytest.raises(ElementTimeoutError):
        await demo.wait_for_function("() => false", timeout_ms=500)
    with pytest.raises(ElementTimeoutError):
        await demo.locator("#box").with_timeout(500).wait_for("hidden")
    with pytest.raises(BridgeProtocolError):
        await demo.evaluate("() => { throw new Error('boom'); }")
    with pytest.raises(BridgeProtocolError):
        await demo.locator("###").with_timeout(500).count()
