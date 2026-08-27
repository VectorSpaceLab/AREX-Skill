# Install and Environment Reference

Read this when choosing packages, extras, optional backends, or safe preflight checks for Docling.

## Package Choice

- `pip install docling` is the normal user-facing install. It is a meta-package that pulls in `docling-slim` with the standard feature set and exposes `docling` / `docling-tools` entry points.
- `pip install "docling-slim[cli]"` is useful when composing a smaller environment and only the CLI dependencies are needed.
- `docling-slim` extras are grouped by capability: format support, CLI, service client, chunking, local models, remote model clients, OCR engines, VLM inline models, ASR, HTML rendering, XBRL, and platform-specific OCR.
- Python support in this repository snapshot is `>=3.10,<4.0`.

## Extras by Task

| Need | Typical install direction | Notes |
| --- | --- | --- |
| Standard CLI and common local conversion | `pip install docling` | Recommended starting point for most users. |
| Slim CLI only | `pip install "docling-slim[cli]"` | CLI imports still need format/model extras for actual conversions that use those paths. |
| PDF/Office/Web/LaTeX/email formats | `docling-slim` format extras or full `docling` | Use the smallest extras matching selected formats. |
| Chunking | full `docling` or `docling-slim[feat-chunking]` | `HybridChunker` uses `docling-core` chunker implementations. |
| Remote docling-serve client | full `docling` or `docling-slim[service-client]` | Requires service URL and optional API key at runtime. |
| Local standard PDF models | full `docling` or `docling-slim[models-local]` | May require Torch/Torchvision and model downloads on first use. |
| VLM inline models | `docling[vlm]` or VLM-specific slim extras | Can be GPU/MLX/network/download heavy. |
| Audio/video ASR | `docling[asr]` plus system `ffmpeg` | Video audio extraction and Whisper decoding require `ffmpeg`. |
| HTML rendering | `docling[htmlrender]` plus browser setup | Playwright-backed rendering can require browser installation. |
| OCR engines | engine-specific extras/binaries | Tesseract CLI requires external executable; EasyOCR/RapidOCR/TesserOCR have their own deps. |

## Safe Preflight

Run the bundled helper first when diagnosing an environment:

```bash
python scripts/check_docling_environment.py --as-json
```

It checks imports, entry points, package versions, and selected optional binaries without converting documents, contacting services, downloading models, or requiring the original repository checkout.

## Model Artifacts

Docling can download models automatically on first use. For offline or controlled environments:

- Use `docling-tools models download` only when model downloads are acceptable.
- Set `artifacts_path` in pipeline options or `DOCLING_ARTIFACTS_PATH` when using prefetched artifacts.
- Do not assume a CLI/API failure is a code bug until the model artifact path and optional backend imports are checked.

## Environment Privacy

Generated skill content should never include local conda prefixes, local Python executable paths, cache paths, private service URLs, or API keys. Treat those as private setup context only.
