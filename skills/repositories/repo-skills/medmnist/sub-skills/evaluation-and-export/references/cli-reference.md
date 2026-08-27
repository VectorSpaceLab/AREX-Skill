# MedMNIST CLI reference

The module entry point uses Python Fire. Run commands from an environment
where `medmnist` and its declared dependencies are installed:

```bash
python -m medmnist <command> [options]
```

## Read-only metadata

```bash
python -m medmnist available
python -m medmnist info --flag=pneumoniamnist
```

`available` lists the package version and the 18 registry entries. `info`
prints the registry record for one flag, including task, channels, labels,
sample counts, and available download metadata. Neither command downloads data
or modifies a dataset root.

## Save all splits as standard images

```bash
python -m medmnist save \
  --flag=pneumoniamnist \
  --folder=./export \
  --postfix=png \
  --download=False \
  --size=28 \
  --root=./data
```

The public `save` signature is effectively:

```text
save(flag, folder, postfix="png", root=DEFAULT_ROOT,
     download=False, size=None)
```

It constructs the selected dataset once for each split (`train`, `val`,
`test`) and calls its `save`. Therefore the root must contain every split in
the same NPZ and `folder` should be an isolated destination. For a 3-D flag,
use GIF:

```bash
python -m medmnist save \
  --flag=organmnist3d \
  --folder=./export \
  --postfix=gif \
  --download=False \
  --size=28 \
  --root=./data
```

2-D flags support sizes 28, 64, 128, and 224. 3-D flags support 28 and 64.
`size=None` means 28. Passing `--download=True` invokes the dataset download
for a missing file and requires network access; keep it false for an offline or
synthetic-fixture check. A missing file with download false raises a dataset
not-found error rather than silently producing partial output.

## Evaluate a standard result file

```bash
python -m medmnist evaluate \
  --path="./results/pneumoniamnist_test_[AUC]1.000_[ACC]1.000@run1.csv"
```

The public wrapper is:

```text
evaluate(path)
```

It delegates to `Evaluator.parse_and_evaluate(path)`. The filename must encode
an unsuffixed or sized flag and a valid split. A file written by
`Evaluator.evaluate` has the required pandas index and score columns. The
parser sorts the index, computes AUC/ACC, prints a `Metrics(...)` value, and
writes a standardized result next to the input.

The CLI `evaluate` command has no `--root` option. `parse_and_evaluate` creates
its evaluator with the package's default root, so a result file made against a
custom root should be evaluated directly with `Evaluator(..., root=...)`, not
by assuming the CLI can discover that custom root. Use a separate results
folder: a parser call can rewrite a file if its generated standardized name
matches the input name.

## Explicitly excluded operations

The package also exposes `download` and `clean`, and a development-only
`test()` command. They are not evaluation/export smoke operations:

- `download` can fetch many large files and is a network and disk-budget
  operation.
- `clean` removes downloaded `*mnist*.npz` files from the selected root and is
  destructive.
- `test()` runs broad development checks, including downloads and large
  exports.

Do not invoke any of these from an automated local verification unless the
user separately approves the exact root, network use, and cleanup scope.
