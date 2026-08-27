# Browser workflows

Use these workflows to select and configure LaVague browser drivers without relying on source-checkout examples. Keep full `WebAgent` execution in the core web-agent route; this file focuses on browser setup and browser-specific behavior.

## Workflow 1: choose a driver

1. Identify hard requirements:
   - Need tabs, Browserbase, Selenium `Options`, dropdown selection, hover-before-scroll, or the broadest feature coverage -> choose Selenium.
   - Need a Playwright `Page`/persistent context supplied by surrounding code -> choose Playwright, then verify the exact feature set.
   - Need Gradio demo or notebook execution -> avoid Playwright unless the caller accepts known async compatibility limits.
2. Probe readiness before live execution:

   ```bash
   python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver both
   ```

3. If the probe reports missing browser binaries, resolve that before constructing a driver.
4. Only after imports and browser runtime look available, construct the driver and pass it to `ActionEngine`.

## Workflow 2: Selenium driver for normal agent runs

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

browser = SeleniumDriver(headless=True, width=1080, height=1080)
action_engine = ActionEngine(browser)
agent = WebAgent(WorldModel(), action_engine)

# Browser navigation and model execution are intentional runtime steps:
# agent.get(target_url)
# result = agent.run(objective)
```

Use `headless=True` in CI, containers, VMs, notebooks, and other environments without a GUI. Use `headless=False` only when a human needs to see or manually control the browser and the environment supports windows.

## Workflow 3: Playwright driver when explicitly requested

```python
from lavague.core import ActionEngine
from lavague.drivers.playwright import PlaywrightDriver

browser = PlaywrightDriver(headless=True, width=1080, height=1080)
action_engine = ActionEngine(browser)
```

Before selecting Playwright, check:

- `lavague.drivers.playwright` imports successfully.
- The Python Playwright package imports successfully.
- Chromium browser binaries are installed for Playwright.
- The required behavior does not depend on Selenium-only features such as Browserbase, Selenium options, robust tab switching, or dropdown-specific generated actions.

## Workflow 4: existing session for logins, pop-ups, and CAPTCHAs

Fresh browser sessions can trigger login walls or CAPTCHAs. When the user has already solved login/CAPTCHA state in their normal browser profile, ask for an explicit profile directory and use `user_data_dir`.

Selenium:

```python
from lavague.drivers.selenium import SeleniumDriver

driver = SeleniumDriver(
    headless=False,
    user_data_dir=profile_dir_supplied_by_user,
)
```

Playwright persistent context:

```python
from lavague.drivers.playwright import PlaywrightDriver

driver = PlaywrightDriver(
    headless=False,
    user_data_dir=profile_dir_supplied_by_user,
)
```

Operational cautions:

- Do not guess or hard-code profile paths. Ask the caller.
- A profile can be locked by an already-running browser. Use a copy or close the other browser instance if construction fails with a profile-lock symptom.
- Persistent browser state can contain sensitive cookies. Avoid logging the path or copying profile contents.
- For manual CAPTCHA/pop-up handling, run headed, navigate to the relevant page, pause for manual resolution, then resume the agent objective.

## Workflow 5: attach Selenium to an existing debug Chrome

When a user starts Chrome separately with a remote debugging port, pass Selenium Chrome options into `SeleniumDriver`:

```python
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = SeleniumDriver(headless=False, options=chrome_options)
```

The user, not the reusable skill, must launch the browser with remote debugging enabled. This is an interactive recovery pattern for session reuse and bot-protection troubleshooting.

## Workflow 6: custom Selenium driver injection

Use injection when a surrounding application already manages WebDriver lifecycle, special Chrome capabilities, proxies, download directories, or browser services.

Factory injection:

```python
from lavague.drivers.selenium import SeleniumDriver


def build_driver():
    # Return a configured selenium.webdriver.remote.webdriver.WebDriver.
    # Keep credentials and local paths outside reusable code.
    ...

