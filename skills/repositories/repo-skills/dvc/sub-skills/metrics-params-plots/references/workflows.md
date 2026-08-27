# Metrics, Params, and Plots Workflows

Use these recipes when a future agent needs repeatable commands or `dvc.yaml` snippets for DVC metrics, params, and plots. Prefer JSON output for automation and Markdown output when the result is going into a review comment.

## Inspect Metrics

```bash
dvc metrics show
dvc metrics show --json
dvc metrics show --md --precision 4
dvc metrics show reports/metrics.json reports/eval.yaml --json
dvc metrics show -R reports --json
dvc metrics show --all-branches --json
dvc metrics show --all-tags --json
dvc metrics show --all-commits --json
```

Notes:

- `targets` limit the command to metrics files or directories; `-R` recursively searches directories.
- `--json` preserves machine-readable structure and exception details for failed revisions.
- `--md` renders a GitHub-flavored Markdown table.
- `--precision <n>` rounds numeric display values; the default CLI precision is 5 digits after the decimal point.
- Metrics files do not have to be declared in `dvc.yaml` when passed as explicit targets.

## Compare Metrics

```bash
dvc metrics diff
dvc metrics diff HEAD workspace
dvc metrics diff HEAD~1 HEAD --json
dvc metrics diff HEAD workspace --targets reports/metrics.json --json
dvc metrics diff HEAD workspace --targets reports --recursive --json
dvc metrics diff HEAD workspace --all --md --precision 4
dvc metrics diff HEAD workspace --no-path
```

Behavior to expect:

- With no revisions, the old revision defaults to `HEAD` and the new revision defaults to `workspace`.
- Numeric metric changes include `old`, `new`, and `diff`; nonnumeric values show `old` and `new`.
- Unchanged metrics are omitted unless `--all` is supplied.
- Malformed or missing metric files may still produce a partial diff plus an `errors` object in JSON/API-level structures.

## Inspect and Compare Params

This checkout's CLI exposes `dvc params diff`; param display is available through `dvc.api.params_show()` and the bundled helper script.

```bash
dvc params diff
dvc params diff HEAD workspace
dvc params diff HEAD~1 HEAD --json
dvc params diff HEAD workspace --targets params.yaml --json
dvc params diff HEAD workspace --targets params.yaml other_params.toml --deps --json
dvc params diff HEAD workspace --all --md
dvc params diff HEAD workspace --no-path
python scripts/summarize_metrics_params.py --params-target params.yaml --stage train --deps
```

Behavior to expect:

- With no revisions, the old revision defaults to `HEAD` and the new revision defaults to `workspace`.
- `--targets` accepts params files even when they are not declared as stage params.
- `--deps` limits diff output to params used as stage dependencies.
- Nested params are displayed with dotted key paths such as `model.depth`.
- Lists and dicts can appear as stringified `old` / `new` values in param diffs; metrics preserve numeric `diff` values when possible.

## Declare Metrics and Plots on a Stage

Use metrics/plot stage outputs when a command produces evaluation files that should be tracked and compared.

```bash
dvc stage add -n train \
  -d src/train.py -d data/features.csv \
  -p params.yaml:model.depth,model.lr \
  -M reports/metrics.json \
  --plots-no-cache reports/training.tsv \
  python src/train.py
```

Key declarations:

- `-m` / `--metrics` declares a metric output and stores it in the DVC cache.
- `-M` / `--metrics-no-cache` declares a metric output but leaves it as a normal workspace/Git file.
- `--plots` declares a plot output and stores it in the DVC cache.
- `--plots-no-cache` declares a plot output but leaves it as a normal workspace/Git file.
- `-p` / `--params` declares params dependencies; syntax is `[<filename>:]<params_list>`.
- Omitting `<filename>:` in `-p` means `params.yaml`.

Common params syntax:

```bash
-p model.depth,model.lr
-p params.yaml:model.depth,model.lr
-p configs/train.toml:optimizer.lr,batch_size
-p configs/params.py:CONST,Config.foo
```

The parser groups repeated `-p` values by file, so multiple `-p params.yaml:key` flags are merged in the stage definition.

## Top-Level `dvc.yaml` Declarations

Top-level declarations let DVC discover metrics, params, or plots outside one specific stage output.

```yaml
metrics:
  - reports/metrics.json
  - reports/eval.yaml

params:
  - params.yaml
  - configs/train.toml

plots:
  - reports/training.tsv
  - reports/confusion.json:
      template: confusion
      x: actual
      y: predicted
      title: Confusion matrix
```

Top-level plot definitions may be strings or one-key mappings. When the key is a data path, DVC uses that file as the plot source. When the key is a plot id and `x` or `y` maps source files to fields, DVC can combine multiple files into one plot.

## Multi-Source Plot Definitions

Use multi-source definitions when one logical chart combines training/validation/test files.

```yaml
plots:
  - accuracy_by_split:
      x: step
      y:
        reports/train.tsv: accuracy
        reports/valid.tsv: accuracy
      title: Accuracy by split
      x_label: Step
      y_label: Accuracy
      template: linear
```

For separate x/y source files, map both axes:

```yaml
plots:
  - error_vs_leaf_nodes:
      template: simple
      x:
        dvclive/plots/metrics/Max_Leaf_Nodes.tsv: Max_Leaf_Nodes
      y:
        dvclive/plots/metrics/Error.tsv: Error
```

DVC resolves source paths relative to the `dvc.yaml` containing the `plots:` definition and normalizes plot sources to POSIX-style paths in JSON output.

## Show or Export Plots Without Opening a Browser

```bash
dvc plots show reports/training.tsv --json -x step -y accuracy --out dvc_plots
dvc plots show reports/training.tsv --show-vega -x step -y accuracy
dvc plots show --json --split --out vis_data
dvc plots diff HEAD workspace --targets reports/training.tsv --json --out dvc_plots
dvc plots diff HEAD workspace --targets reports/training.tsv --show-vega -x step -y accuracy
```

Use `--json` or `--show-vega` for CI, notebooks, or agents that cannot open a browser. Avoid `--open` unless the user explicitly wants an interactive browser.

## Configure Plot Output and Templates

```bash
dvc plots templates
dvc plots templates linear
dvc plots modify reports/training.tsv --template linear -x step -y accuracy --title "Training accuracy"
dvc plots modify reports/training.tsv --unset title y_label
dvc config plots.out_dir dvc_plots
dvc config plots.auto_open false
dvc config plots.html_template plots/template.html
```

Config keys supported by this checkout:

- `plots.out_dir`: default directory for generated HTML/static plot output.
- `plots.auto_open`: whether `dvc plots show` opens the generated HTML automatically.
- `plots.html_template`: HTML template path; relative paths are resolved under the DVC metadata directory.

`dvc plots modify` updates display properties for stage-defined plots. It does not affect image plots and does not run the stage.

## Minimal Validation Loop

When adding metrics or plots to an existing pipeline, use this sequence:

```bash
dvc stage add -n evaluate -d src/evaluate.py -d model.pkl -M reports/metrics.json --plots-no-cache reports/roc.tsv python src/evaluate.py
dvc repro evaluate
dvc metrics show --json
dvc metrics diff HEAD workspace --json
dvc plots show reports/roc.tsv --json -x fpr -y tpr --out dvc_plots
```

If `dvc repro` is expensive or unsafe, inspect the stage declaration and use `dvc repro --dry evaluate` through the data-and-pipelines sub-skill before running it.
