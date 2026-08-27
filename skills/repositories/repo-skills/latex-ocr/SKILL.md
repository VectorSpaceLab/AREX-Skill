---
name: latex-ocr
description: "Guides LaTeX-OCR pix2tex image-to-LaTeX OCR, CLI, Python API, GUI,
  service API, dataset preparation, training, and troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LaTeX-OCR / pix2tex Repo Skill

Use this skill when a task involves the LaTeX-OCR repository or the `pix2tex`
Python package: converting equation images to LaTeX, operating the CLI or
Python API, launching the GUI or API service, preparing OCR datasets, training
or evaluating the model, or troubleshooting optional dependencies.

## First Checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) when you
   need to decide whether this skill matches a current checkout.
2. For a fresh runtime, install the smallest needed extra:
   - `pip install pix2tex` for CLI/Python inference.
   - `pip install "pix2tex[gui]"` for the desktop GUI.
   - `pip install "pix2tex[api]"` for FastAPI/Streamlit service workflows.
   - `pip install "pix2tex[train]"` for dataset/training/evaluation workflows.
3. Run [scripts/check_pix2tex_environment.py](scripts/check_pix2tex_environment.py)
   to check imports, package version, CLI availability, selected extras, and
   CPU/CUDA visibility without downloading checkpoints or running inference.
4. Read [references/troubleshooting.md](references/troubleshooting.md) if an
   install/import/backend issue appears before choosing a sub-skill.

## Route Map

- Read [sub-skills/ocr-inference/SKILL.md](sub-skills/ocr-inference/SKILL.md)
  for CLI and Python OCR inference, image preprocessing, checkpoints, `--no-cuda`,
  output rendering, and prediction-quality troubleshooting.
- Read [sub-skills/interactive-apps-and-api/SKILL.md](sub-skills/interactive-apps-and-api/SKILL.md)
  for `latexocr` GUI, screenshot tools, FastAPI `/predict/` and `/bytes/`
  routes, Streamlit frontend, and Docker API recipes.
- Read [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md)
  for extracting formulas, de-macroing TeX, tokenizer/dataset pickle creation,
  rendering LaTeX into PNGs, and safe data acquisition planning.
- Read [sub-skills/training-and-evaluation/SKILL.md](sub-skills/training-and-evaluation/SKILL.md)
  for model/resizer training, evaluation metrics, config files, checkpoint
  handling, and GPU-memory planning.

## Operating Boundaries

- Do not assume the original repository checkout is available. Runtime guidance
  lives in this skill tree; the source paths in provenance are evidence, not
  links to open during normal use.
- Do not instantiate `LatexOCR()` unless model checkpoint downloads and compute
  are acceptable. Use helper scripts first when you only need environment or
  input validation.
- Treat GUI, Docker, Streamlit, TeX rendering, scraping, and full training as
  optional side-effectful workflows. Ask before starting servers, desktop
  installers, downloads, scraping, or long runs.
- CPU is valid for CLI/Python inference via `--no-cuda` or an arguments object
  with `no_cuda=True`, but it may be slower than CUDA. Do not claim CUDA works
  unless the target environment has a compatible CUDA PyTorch build and a
  successful device smoke check.

## Repository Metadata

- Structured router placement is in
  [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
- Cross-cutting install and optional dependency guidance is in
  [references/troubleshooting.md](references/troubleshooting.md).
