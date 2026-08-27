# Rendering and Formula Preprocessing

## Local Formula Extraction

Use local extraction before considering network scraping:

```bash
python scripts/extract_math_snippets.py paper.tex --demacro --out math.txt
```

The helper distills the repository's `pydemacro` and `find_math` behavior: it
removes common custom macros, strips labels/cites, detects inline/display/math
environments, and writes unique non-empty formulas.

## Rendering LaTeX to PNG

The package renderer uses XeLaTeX and ImageMagick/Ghostscript to convert formulas
into grayscale PNGs, then crops/pads to dimensions divisible by 32.

```bash
python -m pix2tex.dataset.render \
  --data math.txt \
  --out images/ \
  --batchsize 100 \
  --mode equation
```

Rendering is system-dependent. Confirm these tools before running:

- XeLaTeX with `standalone`, `fontspec`, `unicode-math`, and `preview` support;
- ImageMagick `convert` or Windows `magick` plus Ghostscript;
- math fonts such as Latin Modern Math or configured `*Math*.otf` fonts.

## Normalization and Tokenization

The preprocessing script `preprocess_formulas.py` uses a Node/KaTeX parser to
normalize or tokenize formulas. It requires Node.js and the expected KaTeX files
inside the installed package/source distribution. Treat it as a data-cleaning
stage; validate a small sample before processing a large corpus.

## Dimension Filtering

`Im2LatexDataset` groups images by width/height and filters outside the configured
`min_dimensions` and `max_dimensions`. If too many examples disappear, inspect
image sizes and update the model/training config intentionally.
