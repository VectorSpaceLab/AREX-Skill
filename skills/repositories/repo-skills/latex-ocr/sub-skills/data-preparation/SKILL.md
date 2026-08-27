---
name: data-preparation
description: "Guides pix2tex formula extraction, tokenizer and dataset pickle
  creation, LaTeX rendering, scraping boundaries, and data-format
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation

Use this sub-skill when the user needs to prepare image/LaTeX pairs for
LaTeX-OCR, extract formulas from TeX-like documents, create a tokenizer, build
`Im2LatexDataset` pickle files, render formulas to PNGs, or plan safe data
acquisition. Use this before training and evaluation.

## Quick Route

1. Read [references/data-formats.md](references/data-formats.md) for equation
   text files, image naming, tokenizer JSON, and dataset pickle expectations.
2. Read [references/rendering-and-preprocessing.md](references/rendering-and-preprocessing.md)
   before rendering LaTeX to PNG or normalizing formulas.
3. Read [references/data-acquisition.md](references/data-acquisition.md) before
   web, Wikipedia, StackExchange, arXiv, or Google Drive acquisition.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for
   missing system tools, bad formulas, naming mismatch, and import quirks.
5. Use [scripts/extract_math_snippets.py](scripts/extract_math_snippets.py) for
   safe local formula extraction, and
   [scripts/check_dataset_inputs.py](scripts/check_dataset_inputs.py) before
   running the package dataset builder.

## Typical Dataset Build Flow

```bash
# Validate inputs first; this does not create a pickle.
python scripts/check_dataset_inputs.py --equations math.txt --images images/

# Then build the package dataset pickle when the validation looks right.
python -m pix2tex.dataset.dataset \
  --equations math.txt \
  --images images/ \
  --tokenizer tokenizer.json \
  --out dataset.pkl
```

To train a new tokenizer from formulas only:

```bash
python -m pix2tex.dataset.dataset --equations math.txt --vocab-size 8000 --out tokenizer.json
```

## Boundaries

- Training/evaluation commands belong in
  [../training-and-evaluation/SKILL.md](../training-and-evaluation/SKILL.md).
- OCR inference and image capture belong in
  [../ocr-inference/SKILL.md](../ocr-inference/SKILL.md).
- Network scraping, large downloads, TeX rendering, and dataset pickle creation
  can be long or system-dependent; confirm the user's budget and tools before
  running them.
