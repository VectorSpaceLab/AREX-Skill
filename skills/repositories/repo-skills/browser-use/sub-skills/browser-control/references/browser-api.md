# Browser API Reference

This reference covers the browser-control surface only. Combine it with `../../agent-programming/SKILL.md` when the user is building a full `Agent` workflow.

## Public Imports

```python
from browser_use import Browser, BrowserProfile
from browser_use.browser import BrowserSession, ProxySettings
```

`Browser` is the same class as `BrowserSession` and is the clearer import for most user code. `BrowserProfile` is a reusable static configuration object that can be passed to `BrowserSession(browser_profile=...)` or expressed directly as keyword arguments on `Browser(...)`.

## Browser / BrowserSession Construction

Common local fields:

```python
browser = Browser(
    headless=True,
    user_data_dir=None,
    window_size={"width": 1280, "height": 720},
    downloads_path="./downloads",
    allowed_domains=["example.com"],
)
```

Important constructor families:

- Local launch: `headless`, `executable_path`, `channel`, `args`, `ignore_default_args`, `chromium_sandbox`, `devtools`, `env`, `user_data_dir`, `profile_directory`.
- Remote/CDP: `cdp_url`, `is_local`, `headers`.
- Cloud browser: `use_cloud`, `cloud_profile_id`, `cloud_proxy_country_code`, `cloud_timeout`.
- Browser data: `storage_state`, `accept_downloads`, `downloads_path`, `auto_download_pdfs`, `permissions`.
- View/display: `window_size`, `window_position`, `viewport`, `screen`, `no_viewport`, `device_scale_factor`, `headless`.
- Recording/debugging: `record_video_dir`, `record_video_size`, `record_video_framerate`, `record_har_path`, `record_har_content`, `record_har_mode`, `traces_dir`.
- Security/network: `allowed_domains`, `prohibited_domains`, `proxy`, `disable_security`, `deterministic_rendering`, `enable_default_extensions`, `captcha_solver`, `cookie_whitelist_domains`.
- DOM/timing: `cross_origin_iframes`, `max_iframes`, `max_iframe_depth`, `highlight_elements`, `dom_highlight_elements`, `paint_order_filtering`, `minimum_wait_page_load_time`, `wait_for_network_idle_page_load_time`, `wait_between_actions`.

## BrowserProfile

Use `BrowserProfile` when several sessions should share a template or when you want a named profile object:

```python
profile = BrowserProfile(
    headless=False,
    user_data_dir="./browser-profile",
    allowed_domains=["*.example.com"],
    record_video_dir="./recordings",
)

browser = Browser(browser_profile=profile)
```

Notes:

- Pydantic validates and normalizes settings. Unknown fields may be ignored by `BrowserProfile` but are forbidden by `BrowserSession`; put options on the right object and check typos.
- `window_width` and `window_height` are deprecated; use `window_size={"width": ..., "height": ...}`.
- Passing both `storage_state` and a non-temporary `user_data_dir` can overwrite cookies/localStorage/sessionStorage in that profile. Prefer one or use separate profiles for parallel sessions.
- Large domain lists with at least 100 items are optimized to sets for exact matching; pattern matching is not supported for those optimized sets.
- `deterministic_rendering=True` is not recommended because it can break sites and increase bot-detection risk.

## ProxySettings

```python
from browser_use.browser import ProxySettings

browser = Browser(
    proxy=ProxySettings(
        server="http://proxy.example:8080",
        bypass="localhost,127.0.0.1,*.internal",
        username="user",
        password="pass",
    )
)
```

If `bypass` is provided without `server`, Browser Use warns that bypass is ignored.

## Lifecycle Methods

```python
await browser.start()   # initialize/connect and attach watchdogs
await browser.stop()    # stop session bookkeeping; may keep browser alive depending config
await browser.close()   # close session alias path
await browser.kill()    # kill browser process and reset state
await browser.reset()   # reset internal session state
```

Use `kill()` in examples that open disposable local browsers. Use `stop()` when the intent is to detach without force-killing an external or kept-alive browser.

## Tabs and Pages

```python
page = await browser.new_page("https://example.com")
pages = await browser.get_pages()
current = await browser.get_current_page()
current = await browser.must_get_current_page()
await browser.close_page(page)
```

Session helpers:

- `await browser.get_tabs()` returns `TabInfo` objects.
- `await browser.navigate_to(url, new_tab=False)` navigates through the session event path.
- `await browser.get_current_page_url()` and `await browser.get_current_page_title()` read focused page metadata.
- `browser.get_page_targets()` and `browser.get_focused_target()` expose CDP target metadata.

