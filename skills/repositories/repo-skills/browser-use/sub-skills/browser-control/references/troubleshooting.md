# Browser Control Troubleshooting

Use these checks when browser/session/profile/CDP/DOM features fail. Route non-browser issues to sibling sub-skills named in each section.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'browser_use'`
- `ImportError` for browser, actor, DOM, or screenshot modules
- Chromium executable not found after package install

Checks:

```bash
uv pip show browser-use
python - <<'PY'
from browser_use import Browser, BrowserProfile
from browser_use.browser import BrowserSession, ProxySettings
print(Browser, BrowserSession, BrowserProfile, ProxySettings)
PY
uvx browser-use install
```

Guidance:

- Use `uv` for environment commands in this repository.
- Installing the Python package is not always enough; run the Browser Use browser installation command when Chromium is missing.
- If the problem is provider credentials or model initialization, route to `../../llm-and-output/SKILL.md`.

## Browser Does Not Start

Symptoms:

- Browser process exits immediately.
- `Target page, context or browser has been closed`.
- No display/headful failures in CI or containers.

Fixes:

- Set `headless=True` in CI or environments without a display.
- Use `Browser(use_cloud=True)` when local Chromium cannot run or production performance matters.
- Avoid `ignore_default_args=True`; remove only specific conflicting flags.
- In Docker-like environments, keep Browser Use defaults unless you know the sandbox/GPU constraints.
- If `devtools=True`, also use `headless=False`.

Minimal diagnostic:

```python
import asyncio
from browser_use import Browser

async def main():
    browser = Browser(headless=True, user_data_dir=None)
    await browser.start()
    print(await browser.get_tabs())
    await browser.kill()

asyncio.run(main())
```

## Real Chrome Profile Is Locked

Symptom:

- Runtime error says Chrome profile files are locked or being used by another process.

Fixes:

- Close all Chrome windows using that profile, then retry `Browser.from_system_chrome(profile_directory="Default")`.
- Or keep Chrome open and connect over CDP instead:

```bash
chrome --remote-debugging-port=9222 --user-data-dir=/tmp/browser-use-cdp-profile
curl -fsS http://localhost:9222/json/version
```

```python
from browser_use import Browser
browser = Browser(cdp_url="http://localhost:9222", is_local=True)
```

## CDP Connection Fails

Symptoms:

- Connection refused to `localhost:9222`.
- Browser starts but Browser Use cannot attach.
- Existing Chrome ignores the debugging port.

Checks:

```bash
curl -fsS http://localhost:9222/json/version
curl -fsS http://localhost:9222/json/list
```

Fixes:

- Launch Chrome with `--remote-debugging-port=9222` before running Python.
- Use a fresh `--user-data-dir` for the CDP Chrome process to avoid conflicts with a normal profile.
- Use the right host/port in `cdp_url` and include `http://`.
- Set `is_local=True` for local CDP connections.
- If Playwright also connects, ensure both libraries point at the same CDP URL.

## Cloud Browser or API Key Fails

Symptoms:

- Cloud browser authorization error.
- Browser creation times out.
- Proxy country not applied.

Checks:

```bash
python - <<'PY'
import os
print('BROWSER_USE_API_KEY set:', bool(os.getenv('BROWSER_USE_API_KEY')))
PY
```

Fixes:

- Set `BROWSER_USE_API_KEY` in the environment; do not hard-code it.
- Use `Browser(use_cloud=True)` for the simplest cloud session.
- Use supported `cloud_proxy_country_code` values such as `us`, `uk`, `fr`, `it`, `jp`, `au`, `de`, `fi`, `ca`, or `in`.
- Route sandbox deployment, profile sync, and production architecture to `../../production-integrations/SKILL.md`.

## Constructor Validation Errors

Symptoms:

- Pydantic `ValidationError`.
- `extra_forbidden` on a `BrowserSession` field.
- Deprecated window width/height warnings.

Fixes:

- Put browser settings on `Browser(...)`, `BrowserSession(...)`, or `BrowserProfile(...)`; put Agent settings on `Agent(...)`.
- Use `window_size={"width": 1280, "height": 720}` instead of `window_width` / `window_height`.
- Use `proxy=ProxySettings(...)`, not ad-hoc proxy dictionaries unless the API explicitly accepts a dict.
- For unknown BrowserProfile fields, verify whether they are deprecated aliases or unsupported.

## Navigation Blocked by Security Policy

Symptoms:

- `Navigation to ... blocked by security policy`.
- Browser redirects to `about:blank` after a click.
- New tab closes immediately.

Fixes:

- Check both requested URL and final redirect target.
- Add exact domains or scheme-specific URL patterns to `allowed_domains`.
- Remember `example.com` allows only root plus `www`; use `*.example.com` for subdomains.
- Keep pattern lists below 100 items; large lists become exact-match sets.
- If `block_ip_addresses=True`, direct IP URLs and encoded IP forms are blocked.

## Downloads Missing or Unsafe Path Concerns

Symptoms:

- Downloaded file not found.
- Download filename changed to a basename or `download`.
- File appears with `(1)` suffix.

Fixes:

- Set `downloads_path` to a dedicated writable directory and `accept_downloads=True`.
- Expect Browser Use to sanitize traversal/absolute filenames and keep writes inside `downloads_path`.
- Use `browser.downloaded_files()` after the task to inspect recorded files.
- Do not place downloads in project root or other sensitive directories.

## Screenshots, Video, HAR, or Traces Missing

Checks:

- The browser/session was actually started.
- Output directories are writable.
- The browser was stopped or killed cleanly so recording/HAR watchdogs can flush.
- For screenshots, use `await browser.take_screenshot()` or `await page.screenshot()` after navigation completes.

Example:

```python
browser = Browser(record_video_dir="./recordings", record_har_path="./network.har")
await browser.start()
page = await browser.new_page("https://example.com")
print(await page.screenshot())
await browser.kill()
```

## DOM or Click Index Looks Wrong

Symptoms:

- Agent clicks the wrong element.
- Element index is missing.
- Cross-origin iframe content is unavailable.

Fixes:

- Inspect `await browser.get_state_as_text()` and `await browser.get_selector_map()`.
- Toggle `paint_order_filtering=False` to diagnose hidden/covered element filtering.
- Keep `cross_origin_iframes=True` for iframe-heavy pages; lower `max_iframes` or disable it for unstable pages.
- Use Actor selector methods (`page.get_elements_by_css_selector`) or coordinate mouse methods for deterministic fallback.
- Route custom fallback tools to `../../tools-and-actions/SKILL.md`.

## Proxy Problems

Symptoms:

- Browser launches but traffic does not use proxy.
- Proxy auth prompts loop.
- Bypass rules ignored.

Fixes:

- Use a full proxy URL: `http://host:port` or `socks5://host:port`.
- Include `username` and `password` in `ProxySettings` for authenticated proxies.
- Provide `server` when using `bypass`; bypass without server is ignored.
- For Browser Use Cloud, prefer `cloud_proxy_country_code` over local proxy settings.

## Async Misuse

Symptoms:

- `RuntimeWarning: coroutine was never awaited`.
- `asyncio.run() cannot be called from a running event loop`.

Fixes:

- `await` Browser Use async methods inside an async function.
- In notebooks or existing async apps, call `await main()` instead of `asyncio.run(main())`.
- Keep direct browser-control examples async even when no Agent is used.
