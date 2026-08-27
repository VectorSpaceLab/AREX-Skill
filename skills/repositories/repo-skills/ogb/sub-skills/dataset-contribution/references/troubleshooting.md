# Dataset contribution troubleshooting

## Method order

The export helper validates that the methods were called in order. If a later
step fails, rerun the earlier steps before trying to zip again.

## Shape mismatches

- Graphs must have the required keys and matching NumPy shapes.
- Target labels must line up with the dataset family's expected number of data
  points.
- Split dictionaries must contain `train`, `valid`, and `test`.
- If a fresh `split_dict.pt` fails to load under a newer torch release, use
  `torch.load(path, weights_only=False)` for the trusted local file or pin a
  compatible torch build.

## Mapping directory issues

- `copy_mapping_dir()` fails if the mapping directory does not contain a
  `README.md`.
- Keep the mapping contents self-contained; do not rely on the source checkout
  at runtime.

## Family constraints

- Heterogeneous graph export is not implemented for `ogbg`.
- `ogbn` and `ogbl` only support a single graph in the export helper.
- Do not treat the tiny smoke helper as a substitute for validating a real
  contributor release.