## Cookies and Storage State

```python
await browser.start()
cookies = await browser.cookies()
await browser.export_storage_state("storage_state.json")
await browser.clear_cookies()
```

Use `storage_state="storage_state.json"` or a storage-state dict to reuse saved cookies/localStorage without copying a real Chrome profile. Avoid committing storage-state files containing private sessions.

## CDP Helpers

```python
session = await browser.get_or_create_cdp_session()
await browser.set_extra_headers({"X-Trace-Id": "demo"})
```

Useful direct methods include:

- `browser.cdp_client` for the root CDP client after connection.
- `await browser.cdp_client_for_target(target_id)` / `cdp_client_for_frame(frame_id)` / `cdp_client_for_node(node)` for target-specific sessions.
- `await browser.reconnect()` when the websocket drops and the session is recoverable.
- Private `_cdp_*` helpers exist for internal use; prefer public methods unless you are writing Browser Use internals.

## Actor Page API

Actor APIs provide direct CDP-backed control, not Playwright/Selenium compatibility.

```python
page = await browser.new_page("https://example.com")
await page.goto("https://example.com/login")
await page.press("Escape")
title = await page.get_title()
url = await page.get_url()
result = await page.evaluate('() => document.title')
shot_b64 = await page.screenshot(format="png")
```

Common `Page` methods:

- Navigation: `goto`, `go_back`, `go_forward`, `reload`.
- Selectors: `get_elements_by_css_selector(selector)`, `get_element(backend_node_id)`.
- AI-assisted element lookup: `get_element_by_prompt(prompt, llm)`, `must_get_element_by_prompt(prompt, llm)`.
- JavaScript: `evaluate(page_function, *args)`; use arrow-function strings such as `'() => document.title'` or `'(x, y) => x + y'`.
- Keyboard/display: `press(key)`, `set_viewport_size(width, height)`, `screenshot(format="png", quality=None)`.
- Extraction: `extract_content(prompt, structured_output, llm)` for direct page extraction; route model/schema design to `../../llm-and-output/SKILL.md`.

## Actor Element API

```python
elements = await page.get_elements_by_css_selector("input[name='email']")
email = elements[0]
await email.fill("user@example.com")
await email.focus()
value = await email.get_attribute("value")
box = await email.get_bounding_box()
```

Common `Element` methods:

- Interaction: `click(button="left", click_count=1, modifiers=None)`, `fill(text, clear=True)`, `hover`, `focus`, `check`, `select_option(values)`, `drag_to(target)`.
- Inspection: `get_attribute(name)`, `get_bounding_box()`, `get_basic_info()`, `screenshot(format="png")`.
- JavaScript: `evaluate(page_function, *args)` with `this` bound to the element.

Do not invent Playwright-only methods such as `element.submit()`, `element.dispatch_event()`, or `element.get_property()`.

## Mouse API

```python
mouse = await page.mouse
await mouse.move(100, 200)
await mouse.click(100, 200)
await mouse.scroll(x=0, y=100, delta_y=-500)
```

Use coordinate APIs for canvas, drag surfaces, and fallback interactions after DOM element clicks fail.

## DOM and State Methods

`BrowserSession` exposes DOM and selector-map helpers used by tools and agents:

```python
state = await browser.get_browser_state_summary()
text = await browser.get_state_as_text()
selector_map = await browser.get_selector_map()
node = await browser.get_dom_element_by_index(3)
```

Useful methods:

- `get_browser_state_summary(cache_clickable_elements_hashes=True, include_screenshot=True)` summarizes tabs, URL/title, DOM, selector map, and screenshot information.
- `get_state_as_text()` returns a text representation suitable for debugging.
- `get_dom_element_by_index(index)` and `get_element_by_index(index)` resolve numbered interactive DOM elements.
- `get_dom_element_at_coordinates(x, y)` can diagnose coordinate clicks.
- `remove_highlights()`, `add_highlights(selector_map)`, `highlight_interaction_element(node)`, and `highlight_coordinate_click(x, y)` support visual debugging.
- `take_screenshot(full_page=False, clip=None)` and `screenshot_element(selector)` return base64 screenshots.

## Downloaded Files

```python
browser = Browser(downloads_path="./downloads", accept_downloads=True)
# after browsing
files = browser.downloaded_files()
```

Downloads are mediated by a downloads watchdog. Still choose a dedicated `downloads_path` and treat downloaded content as untrusted.
