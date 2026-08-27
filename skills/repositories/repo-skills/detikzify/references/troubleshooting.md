# Troubleshooting

## Import or install failures

- If `import detikzify` fails, check the active environment with `python -m pip check` and re-run the install in a clean prefix.
- If the import works only from a repository checkout, verify that the package was installed in editable or normal package form and that the skill does not depend on the checkout path.
- If you need v1 model support and the loader cannot resolve the legacy branch, install the `legacy` extra so `timm` is available.

## CUDA / GPU issues

- A successful CPU import does not prove GPU support.
- Verify `torch.version.cuda`, `torch.cuda.is_available()`, and a tiny CUDA tensor allocation.
- If the package can import but CUDA is unavailable, you likely have a CPU-only wheel, an incompatible driver, or a broken GPU pass-through.

## TeX / compile / rasterize issues

- `TikzDocument.compile()` needs `latexmk` and a working LaTeX engine.
- Missing `tikz.sty` or `article.cls` means the TeX distribution is incomplete.
- Missing `pdftoppm` or Ghostscript breaks rasterization and SVG/PDF post-processing.
- A document can compile but still rasterize to an empty image; check `TikzDocument.has_content`, not just `status == 0`.
- If the compile log points to a different file, inspect `TikzDocument.errors` before assuming the root TikZ source is at fault.

## Adapter and text-conditioning issues

- Text prompts require an adapter-aware load path.
- If text conditioning fails, verify that the processor expects text and that the adapter checkpoint is loaded.
- Do not assume plain image-only loading can synthesize text-conditioned TikZ.

## Web UI issues

- `python -m detikzify.webui --help` only checks the CLI surface; it does not prove the browser UI can launch with the selected model.
- The UI can still fail later if the model download is missing, the chosen algorithm is unsupported, or TeX tools are absent.
- The `--light` flag only changes theme behavior; it does not affect generation quality.

## Training issues

- `examples/refine.py` needs the TRL vision-support fork mentioned in the repo documentation.
- Training scripts expect CUDA-capable PyTorch and enough GPU memory for the selected checkpoint and batch size.
- Distributed training relies on `torchrun` and the usual `WORLD_SIZE` / rank environment behavior.
- Sketchification depends on the diffusion model path and is not a cheap CPU fallback.

## Evaluation issues

- Metrics are lazily imported; missing optional packages appear only when the metric is first used.
- `CrystalBLEU` depends on the LaTeX tokenization stack and `sacremoses`.
- `DreamSim` and `ClipScore` can require large model downloads before they are usable.

## Dataset and MCTS issues

- `detikzify.dataset.load_dataset(...)` falls back to local package datasets only when the named path exists under the package directory.
- `Node.state` is often treated like a string in tree-printing helpers; keep the state object compatible with the MCTS helper expectations.
- An empty child list means the node is terminal or the `child_finder` failed to add children.
