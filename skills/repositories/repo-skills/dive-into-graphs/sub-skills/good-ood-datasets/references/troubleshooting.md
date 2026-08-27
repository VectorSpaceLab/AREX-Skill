# GOOD Troubleshooting

## Download Surprises

- The loader methods fetch data from external URLs when the processed dataset is absent.
- If the task is only about API shape, use the metadata smoke script instead of calling `.load(...)`.

## Wrong Domain or Shift

- Each GOOD dataset supports only a small set of domain names.
- `shift` must be one of `no_shift`, `covariate`, or `concept`.
- A wrong combination raises `ValueError` before any model code runs.

## Empty or Missing Splits

- If `shift='no_shift'`, `id_val` and `id_test` are usually not applicable.
- Confirm the returned split dictionary before constructing a trainer that expects all five splits.
