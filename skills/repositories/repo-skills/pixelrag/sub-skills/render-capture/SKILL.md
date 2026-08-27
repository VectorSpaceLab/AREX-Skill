---
name: render-capture
description: "Use PixelRAG pixelshot and pixelrag_render to capture URLs, PDFs,
  HTML, and images as screenshot tile directories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG Render Capture

Use this sub-skill when the task is to turn a document or page into screenshot tiles with `pixelshot` or the `pixelrag_render` Python API.

## Start Here

1. Confirm PixelRAG is installed: `python -c "import pixelrag_render"` and `pixelshot --help`.
2. For a browser render, check Chrome resolution with the root `scripts/pixelrag_doctor.py` or `pixelshot which-chrome`.
3. Choose the input route:
   - URL or URL list: `pixelshot https://example.org -o ./tiles` or a `.txt` file with one URL per line.
   - Local HTML: `pixelshot page.html -o ./tiles`.
   - PDF: install the PDF extra and run `pixelshot paper.pdf -o ./tiles --dpi 200`.
   - Existing image: `pixelshot figure.png -o ./tiles` copies it into the output area.
4. Inspect the output directory before downstream indexing: each rendered document should create `*.png.tiles/` with `tiles.json` and one or more `tile_*.jpg` or chunk files.

## Read or Run

- Read [api-and-cli.md](references/api-and-cli.md) for CLI flags and Python signatures.
- Read [tile-format.md](references/tile-format.md) before handing tiles to `index-build` or debugging manifests.
- Read [troubleshooting.md](references/troubleshooting.md) for Chrome, CDP attach, network-idle, PDF, and incomplete-tile failures.
- Run [pixelrag_render_smoke.py](scripts/pixelrag_render_smoke.py) for a local-only dry run or optional tiny HTML render smoke.

## Common Routes

| Request | Action |
| --- | --- |
| "Screenshot this URL" | Use `pixelshot URL -o ./tiles`; add `--wait-network-idle` for JS-heavy pages. |
| "Capture an authenticated page" | Attach to an already-running browser with `--cdp-url` or `PIXELSHOT_CDP_URL`; PixelRAG creates and closes only its own tab. |
| "Render a PDF" | Use the `pdf` extra and `--dpi`; if Poppler/pdf2image is unavailable, resolve that first. |
| "Why is only one viewport captured?" | Read the network/page-height guidance in troubleshooting; confirm current PixelRAG includes full-page measurement fixes. |
| "Now make it searchable" | Route to `../index-build/SKILL.md` after tiles are present. |

## Validation Checklist

- `pixelshot --help` lists `--cdp-url`, `--wait-network-idle`, `--tile-height`, `--quality`, and `--viewport-width`.
- `pixelshot which-chrome` prints an executable Chrome/Chromium path or an actionable error.
- Output includes at least one tile directory, `tiles.json`, and image files.
- For URL batches, the number of returned tile directories matches rendered inputs; failed inputs should be visible in logs.
- Do not depend on original repo demos at runtime; use this bundled smoke script or write a small local fixture.
