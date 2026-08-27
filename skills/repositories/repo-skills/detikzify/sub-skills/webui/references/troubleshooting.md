# Troubleshooting

## Startup failures

- If the CLI help works but the UI launch fails, check model download access, CUDA availability, and the TeX toolchain.
- A missing `gradio` or `fastapi` import usually means the package install was incomplete.
- If `timm`-backed legacy models are missing from the dropdown, install the `legacy` extra.

## Rendering failures

- The web UI uses the same compile/rasterize path as the programmatic pipeline.
- Missing `latexmk`, `tikz.sty`, `article.cls`, `pgf.sty`, Ghostscript, or `pdftoppm` will break the gallery flow.
- A document that compiles but does not rasterize is still a runtime failure for the UI.

## Interaction issues

- If the gallery preview does not restore the code view, the user may be hitting a browser interaction quirk rather than a model problem.
- `--lock` prevents model edits by design; it is not a failure.
- `--light` only changes the visual theme and can make dark figures easier to inspect.
