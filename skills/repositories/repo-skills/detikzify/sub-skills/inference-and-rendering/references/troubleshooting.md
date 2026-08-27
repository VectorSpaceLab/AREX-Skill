# Troubleshooting

## Model loading

- If a v1 model path fails, check whether `legacy` support is installed and whether the model name belongs to the legacy list.
- If a text prompt fails, verify that the adapter load path ran and that the processor knows how to handle text.
- If a remote `modality_projector` path is used, make sure the environment can fetch it.

## Generation and search

- `sample()` returns one document; `simulate()` may return many.
- If search appears to stall, check the MCTS timeout and the compile timeout separately.
- If the search score never improves, confirm that the metric path matches the task.

## Compile / rasterize

- A successful compile is not enough; the output must also rasterize to a meaningful image.
- `latexmk` failures usually mean the TeX toolchain is incomplete or the PATH is wrong.
- Missing `article.cls`, `tikz.sty`, or `pgf.sty` means TeX packages are incomplete.
- Missing `pdftoppm` or Ghostscript breaks the rasterization helper.

## Image input

- Image inputs may come from paths, URLs, base64 strings, or PIL images.
- Unsupported or malformed image strings should be handled before the pipeline is called.
- Use the preprocessing helper when whitespace or padding changes the model's effective view of the input.
