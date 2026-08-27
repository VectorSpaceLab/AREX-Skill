# Data Formats

## Formula Text Files

`pix2tex.dataset.dataset` expects a plain text file with one LaTeX formula per
line. Empty or malformed lines reduce useful examples. If extracting formulas
from TeX-like documents, run the extraction helper and inspect the result before
building a dataset.

## Image Directory Layout

The dataset builder scans `*.png` files in an image directory. Each PNG basename
must be an integer index into the equation text file. For example:

```text
math.txt
  line 0: x^2 + y^2
  line 1: \frac{a}{b}
images/
  0.png
  1.png
```

The builder converts basenames with `int(os.path.basename(img).split('.')[0])`
and selects `equations[index]`. Non-integer basenames or indices outside the
formula file fail.

## Tokenizer JSON

By default, examples use the package tokenizer under the installed model data.
For custom data, build a tokenizer with:

```bash
python -m pix2tex.dataset.dataset --equations math.txt --vocab-size 8000 --out tokenizer.json
```

Then use that tokenizer when building train/validation pickles and update the
training config `tokenizer` and `num_tokens` fields.

## Dataset Pickles

`Im2LatexDataset.save()` writes a Python pickle that stores grouped image/formula
pairs and tokenizer state. Training configs use fields such as:

```yaml
data: dataset/data/train.pkl
valdata: dataset/data/val.pkl
tokenizer: dataset/tokenizer.json
```

Do not edit these pickle files by hand. Rebuild them when formula lines, image
names, tokenizer, dimensions, or train/validation splits change.
