---
name: ocr-inference
description: "Guides pix2tex CLI and Python OCR inference from equation images
  to LaTeX, including images, checkpoints, CPU/CUDA choices, and prediction
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OCR Inference

Use this sub-skill when the user wants LaTeX code from an equation image, wants
to call `pix2tex` or `LatexOCR`, or needs to debug inference quality, model
checkpoints, image preprocessing, or CLI flags.

## Quick Route

1. For the Python class and helper signatures, read
   [references/api-reference.md](references/api-reference.md).
2. For CLI commands and flags, read
   [references/cli-reference.md](references/cli-reference.md).
3. For image size/mode/preprocessing decisions, read
   [references/image-preprocessing.md](references/image-preprocessing.md).
4. For common failures, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. Before loading model weights, run
   [scripts/check_pix2tex_cli.py](scripts/check_pix2tex_cli.py) and, for a
   local image, [scripts/inspect_pix2tex_image.py](scripts/inspect_pix2tex_image.py).

## Standard CLI Workflow

```bash
pix2tex --no-cuda path/to/equation.png
```

Use `--no-cuda` for CPU-only environments or deterministic smoke tests. Omit it
only after verifying CUDA PyTorch in the target environment. Add `--no-resize`
when you do not want the auxiliary image-resizer model to adjust image width.
Use `-t/--temperature` to control sampling; lower values make repeated
predictions less variable.

## Standard Python Workflow

```python
from PIL import Image
from pix2tex.cli import LatexOCR

model = LatexOCR()  # may download checkpoints if missing
latex = model(Image.open("equation.png"))
print(latex)
```

Instantiate `LatexOCR()` only when checkpoint downloads and compute are allowed.
For CPU-only use, pass an argparse-like object or CLI route with `no_cuda=True`.

## Boundaries

- For GUI screenshot workflows or API serving, use
  [../interactive-apps-and-api/SKILL.md](../interactive-apps-and-api/SKILL.md).
- For dataset creation, formula rendering, or scraping, use
  [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
- For training/evaluation or model architecture details, use
  [../training-and-evaluation/SKILL.md](../training-and-evaluation/SKILL.md).
