# Data Preparation Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `python -m pix2tex.dataset.dataset --help` exits with required `--out` usage | The module parser disables default help and requires output. | Use documented commands or run the bundled input checker; this is a CLI quirk, not necessarily a broken install. |
| `ModuleNotFoundError: imagesize` | Training-related dependency missing. | Install `pix2tex[train]` or install `imagesize` before dataset or resizer workflows. |
| `ValueError` converting image basename to int | PNG names are not integer line indices. | Rename images to `0.png`, `1.png`, ... matching formula file line numbers or rebuild mapping. |
| `IndexError` reading equation line | Image index is greater than available formula lines. | Check max image basename and formula line count with `check_dataset_inputs.py`. |
| Render command cannot find `xelatex` or `convert` | System TeX/ImageMagick/Ghostscript stack missing. | Install system tools or skip rendering; do not treat Python package import as proof of rendering readiness. |
| Many formulas fail rendering | Bad LaTeX syntax, unresolved macros, unsupported environments, missing fonts. | Run local extraction with `--demacro`, inspect failures, reduce batch size, and test a small sample. |
| Dataset size is much smaller than expected | Dimension filters or sequence length filters dropped examples. | Inspect image sizes, formula lengths, and config `max_width`, `max_height`, `max_seq_len`. |
| Scraping stalls or returns few formulas | Network/rate limit/page structure issue. | Stop large recursive scraping; use local seed data or lower depth after approval. |
