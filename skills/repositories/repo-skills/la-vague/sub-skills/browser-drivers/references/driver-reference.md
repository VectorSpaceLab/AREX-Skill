# Driver reference

This reference summarizes the LaVague browser drivers as an operating surface for future agents. It is self-contained; use installed package imports and the bundled probe instead of reopening source examples.

## Packages and imports

| Driver | Install/import path | Notes |
| --- | --- | --- |
| Selenium | `from lavague.drivers.selenium import SeleniumDriver` | Installed with the LaVague bundle in the inspected package set; preferred default and broadest support. |
| Browserbase remote connection | `from lavague.drivers.selenium import BrowserbaseRemoteConnection` | Selenium-only remote WebDriver helper. Requires Browserbase credentials supplied at runtime. |
| Playwright | `from lavague.drivers.playwright import PlaywrightDriver` | Optional driver package. Also needs Playwright browser binaries, usually Chromium, installed separately. |

Observed package versions during generation included `lavague` 1.1.19, `lavague-drivers-selenium` 0.2.15, and `lavague-drivers-playwright` 0.2.11.

## Constructor signatures

### `SeleniumDriver`

```python
SeleniumDriver(
    url=None,
    get_selenium_driver=None,
    headless=True,
    user_data_dir=None,
    width=1080,
    height=1080,
    options=None,
    driver=None,
    log_waiting_time=False,
    waiting_completion_timeout=10,
    remote_connection=None,
)
```

Important semantics:

- Construction launches or accepts an underlying Selenium `WebDriver` immediately.
- `url` navigates during construction when supplied.
- `headless=True` is the safe default for non-GUI environments.
- `user_data_dir` points Chrome at a persistent profile directory; use only a path supplied by the caller.
- `options` accepts a Selenium Chrome `Options` object. If supplied, LaVague reuses it and then adds its own required flags/capabilities.
- `get_selenium_driver` can replace the default init function. `driver` can inject an already-created Selenium `WebDriver` object.
- `remote_connection` is for Selenium remote operation, including Browserbase.

Default Selenium init behavior adds a Chrome user agent, `--no-sandbox`, disabled web security/site isolation/notifications, performance logging, optional `--headless=new`, optional `--user-data-dir`, and a LaVague event setup script.

### `PlaywrightDriver`

```python
PlaywrightDriver(
    url=None,
    get_sync_playwright_page=None,
    headless=True,
    width=1080,
    height=1080,
    user_data_dir=None,
    log_waiting_time=False,
    waiting_completion_timeout=10,
)
```

Important semantics:

- Construction enters Playwright sync mode and creates a page immediately unless `get_sync_playwright_page` supplies one.
- `url` navigates during construction when supplied.
- `user_data_dir=None` launches a normal Chromium browser/context. A provided `user_data_dir` uses a persistent context.
- Playwright import errors instruct the user to install the Playwright package and Chromium browser binaries. The browser binary install is a separate step from Python package installation.
- The driver exposes `headless`, but the LaVague driver support matrix marks Playwright headless-agent behavior as incomplete; verify locally before depending on it.

## Feature support boundaries

| Capability | Selenium | Playwright | Operating note |
| --- | --- | --- | --- |
| Default LaVague driver path | Yes | Optional | Selenium is the documented preference. |
| Browser launch in constructor | Yes | Yes | Do not instantiate just to inspect readiness unless launch is intended. |
| Headless mode constructor option | Yes | Yes | Selenium headless is the stable default; Playwright headless-agent support should be verified. |
| Headed/manual session | Yes | Yes | Requires a GUI-capable environment. |
| Existing profile via `user_data_dir` | Yes | Yes | Useful for cookies/logins/CAPTCHAs; profile locking can fail if already open. |
| Iframe handling | Yes | Documented yes | Selenium source includes frame switching through iframe xpaths. Verify complex Playwright iframe cases. |
| Multiple tab reporting/switching | Yes | Not feature-parity | Selenium implements `get_tabs()` and `switch_tab()`; Playwright uses base stubs in the inspected driver. |
| Highlight elements | Yes | Yes | Both expose highlighted element helpers; Selenium also has node highlight utilities. |
| Dropdown select | Yes | Not in Playwright action schema | Selenium has `dropdownSelect`; Playwright action schema lacks dropdown-specific support. |
| Hover before scrolling | Yes | Not in Playwright action schema | Selenium action schema includes `hover`; Playwright action schema does not. |
| Page/component scrolling | Yes | Basic page scroll | Selenium can scroll a hovered/container anchor; Playwright exposes page scroll up/down controls. |
| Remote Browserbase | Yes | No | Browserbase helper is Selenium-only. |
| Notebook/Gradio `agent.demo()` compatibility | Yes/normal caveats | Limited | Playwright sync/async compatibility is called out as incompatible with notebooks and Gradio demo mode. |

Do not overclaim Playwright parity. If a task depends on tabs, Selenium options, Browserbase, dropdowns, or element-container scrolling, choose Selenium unless the caller accepts a local Playwright verification cycle.

## Public driver methods that matter operationally

Both drivers provide the `BaseDriver` shape expected by `ActionEngine`:

- `get(url)` / `code_for_get(url)` for navigation.
- `back()` / `code_for_back()` for browser history.
- `get_url()` for current URL, returning `None` on blank initial pages.
- `get_html()` for page content.
- `get_screenshot_as_png()` for screenshot capture.
- `resize_driver(width, height)` and `code_for_resize(width, height)` for viewport/window sizing.
- `execute_script(...)` / `code_for_execute_script(...)` for JavaScript execution.
- `get_possible_interactions(...)` to enumerate interactable XPath candidates.
- `exec_code(...)` to execute the action code generated by the navigation engine.
- `destroy()` to close the underlying browser/page.

Selenium-specific operational methods and actions:

- `switch_frame(xpath)`, `switch_default_frame()`, `switch_parent_frame()`, and iframe-aware `resolve_xpath(xpath)`.
- `get_tabs()` and `switch_tab(tab_id)` for tab visibility and selection.
- `click`, `setValue`, `setValueAndEnter`, `dropdownSelect`, `hover`, and `scroll` action schema.
- `upload_file` support when `set_value` targets a file input.
- Scroll anchor behavior: after `hover` or a targeted scroll, Selenium remembers `last_hover_xpath`, so a later scroll can target the intended scrollable container.

Playwright-specific operational methods and actions:

- `get_driver()` returns a Playwright `Page` object.
- `resize_driver` sets viewport size with `page.set_viewport_size`.
- `exec_code` accepts JSON actions for `click`, `setValue`, `setValueAndEnter`, `wait`, `failNoElement`, and `failAmbiguous`.
- `maximize_window()` is a no-op in the inspected driver.
- `scroll_up()` and `scroll_down()` scroll the page by one viewport height.

## Import and binary probe

Run the bundled safe probe from the repository or installed skill tree:

```bash
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver both
```

Useful variations:

```bash
# Only import/signature checks; no browser launch.
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver selenium --check-imports

# Binary hints for Chrome/Chromedriver and Playwright's browser cache; no downloads.
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver both --check-browser-binaries

# Explicit browser construction check. This may launch a local browser.
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver selenium --construct --headless
```

Default probe behavior is import plus browser-binary reporting only. It should report missing optional packages or browser binaries clearly rather than silently launching a browser.
