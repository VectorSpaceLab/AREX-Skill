# Render Troubleshooting

## `pixelshot` is not found

Install the base package in the environment used by the agent:

```bash
pip install pixelrag
pixelshot --help
```

For always-on agent usage, prefer an isolated tool install such as `uv tool install pixelrag` or `pipx install pixelrag` so the `pixelshot` command is on `PATH`.

## Chrome cannot be found

Run:

```bash
pixelshot which-chrome
```

Recovery options:

- Install Chrome/Chromium using the host's normal package manager.
- Set `CHROME_PATH` to an executable browser.
- Use a Playwright Chromium already present on the machine.
- As a last resort, run `pixelshot install-chrome` if downloads are allowed.
- For authenticated pages or remote browser sessions, use `--cdp-url` instead of launching a local browser.

## Authenticated page renders logged-out content

Start Chrome/Brave with a remote debugging port using the profile/session that has the login, then render with:

```bash
pixelshot https://private.example -o ./tiles --cdp-url http://127.0.0.1:9222
```

PixelRAG creates a new tab and closes only that tab. It does not close the user's browser.

## Page is blank or missing late-loaded content

Use:

```bash
pixelshot https://app.example -o ./tiles --wait-network-idle
```

This waits for load plus a networkidle2-style quiet window. It tolerates two persistent analytics/long-poll requests and has a hard cap, so it should not hang forever.

## Only one viewport was captured

Check that you are using a current PixelRAG build. The renderer measures full document height, not only `body.getBoundingClientRect()`, so pages with `html, body { height: 100% }` should still tile past the first viewport. Validate with the smoke script or a simple tall local HTML fixture.

## PDF render fails

Symptoms include `ImportError: pdf2image is required` or a Poppler-related error.

Actions:

- Install `pixelrag[pdf]` or add `pdf2image` to the environment.
- Install Poppler tools if the platform requires external `pdftoppm`/`pdftocairo` binaries.
- Use a small page subset first: `pixelshot paper.pdf -o ./tiles --dpi 150`.
- If the PDF is encrypted or malformed, render a known-good PDF to isolate dependency problems.

## Output has no tiles

- Confirm the input extension is supported.
- Check command stderr/logs for per-file failures.
- For URL lists, ensure the `.txt` file exists and contains non-empty URL lines.
- For images, confirm the source image is readable by Pillow.
- For index handoff, ensure `tiles.json` exists before running chunk/embed stages.
- If logs say `Batch complete: done=0 failed=0`, check whether another service is already listening on PixelRAG's default CDP worker port range starting at 9400. Stop the conflicting service, run on a host without that conflict, or attach to a browser on a different DevTools port with `--cdp-url`.
