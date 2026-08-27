# Configuration Reference

This reference follows the current code-backed `Config` model used by `nannyml.cli` and `nannyml.runner`.

> Note: some older NannyML docs show a higher-level YAML shape with top-level `column_mapping`, `problem_type`, or `output` sections. The current runtime config path is calculator-centric: `input`, `calculators`, `scheduling`, and `ignore_errors`.

## Top-level keys

```yaml
input: ...
calculators: ...
scheduling: ...
ignore_errors: false
```

## Input section

```yaml
input:
  reference_data:
    path: data/reference.csv
    credentials:
      client_kwargs:
        aws_access_key_id: ACCESS_KEY_ID
        aws_secret_access_key: SECRET_ACCESS_KEY
    read_args:
      sep: ','

  analysis_data:
    path: data/analysis.csv

  target_data:
    path: data/analysis_targets.csv
    join_column: id
```

- `reference_data.path` and `analysis_data.path` are required when running from files.
- `target_data` is optional and only needed when analysis targets arrive separately.
- `read_args` are passed through to pandas read functions.
- Cloud readers use `fsspec` credentials.

## Calculators section

Each entry selects one calculator or estimator and the arguments that would normally be passed to its constructor.

```yaml
calculators:
  - type: missing_values
    name: missing-values
    enabled: true
    params:
      column_names: [car_value, salary_range]
      timestamp_column_name: timestamp
      chunk_size: 5000
    outputs:
      - type: raw_files
        params:
          path: out/results
          format: parquet
    store:
      path: out/cache/calculators
      filename: missing-values.pkl
      invalidate: false
```

### Calculator fields

- `type`: registry key such as `missing_values`, `univariate_drift`, `performance`, `cbpe`, `dle`, `reconstruction_error`, `domain_classifier`, `unseen_values`, `summary_stats_avg`, `summary_stats_row_count`, etc.
- `name`: optional display label used in logs.
- `enabled`: set to `false` to skip a calculator.
- `params`: direct constructor kwargs for the selected calculator.
- `outputs`: list of writer configs.
- `store`: optional `FilesystemStore` config for fitted-object reuse.

## Writer configs

Writer entries have the shape:

```yaml
outputs:
  - type: raw_files
    params:
      path: out/results
      format: csv
  - type: pickle
    params:
      path: out/pickles
      filename: monitoring-result.pkl
  - type: database
    params:
      connection_string: sqlite:///
      model_name: demo
```

The registered writer keys are:

- `raw_files`
- `pickle`
- `database`

`raw_files` and `pickle` both need a `filename` at write time if the writer call does not supply one automatically.

## Store configs

`store` configures a filesystem-backed cache for fitted calculators.

```yaml
store:
  path: out/cache/calculators
  credentials:
    client_kwargs:
      aws_access_key_id: ACCESS_KEY_ID
      aws_secret_access_key: SECRET_ACCESS_KEY
  filename: my-calculator.pkl
  invalidate: false
```

- `path` is required.
- `credentials` is optional and passed to `fsspec`.
- `filename` is optional.
- `invalidate: true` forces a refit instead of reusing the cached object.

## Scheduling

```yaml
scheduling:
  interval:
    days: 1

# or
scheduling:
  cron:
    crontab: "*/5 * * * *"
```

Rules from the current scheduler code:

- Only one of `interval` or `cron` may be present.
- `interval` must contain exactly one non-null unit.
- Supported `interval` units are `weeks`, `days`, `hours`, and `minutes`.
- `cron.crontab` is parsed with `CronTrigger.from_crontab`.

## Path templating

The config loader renders `{{minute}}`, `{{hour}}`, `{{day}}`, `{{weeknumber}}`, `{{month}}`, and `{{year}}` in configured paths.

This applies to:

- input paths
- output writer `params.path`
- store paths

Example:

```yaml
input:
  reference_data:
    path: data/{{year}}/{{month}}/reference.csv
```

## Full one-off example

```yaml
input:
  reference_data:
    path: data/reference.csv
  analysis_data:
    path: data/analysis.csv

calculators:
  - type: missing_values
    params:
      column_names: [car_value, salary_range]
      timestamp_column_name: timestamp
      chunk_size: 5000
    outputs:
      - type: raw_files
        params:
          path: out/missing-values
          format: parquet
```

## Full scheduled example

```yaml
input:
  reference_data:
    path: data/reference.csv
  analysis_data:
    path: data/analysis.csv

calculators:
  - type: summary_stats_row_count
    params:
      timestamp_column_name: timestamp
      chunk_period: D
    outputs:
      - type: raw_files
        params:
          path: out/daily-row-count
          format: csv
    store:
      path: out/cache/row-count
      invalidate: false

scheduling:
  cron:
    crontab: "0 6 * * *"
```

## Compatibility note

`ignore_errors` is part of the config model and the CLI surface, but the exact error-handling behavior should be verified against the installed package before relying on it in production automation.
