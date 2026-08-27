# Metrics, Params, and Plots Troubleshooting

Use this guide to turn empty, malformed, or surprising metrics/params/plots output into concrete checks. Start with read-only commands before editing `dvc.yaml` or rerunning a pipeline.

## Empty Metrics

Symptoms:

- `dvc metrics show --json` prints no metric data.
- `dvc metrics diff` returns `{}`.
- `dvc.api.metrics_show()` returns `{}`.

Checks:

```bash
dvc root
dvc metrics show --json
dvc metrics show reports/metrics.json --json
dvc metrics show -R reports --json
rg -n "metrics:|metrics-no-cache|reports/metrics" dvc.yaml
```

Likely causes and fixes:

- The file is not declared as a metric: pass it as an explicit target or add it with `-m`, `-M`, or top-level `metrics:`.
- The metric file was never generated: inspect the stage command and use data-and-pipelines guidance for `dvc repro --dry` before rerunning.
- The file exists only in cache and cache objects are missing locally: fetch/pull the needed data before reporting.
- The metric value is an unsupported type or an empty dictionary: write scalar/string/numeric leaves or nested dictionaries with supported leaves.
- No Git commits exist: diff commands return empty results until there is a baseline commit.

## Empty Params

Symptoms:

- `dvc params diff` returns `{}`.
- `dvc.api.params_show()` returns `{}`.
- `--deps` hides keys that appear when reading a params file directly.

Checks:

```bash
dvc params diff HEAD workspace --json
dvc params diff HEAD workspace --targets params.yaml --json
python scripts/summarize_metrics_params.py --params-target params.yaml --stage train --deps
rg -n "params:" dvc.yaml
```

Likely causes and fixes:

- The stage has no params dependencies: add `-p <key>` or edit `stages.<name>.params` carefully.
- `--deps` is limiting output to stage dependency params: rerun without `--deps` or pass explicit targets.
- The stage filter is wrong: for nested stages use `subdir/dvc.yaml:stage-name`.
- The params file is not named `params.yaml`: pass the file explicitly or declare it under top-level `params:`.
- The params file is malformed: validate JSON/YAML/TOML/Python syntax before running DVC commands.

## Ambiguous Duplicate Keys

Symptoms:

- API output contains keys like `reports/train.json:accuracy` or `configs/prod.yaml:lr`.
- An agent expected `accuracy` or `lr` but got file-prefixed keys.

Cause:

- `dvc.api.metrics_show()` and `dvc.api.params_show()` flatten per-file results. If more than one file contains the same top-level key, DVC prefixes the ambiguous key with `<file>:`.

Checks:

```bash
python scripts/summarize_metrics_params.py --metrics-target reports/train.json --metrics-target reports/test.json
python scripts/summarize_metrics_params.py --params-target params.yaml --params-target configs/prod.yaml
```

Fixes:

- Preserve the file-prefixed keys in automation instead of stripping prefixes.
- Query one target at a time when the caller needs unprefixed keys.
- Rename top-level keys in the files if downstream consumers require a flat unique namespace.
- For params, restrict by `--stage` / `stages=` only if stage ownership is the desired filter.

## Wrong Stage Paths or Params Syntax

Symptoms:

- `params_show(stages="train")` works at repo root but fails or returns `{}` from a subdirectory.
- A stage uses a params file but DVC reports no matching params dependency.
- `dvc params diff --deps` misses expected keys.

Checks:

```bash
dvc root
rg -n "stages:|params:" dvc.yaml */dvc.yaml
python scripts/summarize_metrics_params.py --stage subdir/dvc.yaml:train --deps
```

Fixes:

- Use `{relpath-to-dvc.yaml}:{stage}` for nested stage addresses.
- Use `[<filename>:]<params_list>` syntax for CLI `-p`; omitting the filename means `params.yaml`.
- For TOML/JSON/YAML nested keys, use dotted paths like `optimizer.lr`.
- For Python params, use selected names such as `CONST` or `Config.foo`.
- Do not confuse stage target paths with params target file paths; `--targets` on `dvc params diff` means params files.

## Precision and Output Format Surprises

