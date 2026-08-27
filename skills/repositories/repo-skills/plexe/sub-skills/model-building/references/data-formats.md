# Plexe data formats

This reference describes the data layouts, input formats, checkpoint locations, and package
artifacts that Plexe expects.

## Supported input dataset formats

Plexe accepts these input formats before normalization:

- Parquet
- CSV
- ORC
- Avro

The workflow normalizes non-Parquet inputs to Parquet before the main phases run.

### CSV options

- `csv_delimiter` controls the field separator.
- `csv_header` controls whether the first row is treated as a header.

The CLI exposes these as `--csv-delimiter` and `--csv-header`.

## Supported data layouts

Plexe's data understanding phase classifies the physical layout of the dataset.

| Layout | Meaning | Typical model families |
| --- | --- | --- |
| `flat_numeric` | Tabular data in a feature matrix | XGBoost, CatBoost, LightGBM, Keras, PyTorch |
| `image_path` | A single column of image file paths | Keras, PyTorch |
| `text_string` | A single column of raw text | Keras, PyTorch |
| `unsupported` | Layout Plexe cannot handle directly | none |

If a dataset is marked `unsupported`, the workflow should stop with a clear error.

## Split behavior

Plexe supports both generated and explicit splits.

### Generated splits

If only a training dataset is provided, Plexe creates train/validation splits and may also
create a test split when final evaluation is enabled.

### Explicit splits

If validation and/or test datasets are provided, Plexe reuses them and may fill in the
missing split when final evaluation requires one.

### Split validation

The workflow validates that split ratios look plausible and that each split is non-empty.

## Build workspace layout

The main workflow writes intermediate data and reports under `work_dir/.build/`.

```text
.build/
  checkpoints/
    01_analyze_data.json
    02_prepare_data.json
    03_build_baselines.json
    04_search_models.json
    05_evaluate_final.json
    06_package_final_model.json
  data/
    normalized/
    splits/
    samples/
    transformed/
  reports/
    00_layout_detection.yaml
    01_statistical_analysis.yaml
    02_task_analysis.yaml
    03_metric_selection.yaml
    04_baseline.yaml
    05_final_evaluation.yaml
```

The exact contents vary with the selected workflow branch and whether final evaluation runs.

## Final model package layout

The packaged model lives at `work_dir/model/` and is archived as `work_dir/model.tar.gz`.

```text
model/
  artifacts/
    model.pkl | model.cbm | model.keras | model.pt
    pipeline.pkl
    label_encoder.pkl
    metadata.json
    history.json
  src/
    pipeline.py
    predictor.py
    trainer.py
  schemas/
    input.json
    output.json
  config/
    hyperparameters.json
  evaluation/
    ...
  model.yaml
  README.md
```

### Model artifact names by family

| Family | Artifact |
| --- | --- |
| XGBoost | `artifacts/model.pkl` |
| CatBoost | `artifacts/model.cbm` |
| LightGBM | `artifacts/model.pkl` |
| Keras | `artifacts/model.keras` |
| PyTorch | `artifacts/model.pt` and `artifacts/model_class.pkl` |

## Retraining-specific package expectations

Retraining needs the original package to expose:

- `artifacts/metadata.json`
- `src/pipeline.py`
- `src/trainer.py`
- the original model artifact for the chosen family

If any of those are missing, retraining should fail fast with a clear message.

## Predictor expectations

The packaged predictors expect these files to exist:

- `artifacts/pipeline.pkl`
- `artifacts/model.pkl`, `model.cbm`, `model.keras`, or `model.pt`
- `artifacts/label_encoder.pkl` when label encoding was used
- `src/pipeline.py` when the pipeline uses custom helper functions

## Data and task metadata in the package

The package metadata stores information such as:

- model type
- task type
- target column
- feature count
- training and validation sample counts
- training hyperparameters
- evaluation summary

This metadata is what the dashboard and predictors use to understand the package.

## Where to go next

- Use `workflows.md` for the sequence of phases and commands.
- Use `configuration.md` for input flags and backend settings.
- Use `troubleshooting.md` when a dataset, split, or package file is missing or malformed.

