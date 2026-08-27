# Security and DOM Reference

Use this reference for navigation guardrails, download safety, DOM snapshots, iframes, screenshots, and visual debugging.

## Domain Restrictions

`allowed_domains` and `prohibited_domains` are browser/session settings, not prompt instructions.

```python
browser = Browser(
    allowed_domains=["example.com", "*.trusted.example", "https://accounts.example.com"],
    prohibited_domains=["*.ads.example"],
)
```

Behavior verified by security tests:

- If `allowed_domains` is set, navigation is allowed only when a pattern matches.
- `allowed_domains` takes precedence over `prohibited_domains` when both are set.
- `example.com` allows `https://example.com` and automatically allows `https://www.example.com`, but not arbitrary subdomains like `mail.example.com`.
- `*.example.com` matches both `example.com` and subdomains such as `sub.example.com`.
- Full URL patterns with schemes, such as `https://example.com`, require the same scheme.
- Browser internal targets `about:blank`, `chrome://new-tab-page/`, `chrome://new-tab-page`, and `chrome://newtab/` are allowed.
- `data:` and `blob:` URLs are allowed because they have no host.
- Authentication-bypass strings such as `https://example.com@malicious.com` are checked by parsed hostname and are blocked when the real host is not allowed.
- For domain lists with 100 or more entries, BrowserProfile optimizes to a set for exact matching; keep pattern lists under that threshold or use exact domains.

## Blocking IP Addresses

Use `BrowserProfile(block_ip_addresses=True)` when the task must avoid direct IP navigation. The security watchdog detects IPv4, IPv6, and non-standard IPv4 encodings that browsers may resolve.

```python
browser = BrowserProfile(
    allowed_domains=["example.com"],
    block_ip_addresses=True,
)
```

Use this for SSRF-sensitive workflows, internal-network protections, or browser tasks supplied by untrusted users.

## Navigation Enforcement Points

The security watchdog checks three moments:

- Before `NavigateToUrlEvent`: blocks requested disallowed navigation by raising a navigation error.
- After `NavigationCompleteEvent`: catches redirects to disallowed URLs and tries to navigate back to `about:blank`.
- On `TabCreatedEvent`: closes tabs created with disallowed URLs.

If an agent reports a blocked navigation, inspect the final redirected URL, not only the original task URL.

## Download Safety

Downloads can be triggered by normal navigation or `Content-Disposition: attachment`. Browser Use sanitizes attacker-controlled filenames before writing:

- Relative traversal like `../../etc/passwd` becomes `passwd`.
- Absolute paths like `/etc/shadow` become `shadow`.
- Windows backslash paths are reduced to their basename.
- Pure traversal names such as `..`, `.`, `/`, or `\\` fall back to `download`.
- Null bytes are stripped.
- Containment is checked with resolved paths before writing under `downloads_path`.

Still use a dedicated downloads directory:

```python
browser = Browser(downloads_path="./downloads", accept_downloads=True)
```

Treat all downloaded files as untrusted. Do not set `downloads_path` to a project root or home directory.

## Risky Browser Options

Avoid these unless the user explicitly needs them and understands the trade-off:

- `disable_security=True`: adds Chromium flags that disable web security, site isolation, and certificate checks. Use only for controlled local testing.
- `deterministic_rendering=True`: helps screenshot reproducibility but can break sites and increase bot-detection risk.
- `ignore_default_args=True`: removes Browser Use default Chromium safety/stability flags. Prefer a narrow list of ignored flags.
- Shared `user_data_dir` across parallel sessions: risks lock errors and profile corruption.

## Default Extensions and Cookie Handling

`enable_default_extensions` defaults to enabled unless `BROWSER_USE_DISABLE_EXTENSIONS` disables it. The default extension set is automation-oriented and can include ad blocking, cookie banner handling, and URL cleaning. Use `cookie_whitelist_domains` when a site should not have cookie banners automatically handled.

## DOM State and Selector Maps

Browser Use serializes DOM into an `EnhancedDOMTreeNode` tree and a selector map of numbered interactive elements.

```python
state = await browser.get_browser_state_summary()
selector_map = await browser.get_selector_map()
node = await browser.get_dom_element_by_index(1)
text = await browser.get_state_as_text()
```

Use this for debugging mismatched click indices, finding hidden/covered elements, and inspecting what the agent saw.

## Iframes and Cross-Origin Frames

Relevant settings:

```python
browser = Browser(
    cross_origin_iframes=True,
    max_iframes=100,
    max_iframe_depth=5,
)
```

Guidance:

- Keep `cross_origin_iframes=True` when tasks require embedded login, payment, or document frames.
- Reduce `max_iframes` or set `cross_origin_iframes=False` for pages with many third-party iframes causing slow or unstable DOM capture.
- When clicks inside iframes fail, inspect `get_browser_state_summary()` and try direct Actor element or coordinate methods.

## Highlighting and Paint Order

Useful settings:

- `highlight_elements=True`: visual overlays for interactive elements.
- `dom_highlight_elements=True`: debugging-only DOM highlights; if enabled with `highlight_elements`, it takes priority and disables normal highlighting.
- `filter_highlight_ids=True`: hides IDs for elements with long LLM representations.
- `paint_order_filtering=True`: filters elements hidden behind others; disable only when debugging false negatives.

Debug methods:

```python
await browser.remove_highlights()
await browser.highlight_coordinate_click(100, 200)
selector_map = await browser.get_selector_map()
await browser.add_highlights(selector_map)
```

## Screenshots

Session-level screenshots:

```python
png_b64 = await browser.take_screenshot(full_page=False)
element_png = await browser.screenshot_element("button[type='submit']")
```

Actor screenshots:

```python
page_png = await page.screenshot(format="png")
element_png = await element.screenshot(format="png")
```

For Agent-driven screenshots and GIF generation, route to `../../agent-programming/SKILL.md`; this reference owns direct browser/session screenshot APIs.

## File and Privacy Hygiene

- Never commit browser profiles, `storage_state`, downloads, video, HAR, traces, or screenshots that may contain user data.
- Use `user_data_dir=None` or a temporary dedicated directory for untrusted browsing.
- Keep browser paths relative to the user project in examples; ask users for OS-specific executable paths instead of embedding local machine paths.