browser = SeleniumDriver(get_selenium_driver=build_driver)
```

Existing object injection:

```python
browser = SeleniumDriver(driver=already_created_webdriver)
```

Remember that `SeleniumDriver.destroy()` calls `quit()` on its underlying WebDriver. Do not hand it a shared driver unless that lifecycle is acceptable.

## Workflow 7: custom Playwright page injection

Use `get_sync_playwright_page` when surrounding code already created a synchronous Playwright page:

```python
from lavague.drivers.playwright import PlaywrightDriver


def get_page():
    # Return a playwright.sync_api.Page created by the caller.
    ...

browser = PlaywrightDriver(get_sync_playwright_page=get_page)
```

The LaVague Playwright driver uses the sync Playwright API. Do not mix this with async-only control flow without an explicit compatibility plan.

## Workflow 8: iframe-heavy tasks

LaVague driver docs mark iframes as supported by both Selenium and Playwright, and the Selenium source includes iframe-aware XPath resolution:

- `SeleniumDriver.resolve_xpath(xpath)` partitions nested xpath strings around iframe segments and switches frames as needed.
- It resets to the default frame when the context manager exits.
- Selenium default Chrome options disable some web-security/site-isolation restrictions to improve frame access.

For future agents:

1. Prefer Selenium for complex nested iframes unless the task explicitly requires Playwright.
2. Keep navigation instructions precise: tell the action engine which iframe-contained field or button is visible.
3. If an iframe step fails, verify the page actually exposed the expected frame and that the target element is not inside a cross-origin frame the browser refuses to control.
4. Model-provider choices for iframe examples belong to the contexts route, not this browser route.

## Workflow 9: tabs, scan, and scroll controls

LaVague `NavigationControl` sends browser-level commands through the driver:

| Control instruction | Driver behavior |
| --- | --- |
| `SCAN` | Calls `get_screenshots_whole_page()`, captures screenshots, scrolls down until bottom or max screenshot count. |
| `SCROLL_DOWN` / `SCROLL_UP` | Calls driver page scroll helpers. |
| `SWITCH_TAB n` | Calls `driver.switch_tab(tab_id=n)`. Selenium implements real tab switching; Playwright should not be assumed to. |
| `BACK` | Uses browser history. |
| `MAXIMIZE_WINDOW` | Selenium maximizes the window; inspected Playwright implementation is a no-op. |
| `WAIT` | Sleeps for the configured navigation-control interval and waits for idle. |

For scrollable components, instruct the navigation engine to hover over the component first, then use scroll or scan. Selenium remembers the hover anchor and can scroll that container; page-level scan alone may miss content inside a nested scroll pane.

## Workflow 10: Selenium remote connection through Browserbase

Selenium has a `BrowserbaseRemoteConnection` helper for remote WebDriver sessions:

```python
from lavague.drivers.selenium import BrowserbaseRemoteConnection, SeleniumDriver

connection = BrowserbaseRemoteConnection(
    "http://connect.browserbase.com/webdriver",
    api_key=browserbase_api_key_supplied_at_runtime,
    project_id=browserbase_project_id_supplied_at_runtime,
)

with SeleniumDriver(remote_connection=connection) as driver:
    ...
```

If constructor arguments are omitted, the helper reads `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID` from the environment. Do not place credential values in generated files or logs. Browserbase is remote and network-dependent; it is not part of the default safe probe and is not supported by the Playwright driver.

## Escalation from probe to live run

Use this order:

1. `lavague_driver_probe.py --driver both` for import and local binary hints.
2. `lavague_driver_probe.py --driver selenium --construct --headless` for an explicit blank-page Selenium launch check.
3. Add `--url` only when the caller wants a live navigation construction check.
4. Create `ActionEngine`/`WebAgent` only after browser construction works.
5. Add provider model credentials and public-network objectives only in the core/context workflows, not as a browser-readiness check.
