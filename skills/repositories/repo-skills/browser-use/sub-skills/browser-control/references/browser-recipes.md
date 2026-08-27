# Browser Recipes

These recipes are self-contained patterns adapted from Browser Use browser examples and tests. They avoid local checkout paths and never include credentials.

## Local Headful Browser with an Agent

```python
import asyncio
from browser_use import Agent, Browser, ChatBrowserUse

async def main():
    browser = Browser(
        headless=False,
        window_size={"width": 1200, "height": 800},
        downloads_path="./downloads",
    )
    agent = Agent(
        task="Open https://example.com and summarize the visible page.",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    history = await agent.run()
    print(history.final_result())
    await browser.kill()

asyncio.run(main())
```

Route changes to `task`, `max_steps`, callbacks, history, and prompt design to `../../agent-programming/SKILL.md`.

## Direct Browser Control Without an Agent

```python
import asyncio
from browser_use import Browser

async def main():
    browser = Browser(headless=True, user_data_dir=None)
    await browser.start()
    page = await browser.new_page("https://example.com")
    print(await page.get_title())
    print(await page.evaluate('() => document.body.innerText.slice(0, 120)'))
    await browser.kill()

asyncio.run(main())
```

Use this for deterministic smoke checks before adding an LLM agent.

## Use Real Chrome Profile

```python
import asyncio
from browser_use import Agent, Browser, ChatBrowserUse

async def main():
    profiles = Browser.list_chrome_profiles()
    print([p["name"] for p in profiles])
    browser = Browser.from_system_chrome(profile_directory="Default")
    agent = Agent(
        task="Open a site where I am already logged in and report the account label.",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()
    await browser.kill()

asyncio.run(main())
```

Operational notes:

- Close normal Chrome windows before copying a real profile.
- If the profile is locked, use CDP to connect to the already-running Chrome instead of copying it.
- Do not hard-code machine-specific Chrome paths in public skill content; ask the user for their path when needed.

## Connect to Existing Chrome with CDP

Start Chrome with remote debugging enabled, then connect Browser Use to it.

```bash
chrome --remote-debugging-port=9222 --user-data-dir=/tmp/browser-use-cdp-profile
curl -fsS http://localhost:9222/json/version
```

```python
import asyncio
from browser_use import Agent, ChatBrowserUse
from browser_use.browser import BrowserProfile, BrowserSession

async def main():
    browser = BrowserSession(
        browser_profile=BrowserProfile(cdp_url="http://localhost:9222", is_local=True)
    )
    agent = Agent(
        task="Open DuckDuckGo and search for browser automation.",
        llm=ChatBrowserUse(),
        browser_session=browser,
    )
    await agent.run()
    await browser.kill()

asyncio.run(main())
```

Validation checks:

- `curl http://localhost:9222/json/version` returns JSON before the Python code runs.
- Use a unique `--user-data-dir` if starting a new Chrome process.
- Use `is_local=True` for local CDP sessions so Browser Use treats the browser as local.

## Cloud Browser Session

```python
import asyncio
from browser_use import Agent, Browser, ChatBrowserUse

async def main():
    browser = Browser(
        use_cloud=True,
        cloud_proxy_country_code="us",
        cloud_timeout=30,
    )
    agent = Agent(
        task="Open example.com and summarize the page.",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()

asyncio.run(main())
```

Requirements and routing:

- Requires `BROWSER_USE_API_KEY` in the environment.
- Use this when users ask for better production browser performance, captchas/bot-detection resilience, remote streaming, or profile sync.
- Route production deployment, `@sandbox`, and profile sync to `../../production-integrations/SKILL.md`.

## Proxy Configuration

```python
from browser_use import Browser
from browser_use.browser import ProxySettings

browser = Browser(
    proxy=ProxySettings(
        server="http://proxy.example:8080",
        bypass="localhost,127.0.0.1",
        username="proxy-user",
        password="proxy-pass",
    )
)
```

For Browser Use Cloud geo-routing, use `cloud_proxy_country_code` instead of a local proxy object.

## Export and Reuse Storage State

```python
import asyncio
from browser_use import Browser

async def export_state():
    browser = Browser.from_system_chrome(profile_directory="Default")
    await browser.start()
    await browser.export_storage_state("storage_state.json")
    await browser.stop()

async def reuse_state():
    browser = Browser(storage_state="storage_state.json", user_data_dir=None)
    await browser.start()
    print(await browser.get_current_page_url())
    await browser.kill()

asyncio.run(export_state())
```

Treat `storage_state.json` as sensitive because it can contain authenticated cookies and local storage.

## Parallel Browsers

```python
import asyncio
from browser_use import Agent, Browser, ChatBrowserUse

async def run_one(index: int, task: str):
    browser = Browser(user_data_dir=f"./tmp-browser-profile-{index}", headless=True)
    agent = Agent(task=task, llm=ChatBrowserUse(), browser=browser)
    try:
        return await agent.run()
    finally:
        await browser.kill()

async def main():
    await asyncio.gather(
        run_one(1, "Open example.com"),
        run_one(2, "Open example.org"),
    )

asyncio.run(main())
```

Use separate `Browser` instances and separate `user_data_dir` values. Parallel agents sharing one browser can conflict unless the user intentionally coordinates tabs.

## Downloads, Video, HAR, and Traces

```python
browser = Browser(
    downloads_path="./downloads",
    accept_downloads=True,
    auto_download_pdfs=True,
    record_video_dir="./recordings",
    record_video_size={"width": 1280, "height": 720},
    record_har_path="./network.har",
    record_har_content="embed",
    record_har_mode="full",
    traces_dir="./traces",
)
```

Checks:

- Create or choose directories the process can write.
- Keep recordings and HAR files out of version control when they may contain private pages, headers, or cookies.
- If no video/HAR appears, verify the browser actually started and was stopped cleanly so watchdogs can flush outputs.

## Custom Headers Through BrowserSession

For simple one-time headers after session startup:

```python
await browser.start()
await browser.set_extra_headers({"X-Trace-Id": "debug-run"})
```

For every new tab/focus change, create a custom watchdog using Browser Use events. Keep custom action registration and `ActionResult` patterns in `../../tools-and-actions/SKILL.md`.

## Browser Use plus Playwright

When a user needs Playwright selectors together with Browser Use:

1. Start or connect to one Chrome instance through CDP.
2. Connect Playwright to the same `cdp_url`.
3. Register Browser Use custom tools that call Playwright functions and accept `browser_session: BrowserSession` when they need session context.

Route the custom tool implementation details to `../../tools-and-actions/SKILL.md`; this sub-skill owns only the shared CDP/browser setup.
