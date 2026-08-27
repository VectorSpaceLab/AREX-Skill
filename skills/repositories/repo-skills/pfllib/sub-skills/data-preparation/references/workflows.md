# Data Preparation Workflows

## 1. Generate a built-in split

Use the bundled launcher so the checkout path is explicit and the working
directory is normalized to `dataset/`.

```bash
python scripts/run_dataset_generator.py \
  --repo-root <path-to-checkout> \
  --generator generate_MNIST.py \
  --execute -- noniid - dir
```

Useful variations:

- `generate_MNIST.py` for the MNIST label-skew template
- `generate_AGNews.py` for a text label-skew split
- `generate_AmazonReview.py` for a feature-shift split
- `generate_HAR.py` for a real-world sensor split

If you only want to inspect the command, omit `--execute`.

## 2. Validate an existing split

```bash
python scripts/validate_dataset_layout.py \
  --dataset-root <path-to-checkout>/dataset/MNIST \
  --expect-clients 20 \
  --expect-classes 10
```

The validator should confirm:

- `config.json` exists
- `train/` and `test/` exist
- the client count matches the metadata
- a sample `.npz` file round-trips to a dict with `x` and `y`

## 3. Reuse an already generated tree

Many generators detect an existing `config.json` and skip work when the split
parameters match. In that case, treat the generator output as a confirmation
and then run the validator.

## 4. Hand the dataset to experiments

Once the tree is valid, the experiment runner can consume it without additional
preprocessing.

## Recommended order

1. Choose the dataset family and split style.
2. Generate or confirm the dataset tree.
3. Validate the layout.
4. Launch the experiment runner.
