# Datasets Workflows

## When to read

Read this when a task starts with loading a bundled pyts dataset, creating a
synthetic dataset, or looking up UCR/UEA metadata before modeling.

## Verified dataset helpers

Current package signatures:

- `load_basic_motions(return_X_y=False)`
- `load_coffee(return_X_y=False)`
- `load_gunpoint(return_X_y=False)`
- `load_pig_central_venous_pressure(return_X_y=False)`
- `make_cylinder_bell_funnel(n_samples=30, weights=None, shuffle=True, random_state=None, return_params=False)`
- `ucr_dataset_list()` / `ucr_dataset_info(dataset=None)` / `fetch_ucr_dataset(dataset, use_cache=True, data_home=None, return_X_y=False)`
- `uea_dataset_list()` / `uea_dataset_info(dataset=None)` / `fetch_uea_dataset(dataset, use_cache=True, data_home=None, return_X_y=False)`

## Workflow patterns

### 1. Network-free toy data

Use the bundled loaders when you need a small, deterministic dataset for a
smoke test or a reproducible example.

```python
from pyts.datasets import load_gunpoint
X_train, X_test, y_train, y_test = load_gunpoint(return_X_y=True)
```

The installed package smoke check confirms that the packaged loaders return
train/test splits and that `BasicMotions` is multivariate.

### 2. Synthetic data generation

Use `make_cylinder_bell_funnel` when you need a fast univariate toy dataset.

```python
from pyts.datasets import make_cylinder_bell_funnel
X, y = make_cylinder_bell_funnel(n_samples=12, random_state=0)
```

The smoke script prints a `(12, 128)` feature matrix and a `(12,)` label array
for this call.

### 3. Catalog lookup before remote fetch

Use `ucr_dataset_list()` / `uea_dataset_list()` before a remote fetch so you can
validate the dataset name and estimate the dataset family.

```python
from pyts.datasets import ucr_dataset_list, uea_dataset_list
print(len(ucr_dataset_list()), len(uea_dataset_list()))
```

The installed package currently exposes 128 UCR entries and 30 UEA entries in
these catalog helpers.

### 4. Remote fetch helpers

Use `fetch_ucr_dataset` or `fetch_uea_dataset` only when network or a warm
local cache is acceptable.

```python
from pyts.datasets import fetch_ucr_dataset
X_train, X_test, y_train, y_test = fetch_ucr_dataset('GunPoint', return_X_y=True)
```

## Return conventions

- Packaged loaders and remote fetchers return train/test splits when
  `return_X_y=True`.
- `make_cylinder_bell_funnel` returns a synthetic feature matrix and labels,
  and can optionally return generation parameters.
- The packaged multivariate loader `load_basic_motions` returns a 3D array with
  feature/channel axis second.

## Cross-links

- Use `../preprocessing-and-symbols/SKILL.md` once the dataset is loaded and
  you need scaling, discretization, or symbolic transforms.
- Use `../metrics-and-classifiers/SKILL.md` if you are about to score or
  classify the loaded data.
- Use `../multivariate-workflows/SKILL.md` for 3D inputs such as BasicMotions.
