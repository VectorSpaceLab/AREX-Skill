# GOOD Data Formats

## Shared Loader Pattern

Every GOOD dataset exposes a static `load(dataset_root, domain, shift='no_shift', generate=False)` helper.
It returns a tuple:

- `dataset_or_split_dict`
- `meta_info`

The split dictionary usually contains `train`, `id_val`, `id_test`, `val`, `test`, `task`, and `metric`.

## Dataset Families

- `GOODHIV`, `GOODPCBA`, `GOODZINC`: molecular graph OOD datasets with `scaffold` and `size` domains.
- `GOODCMNIST`: `color` domain.
- `GOODMotif`: `basis` and `size` domains.
- `GOODCora`: `word` and `degree` domains.
- `GOODArxiv`: `time` and `degree` domains.
- `GOODCBAS`: `color` domain.

## Metadata Fields

`meta_info` includes at least:

- `dataset_type`
- `model_level`
- `dim_node`
- `dim_edge`
- `num_envs`
- `num_classes`
