# Metrics, Params, and Plots Data Formats

DVC metrics, params, and plots are regular files plus declarations in `dvc.yaml` or stage outputs. This reference summarizes the formats supported by this checkout and the shapes agents should expect.

## Metrics Files

Supported metric data formats come from DVC's serialization layer:

- JSON: `metrics.json`
- YAML/YML: `metrics.yaml`, `metrics.yml`
- TOML: `metrics.toml`
- Python values through the generic serializer when used as explicit targets, but prefer JSON/YAML/TOML for metrics artifacts.

Metric values that DVC keeps:

- Numbers: `0`, `0.0`, `0.9234`
- Strings: `"ok"`, `"class_a"`
- Nested dictionaries containing supported values

Metric values that DVC drops or cannot compare usefully:

- Empty dictionaries are ignored in metric extraction.
- Unsupported leaf types may be skipped with debug logging.
- Malformed JSON/YAML/TOML surfaces as parse errors in CLI/API results.

Example metric file:

```json
{
  "accuracy": 0.91,
  "loss": 0.17,
  "by_split": {
    "train": 0.95,
    "valid": 0.88
  }
}
```

## Params Files

Supported params formats:

- YAML/YML: default `params.yaml` and nested dictionaries/lists/scalars.
- JSON: `params.json`.
- TOML: `params.toml`.
- Python: `params.py`, including selected constants and class attributes.

Stage params dependency syntax:

```bash
-p learning_rate,batch_size
-p params.yaml:learning_rate,batch_size
-p configs/train.toml:optimizer.lr,batch_size
-p params.py:CONST,Config.hidden_size
```

In `dvc.yaml`, params may appear as strings or mappings:

```yaml
stages:
  train:
    cmd: python train.py
    params:
      - learning_rate
      - params.yaml:batch_size
      - configs/train.toml:
          - optimizer.lr
          - model.depth
      - params.py:
          - CONST
          - Config.hidden_size
```

Top-level params can be declared outside a stage:

```yaml
params:
  - params.yaml
  - configs/train.toml
```

Important behavior:

- When no file is provided in CLI `-p`, DVC uses `params.yaml`.
- Dotted key paths select nested YAML/JSON/TOML/Python values.
- `dvc.api.params_show(stages=...)` can address nested stage files as `subdir/dvc.yaml:stage-name`.
- If multiple params files define the same top-level key, public API output prefixes duplicates as `<file>:<key>`.

## Plot Data Files

Supported plot source formats:

- JSON: lists of row objects or structured values suitable for Vega conversion.
- YAML/YML: YAML equivalents of JSON plot data.
- CSV: parsed as rows of strings.
- TSV: parsed as rows of strings.
- Images: supported by DVC render image extensions, such as PNG/JPG/SVG-style image outputs.

CSV/TSV behavior:

- Headers are used by default.
- `--no-header` sets generated field names to string indexes: `"0"`, `"1"`, `"2"`, and so on.
- All CSV/TSV cell values are strings in parsed plot data.

Example TSV:

```text
step	accuracy	loss
0	0.71	0.52
1	0.82	0.36
2	0.88	0.25
```

Command:

```bash
dvc plots show reports/training.tsv -x step -y accuracy --json
```

## Stage Plot Outputs

Stage outputs can declare plots directly:

```yaml
stages:
  train:
    cmd: python train.py
    deps:
      - src/train.py
    params:
      - params.yaml:model.lr,model.depth
    metrics:
      - reports/metrics.json:
          cache: false
    plots:
      - reports/training.tsv:
          cache: false
          x: step
          y: accuracy
          title: Training accuracy
```

Equivalent CLI declaration:

```bash
dvc stage add -n train -d src/train.py -p params.yaml:model.lr,model.depth -M reports/metrics.json --plots-no-cache reports/training.tsv python src/train.py
```

Plot properties can be added or changed later for stage-defined plots:

```bash
dvc plots modify reports/training.tsv -x step -y accuracy --title "Training accuracy"
```

## Top-Level Plot Definitions

Top-level `plots:` definitions are useful when data files are not stage plot outputs or when one logical plot combines multiple source files.

Simple path:

```yaml
plots:
  - reports/training.tsv
```

Path with properties:

```yaml
plots:
  - reports/training.tsv:
      x: step
      y: accuracy
      title: Training accuracy
      x_label: Step
      y_label: Accuracy
      template: linear
```

Named plot with multi-file y values:

```yaml
plots:
  - accuracy_by_split:
      x: step
      y:
        reports/train.tsv: accuracy
        reports/valid.tsv: accuracy
      title: Accuracy by split
```

Named plot with separate x and y source files:

```yaml
plots:
  - error_vs_leaf_nodes:
      template: simple
      x:
        dvclive/plots/metrics/Max_Leaf_Nodes.tsv: Max_Leaf_Nodes
      y:
        dvclive/plots/metrics/Error.tsv: Error
```

The plot schema supports these properties:

- `template`
- `x`
- `y`
- `x_label`
- `y_label`
- `title`
- `header`

Top-level plot definitions support `x`, `y`, `x_label`, `y_label`, `title`, and `template`. Stage output plot properties also support `header` for CSV/TSV handling.

## Plot Config

Repository config supports a `plots` section:

```ini
['plots']
out_dir = dvc_plots
auto_open = false
html_template = plots/template.html
```

The CLI reads these keys:

- `out_dir`: default output directory for generated HTML/static plot files.
- `auto_open`: open generated HTML automatically when true.
- `html_template`: custom HTML template path; relative values are resolved from the DVC metadata directory.

Use command-line `--out`, `--open`, and `--html-template` to override config for one run.

## Plot JSON Output

`dvc plots show --json` and `dvc plots diff --json` emit renderer-oriented JSON, not the raw `repo.plots.show()` internal structure. Vega renderer entries include:

- `type`: usually `vega` for data-series plots.
- `revisions`: revisions included in the plot.
- `content`: the filled Vega specification.
- optional split-template content when `--split` is used.

Image renderer entries include:

- `type`: `image`.
- `revisions`: the revision for the image data.
- `url`: path under the generated static output directory.

For direct raw structures, use the Repo API only when writing DVC-internal tools; public reusable scripts should prefer CLI JSON or the public `dvc.api` helpers.
