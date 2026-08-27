# Installation

## Base package

Install the package and the examples workflow surface with:

```bash
pip install "detikzify[examples]"
```

## Optional extras

- `legacy`: needed for the older v1 model family and its `timm`-backed code paths.
- `deepspeed`: needed when you want the training scripts to use DeepSpeed.
- `examples`: includes the evaluation extras and `diffusers` used by the repo's example workflows.

## System dependencies for rendering workflows

The compile/rasterize path and the web UI MCTS gallery require a real TeX toolchain plus PDF tooling.

Make sure the host provides:

- TeX Live 2023 or equivalent
- `latexmk`
- `pdflatex` or another LaTeX engine supported by the repo
- `tikz.sty`, `article.cls`, and `pgf.sty`
- Ghostscript
- Poppler utilities such as `pdftoppm`

## Workflow-specific extras

- `examples/refine.py` needs a TRL build with vision support in addition to the package extras.
- `examples/sketchify.py` is GPU-heavy and depends on the diffusion stack plus downloadable model weights.
- Training workflows expect CUDA-capable PyTorch when they are launched on GPU hardware.

## Smoke checks

After installation, run the bundled safe checks:

```bash
python scripts/api_smoke.py
python scripts/tikz_smoke.py
```

If you need the browser app surface, also run:

```bash
python scripts/webui_help.sh
```
