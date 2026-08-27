# Surprise CLI reference for evaluation

The `surprise` console command evaluates a prediction algorithm with cross-validation. It is useful for quick shell checks, custom rating files, and predefined train/test folds. It is not a hyperparameter-search CLI.

Equivalent module form, useful when the console script is not on `PATH`:

```bash
python -m surprise --help
```

## Command shape

```bash
surprise \
  -algo SVD \
  -params "{'n_epochs': 5, 'n_factors': 20, 'random_state': 0}" \
  -load-custom ratings.txt \
  -reader "Reader(line_format='user item rating', sep=' ', rating_scale=(1, 5))" \
  -n-folds 3 \
  -seed 0
```

What happens:
1. the algorithm class is selected from a fixed CLI list;
2. `-params` is evaluated into algorithm keyword arguments;
3. the dataset is loaded from a custom file, predefined fold files, or a built-in dataset;
4. the dataset is split with `KFold` or `PredefinedKFold`;
5. `cross_validate(..., verbose=True)` prints RMSE and MAE by default.

## Supported algorithm names

`NormalPredictor`, `BaselineOnly`, `KNNBasic`, `KNNBaseline`, `KNNWithMeans`, `SVD`, `SVDpp`, `NMF`, `SlopeOne`, and `CoClustering`.

Use the sibling prediction-algorithms sub-skill for constructor parameters and option semantics before forming a CLI `-params` string.

## Dataset options

| Option | Use | Reader requirement |
| --- | --- | --- |
| `-load-custom <file>` | Load a single local ratings file and create `KFold(n_splits=<n-folds>, random_state=<seed>)` | Required: pass `-reader "Reader(...)"`. |
| `-folds-files "train1 test1 train2 test2 ..."` | Load explicit train/test fold files and use `PredefinedKFold()` | Required: pass `-reader "Reader(...)"`. |
| `-load-builtin <name>` | Load a built-in dataset such as `ml-100k`, then create `KFold` | Not needed; built-in readers are implied. May prompt/download if not cached. |

Prefer `-load-custom` or `-folds-files` for deterministic no-network automation. Built-in loading is convenient for interactive local exploration, but can block on a download prompt when the dataset cache is absent.

## Reader expressions

The CLI imports `Reader`, then evaluates the string supplied to `-reader`. Common forms:

```bash
-reader "Reader(line_format='user item rating', sep=' ', rating_scale=(1, 5))"
-reader "Reader(line_format='user item rating timestamp', sep='\t', rating_scale=(1, 5))"
-reader "Reader('ml-100k')"
```

For dataframe loading, use Python APIs rather than the CLI; the CLI only accepts files or built-in datasets.

## Parameter expressions

The CLI evaluates `-params` and splats the result into the algorithm constructor.

```bash
-params "{'n_epochs': 2, 'n_factors': 5, 'random_state': 0, 'verbose': False}"
-params "{'k': 20, 'sim_options': {'name': 'cosine', 'user_based': False}}"
```

Safety and quoting rules:
- Only pass trusted strings; the CLI uses Python `eval` for both `-params` and `-reader`.
- Quote the full dictionary/expression for your shell.
- Use Python booleans (`True`, `False`) and strings with quotes inside the dictionary.
- A malformed expression is not converted into a friendly validation error; fix the string syntax first.

## Custom-file recipe

Given a whitespace-separated file like:

```text
u1 i1 5
u1 i2 4
u2 i1 3
u2 i2 2
```

run:

```bash
surprise \
  -algo NormalPredictor \
  -load-custom ratings.txt \
  -reader "Reader(line_format='user item rating', sep=' ', rating_scale=(1, 5))" \
  -n-folds 2 \
  -seed 0
```

If `-reader` is omitted with `-load-custom`, the CLI exits with a parser error saying the reader parameter is needed.

## Predefined-fold recipe

Given train/test files already split into folds:

```bash
surprise \
  -algo SVD \
  -params "{'n_epochs': 2, 'random_state': 0}" \
  -folds-files "fold1.train fold1.test fold2.train fold2.test" \
  -reader "Reader(line_format='user item rating', sep=' ', rating_scale=(1, 5))" \
  -seed 0
```

The CLI pairs file paths two at a time: `(train1, test1)`, `(train2, test2)`, and so on. Use an even number of file paths.

## Flags to treat carefully

- `--with-dump` writes one dump file per fold. That is an evaluation side effect, not a recommendation/export workflow. Keep output in a temporary or explicit directory when using it.
- `-dump-dir <dir>` controls where dump files go when `--with-dump` is enabled.
- `--clean` removes the Surprise dataset cache directory and exits. Do not use it in evaluation automation unless the task is explicitly cache cleanup.
- `-v`/`--version` prints the package version and exits.

## Bundled CLI smoke script

Run:

```bash
python scripts/cli_eval_smoke.py
```

It checks CLI help, verifies the missing-reader error path on a temporary custom file, and runs a happy-path custom-file evaluation without built-in dataset downloads.