Symptoms:

- CLI table rounds numeric metrics.
- Markdown and JSON output do not look the same.
- Param list/dict changes appear stringified.

Checks:

```bash
dvc metrics show --json
dvc metrics show --md --precision 8
dvc metrics diff HEAD workspace --json --precision 8
dvc params diff HEAD workspace --json
```

Guidance:

- Use `--json` for automation and exact downstream parsing.
- Use `--precision <n>` for human table/Markdown rendering; default CLI precision is 5.
- Metrics diffs include numeric `diff` where possible.
- Params diffs may stringify lists/dicts in `old` and `new` values; avoid numeric assumptions for params diff fields.
- Use `--no-path` only for human reports where file paths add noise.

## Plot Field, Header, and Template Issues

Symptoms:

- `dvc plots show` creates no visualization.
- `--show-vega` returns nothing or errors.
- The plot uses the wrong x/y fields.
- CSV/TSV rows are keyed as `"0"`, `"1"`, etc.
- A template name or custom template path fails.

Checks:

```bash
dvc plots show reports/training.tsv --json -x step -y accuracy --out dvc_plots
dvc plots show reports/training.tsv --show-vega -x step -y accuracy
dvc plots templates
dvc plots templates linear
python - <<'PY'
import csv
with open('reports/training.tsv', newline='') as f:
    print(next(csv.reader(f, delimiter='\t')))
PY
```

Likely causes and fixes:

- Wrong field names: inspect the data file header or JSON keys, then pass `-x` / `-y` or update `dvc.yaml` plot properties.
- Headerless CSV/TSV: use `--no-header` and refer to fields as `"0"`, `"1"`, etc.
- Unsupported plot file type: data-series plots support JSON/YAML/CSV/TSV; image plots require supported image extensions.
- Template typo: list built-ins with `dvc plots templates`; custom templates should be reachable from the current repo context.
- `--show-vega` needs exactly one target and cannot be combined with `--json`.
- Browser output is not desired: use `--json`, `--show-vega`, and `--out`; avoid `--open`.

## No Plots Loaded

Symptoms:

- CLI warns: `No plots were loaded, visualization file will not be created.`
- `dvc plots show --json` has empty `data` or only `errors`.

Checks:

```bash
dvc plots show --json
dvc plots show reports/training.tsv --json
rg -n "plots:" dvc.yaml */dvc.yaml
```

Likely causes and fixes:

- No stage or top-level plot declarations exist: pass a target explicitly or declare `plots:`.
- The path in `dvc.yaml` is relative to a nested `dvc.yaml`; resolve from that file's directory.
- A directory plot points at an empty directory.
- Cache objects are missing for cached plot outputs.
- An overlapping output declaration prevents collection; inspect `dvc status` and the stage output layout.

## Malformed Metrics, Params, or Plots

Symptoms:

- JSON/YAML/TOML corrupted-file exceptions.
- Plot parse errors for a revision.
- Params API raises instead of returning partial data.

Checks:

```bash
python -m json.tool reports/metrics.json
python - <<'PY'
from pathlib import Path
import tomllib
for path in ['configs/train.toml']:
    with open(path, 'rb') as f:
        tomllib.load(f)
    print(path, 'ok')
PY
dvc metrics show reports/metrics.json --json
dvc params diff HEAD workspace --targets params.yaml --json
dvc plots show reports/training.tsv --json
```

Fixes:

- Validate the file with a format-specific parser before blaming DVC.
- For YAML, check indentation and duplicate/unquoted special values.
- For JSON, remove trailing text or comments.
- For TOML, check table syntax and scalar/list types.
- For Python params, keep selected values importable without side effects.
- If one revision is malformed, compare a known-good revision with `HEAD~1`, `HEAD`, or an explicit branch to isolate when it broke.

## When to Ask for User Input

Ask before mutating when:

- Running `dvc repro` would execute expensive or unsafe user code.
- Fixing malformed params/metrics requires choosing canonical key names or deleting data.
- Changing `plots.auto_open`, `plots.out_dir`, or templates affects user workflow.
- Fetching missing cache objects requires network credentials or remote storage access.
