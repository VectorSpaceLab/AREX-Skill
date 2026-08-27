# Component Catalog

## Descriptor model

- `list_components()` returns two lists: `buildin` and `thirdparty`.
- `load_component(name, stage)` resolves a built-in component first, then checks the `fate.ext.component_desc` entry-point group for third-party descriptors.
- `desc` dumps the merged component descriptor across stages.
- `artifact-type` dumps the role- and stage-filtered runtime I/O view.
- `reader` is special: it writes a metadata-only data handle that downstream tasks resolve by `namespace` and `name`.

## Key user-facing families

### Ingress, alignment, and set operations

| Component | Roles | Primary I/O shape | Notes |
| --- | --- | --- | --- |
| `reader` | `guest`, `host`, `arbiter` | `output_data` as a data-unresolved handle | Bind table identity from `name` + `namespace`. |
| `psi` | `guest`, `host` | `input_data` dataframe → `output_data` dataframe + hidden metric | Set intersection with the `ecdh_psi` / `curve25519` defaults in the sample descriptor. |
| `sample` | `guest`, `host` | `input_data` dataframe → `output_data` dataframe | Sampling with `frac` or `n`, optional hetero sync. |
| `data_split` | `guest`, `host` | `input_data` dataframe → `train_output_data`, `validate_output_data`, `test_output_data` | Default-stage splitter used by both hetero and local-style flows. |
| `union` | `guest`, `host` | `input_datas` dataframe list → `output_data` dataframe | Combines multiple tables into one. |

### Feature prep and statistics

| Component | Roles | Primary I/O shape | Notes |
| --- | --- | --- | --- |
| `feature_scale` | `guest`, `host` | train: `train_data` dataframe → `train_output_data` + `output_model`; predict: `input_model` + `test_data` → `test_output_data` | Stage-specific train/predict component. |
| `statistics` | `guest`, `host` | `input_data` dataframe → `output_model` json model | Feature statistics and summary metrics. |
| `hetero_feature_binning` | `guest`, `host` | train: `train_data` → `train_output_data` + `output_model`; predict: `input_model` + `test_data` → `test_output_data` | Supports quantile/bucket/manual binning and optional transform. |
| `hetero_feature_selection` | `guest`, `host` | train: `train_data` + optional `input_models` → `train_output_data` + `train_output_model`; predict: `input_model` + `test_data` → `test_output_data` | Feature filters and model-driven selection. |
| `feature_correlation` | `guest`, `host` | `input_data` dataframe → `output_model` json model | Pearson-correlation style analysis. |

### Learners

| Component | Roles | Primary I/O shape | Notes |
| --- | --- | --- | --- |
| `coordinated_lr` | `guest`, `host`, `arbiter` | train/predict/cv with dataframe inputs and JSON model outputs | Hetero logistic regression family. |
| `coordinated_linr` | `guest`, `host`, `arbiter` | train/predict/cv with dataframe inputs and JSON model outputs | Hetero linear regression family. |
| `homo_lr` | `guest`, `host`, `arbiter` | train/predict with dataframe inputs and JSON model outputs | Homo logistic regression; arbiter participates in training. |
| `homo_nn` | `guest`, `host`, `arbiter` | train/predict with dataframe or data-directory inputs and model-directory outputs | Neural-network runner-based flow. |
| `hetero_nn` | `guest`, `host` | train/predict with dataframe or data-directory inputs and model-directory outputs | Neural-network runner-based hetero flow. |
| `hetero_secureboost` | `guest`, `host` | train/predict/cv with dataframe inputs and JSON model outputs | SecureBoost with optional warm start and HE params. |
| `sshe_lr` | `guest`, `host` | train/predict/cv with dataframe inputs and JSON model outputs | Local secure multi-party logistic regression; the component initializes MPC. |
| `sshe_linr` | `guest`, `host` | train/predict/cv with dataframe inputs and JSON model outputs | Local secure multi-party linear regression. |

### Evaluation

| Component | Roles | Primary I/O shape | Notes |
| --- | --- | --- | --- |
| `evaluation` | `guest`, `host` | `input_datas` dataframe list; logs metrics instead of emitting data/model artifacts | Consumes prediction rows and reports metrics through the context logger. |

## Internal smoke and demo ids

The installed package also exposes internal or test-oriented built-ins such as `artifact_test`, `dataframe_io_test`, `multi_model_test`, `cv_test2`, `toy_example`, and `dataframe_transformer`. Treat these as smoke or inspection aids, not as the primary end-user recipe surface.

## Current built-in inventory shape

The currently observed built-in ids from `component list` are the families above plus the internal helpers listed here. Use `list` to refresh the exact inventory when the package changes.
