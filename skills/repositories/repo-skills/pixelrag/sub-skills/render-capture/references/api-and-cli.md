# Render API and CLI

## CLI: `pixelshot`

`pixelshot` is the light capture command installed by the base `pixelrag` package.

```bash
pixelshot INPUT [INPUT ...] --output ./tiles
```

Important flags:

| Flag | Meaning |
| --- | --- |
| `--output`, `-o` | Directory where tile subdirectories are written. |
| `--backend cdp` | Browser backend for URLs and HTML. CDP is the supported fast path. |
| `--workers`, `-w` | Parallel browser processes for URL batches; default is 4. |
| `--tile-height` | Maximum tile height; default 8192 px. |
| `--quality` | JPEG quality; default 85. |
| `--viewport-width` | Browser viewport width; default 875 px, matching embedding width assumptions. |
| `--wait-network-idle` | Wait for networkidle2 after load; useful for SPAs and late fetches. |
| `--dpi` | PDF rendering DPI; default 200. |
| `--cdp-url` | Attach to an existing Chrome/Brave DevTools endpoint. Env: `PIXELSHOT_CDP_URL`. |

Chrome management subcommands:

```bash
pixelshot which-chrome
pixelshot install-chrome
```

Use `which-chrome` first. `install-chrome` may download a browser binary, so treat it as a host change when operating under restricted policies.

## Input dispatch

`pixelshot` accepts:

- `http://` and `https://` URLs.
- `.txt` URL files, one URL per non-empty line.
- `.html` / `.htm` local files, rendered through `file://`.
- `.pdf` files via the PDF backend.
- `.png`, `.jpg`, `.jpeg`, `.webp` image files, copied into the output area.

Unsupported file extensions are skipped with a warning.

## Python API

```python
from pixelrag_render import render_file, render_pdf, render_url
from pixelrag_render.render import render_urls

render_url(
    "https://example.org",
    "./tiles",
    backend="cdp",
    tile_height=8192,
    quality=85,
    viewport_width=875,
    workers=1,
)

render_urls(
    ["https://a.example", "https://b.example"],
    "./tiles",
    stems=["a", "b"],
    workers=4,
    wait_network_idle=True,
)

render_pdf("paper.pdf", "./tiles", dpi=200, pages=[1, 3], stem="paper")
render_file("page.html", "./tiles")
```

Verified signatures:

- `render_url(url, output_dir, backend='cdp', *, tile_height=8192, quality=85, viewport_width=875, workers=1, **kwargs) -> list[Path]`
- `render_urls(urls, output_dir, backend='cdp', *, stems=None, tile_height=8192, quality=85, viewport_width=875, workers=4, **kwargs) -> list[Path]`
- `render_pdf(path, output_dir, *, dpi=200, pages=None, quality=85, stem=None) -> list[Path]`
- `render_file(path, output_dir, backend='cdp', **kwargs) -> list[Path]`

## CDP attach route

Use this for authenticated pages or when no local Chrome binary is available but a browser with DevTools is already running:

```bash
pixelshot https://internal.example -o ./tiles --cdp-url http://127.0.0.1:9222
```

The attach path normalizes `127.0.0.1:9222`, `http://.../json/version`, and browser websocket URLs. It creates a fresh target/tab for each render and closes only that target, not the user's browser.

## Network idle route

For static pages, default load-event capture is fastest. For SPAs or pages that fetch content after load:

```bash
pixelshot https://app.example -o ./tiles --wait-network-idle
```

Network-idle uses Puppeteer-like `networkidle2` semantics: up to two persistent requests are tolerated, a hydration burst waits for quiet, and a hard cap prevents hangs.
