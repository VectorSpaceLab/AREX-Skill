# Browser driver troubleshooting

Use this guide when LaVague browser driver import, construction, navigation controls, or browser session reuse fails. Start with the safe probe and only escalate to browser launch with explicit user intent.

## First diagnostic command

```bash
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver both
```

Default output reports:

- LaVague driver imports and constructor signatures.
- Selenium/Playwright Python package imports.
- Chrome/Chromium/Chromedriver command availability hints.
- Playwright browser-cache hints.

It does not launch a browser unless `--construct` is passed.

## Symptom: `ModuleNotFoundError` for LaVague or driver packages

Likely causes:

- The active Python environment does not have the LaVague bundle or selected integration package installed.
- Playwright support was not installed even though Selenium support is available.

Fix pattern:

```bash
python -m pip install lavague
python -m pip install lavague-drivers-playwright  # only if Playwright is needed
```

Then rerun the probe with `--check-imports`. Keep provider credentials and full agent execution out of the driver import check.

## Symptom: Chrome, Chromium, or Chromedriver missing

Signals:

- Probe shows no Chrome/Chromium command and no `chromedriver` command.
- `SeleniumDriver(..., --construct)` fails with a Selenium `SessionNotCreatedException`, `WebDriverException`, or browser-not-found message.
- Selenium Manager may attempt to locate or download a driver, but offline/locked-down environments can block it.

Fix pattern:

1. Install a compatible Chrome or Chromium browser for the host.
2. Install or expose a compatible driver when Selenium Manager cannot handle it.
3. Confirm shell visibility:

   ```bash
   command -v google-chrome || command -v chromium || command -v chromium-browser
   command -v chromedriver || true
   ```

4. Rerun:

   ```bash
   python sub-skills/browser-drivers/scripts/lavague_driver_probe.py --driver selenium --construct --headless
   ```

Do not treat missing Chrome as a model/provider problem. Fix browser runtime first.

## Symptom: Playwright imports but browser binaries are missing or stale

Signals:

- `lavague.drivers.playwright` imports, but construction fails with a message asking to install browser drivers.
- Probe reports a Playwright Python package but no Chromium cache hints.
- Probe shows cached executables, yet construction still fails with a missing executable for a different Playwright browser revision.

Fix pattern:

```bash
python -m playwright install chromium
```

If that still fails, the local browser cache is usually stale or mismatched with the installed Playwright revision. Reinstall Chromium for the active Playwright package rather than assuming the cache is usable.

If the host needs OS-level browser dependencies and the user has permission, install those dependencies through the host package manager or Playwright's dependency helper. Do not run downloads from a reusable script by default; ask for explicit permission.

## Symptom: headed mode fails with `DevToolsActivePort`, display, or Chrome crash errors

Likely causes:

- `headless=False` was used in a non-GUI environment such as a container, VM, notebook, or remote shell.
- A Chrome profile is locked or incompatible.
- Browser sandbox/display dependencies are missing.

Fix pattern:

- Use `SeleniumDriver(headless=True)` or `PlaywrightDriver(headless=True)` for CI and non-GUI runs.
- Use `headless=False` only when a display server is available and the task needs manual login/CAPTCHA handling.
- If using a profile, close other browser instances using the same profile or use a copied profile directory supplied by the user.
- For Windows Subsystem for Linux issues, prefer a GUI-capable WSL2 setup when headed mode is required.

## Symptom: CAPTCHA, login, or pop-up blocks a fresh browser

Fresh sessions have no cookies and can trigger bot-protection flows.

Recovery options:

1. Use a user-supplied `user_data_dir` so the browser starts with existing cookies and settings.
2. Use `headless=False`, navigate to the site, let a human resolve login/CAPTCHA/pop-ups, then resume the automated objective.
3. For Selenium, attach to an already-launched debug Chrome with a Selenium `Options` object and `debuggerAddress`.

Never persist profile paths, cookies, or credential values in generated files or logs.

## Symptom: iframe interactions fail

Checks:

- Prefer Selenium for complex iframes. Its driver resolves iframe-containing XPaths by switching frames and then resetting to default content.
- Confirm the target element is actually in the current frame and visible/enabled.
- Cross-origin frames can still block control depending on browser policy and page behavior.
- If a task example also changes the model context, route model/context issues separately; driver selection alone does not fix provider errors.

## Symptom: tabs are visible but the agent stays on the wrong tab

Checks:

- Selenium implements `get_tabs()` and `switch_tab(tab_id)`. Use `SWITCH_TAB n` through Navigation Controls when a click opened a new tab.
- `tab_id` is zero-based in Selenium's current window-handle order.
- The inspected Playwright driver does not implement feature-parity tab switching. Do not promise `SWITCH_TAB` behavior with Playwright unless a local verification proves it.

## Symptom: `SCAN` or scroll misses content

How LaVague controls work:

- `SCAN` captures whole-page screenshots by repeatedly saving screenshots, scrolling down, waiting for idle, and stopping at page bottom or a maximum count.
- `SCROLL_DOWN` and `SCROLL_UP` call driver scroll helpers.
- For nested scroll panes, tell the navigation engine to `hover` an element in the pane first. Selenium records the hovered XPath and can scroll that container.
- Page-level scans can miss content inside independently scrollable components.

If a task requires a dropdown or hover-revealed menu, choose Selenium; its action schema includes `dropdownSelect`, `hover`, and container `scroll` actions.

## Symptom: Selenium needs custom launch options

Use Selenium `Options`, a factory, or an existing WebDriver injection.

Options pattern:

```python
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--some-runtime-flag")
driver = SeleniumDriver(options=options)
```

Factory pattern:

```python
def build_driver():
    ...

driver = SeleniumDriver(get_selenium_driver=build_driver)
```

Existing object pattern:

```python
driver = SeleniumDriver(driver=already_created_webdriver)
```

Remember that LaVague still adds driver-level flags/capabilities in its default flow when it owns the options, and `destroy()` closes the underlying driver.

## Symptom: Browserbase remote Selenium fails

Checks:

- Browserbase is Selenium-only in this skill; Playwright does not have this remote helper.
- Network access to the remote WebDriver endpoint is required.
- Supply Browserbase credential values at runtime, either through constructor arguments or environment variables `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`.
- Do not run the remote connection as a default check: creating a Browserbase session performs a network request and consumes remote resources.

## Symptom: Playwright selected but behavior differs from Selenium

Expected limits:

- Playwright driver support is not complete feature parity with Selenium.
- Do not assume robust multi-tab support, Browserbase remote support, Selenium `Options`, dropdown-specific action generation, or hover/container-scroll action generation.
- The Playwright sync API has documented compatibility limits in notebooks and Gradio demo mode.
- If a task hits one of these limits, switch to Selenium unless Playwright is a hard requirement.

## Symptom: imports succeed but noisy warnings appear

LaVague imports can transitively import broader model/retriever dependencies. If warnings mention optional NLP data, package-resource deprecations, or provider libraries but the driver imports and signatures succeed, treat them as environment warnings. Route broad install/import cleanup to the root LaVague troubleshooting guidance; do not misdiagnose browser binaries from unrelated warnings.
