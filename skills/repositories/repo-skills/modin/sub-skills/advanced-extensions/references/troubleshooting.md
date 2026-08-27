# Advanced extension troubleshooting

## Batch Pipeline

- Error mentions `PandasOnRay`: set `MODIN_ENGINE=Ray` before importing Modin and rerun from a fresh process.
- Query callbacks receive pandas partition DataFrames. Use `pandas` module functions inside callbacks, not `modin.pandas` module-level functions.
- If `pass_output_id=True`, all output nodes must have `output_id`.
- `output_id` cannot be assigned to non-output nodes.
- `fan_out=True` needs a `reduce_fn` and is intended for a one-partition input before fan-out.
- Keep callbacks top-level and pickleable; avoid open files, live DB connections, and mutable global state.

## XGBoost

- The extension supports only the Ray engine.
- If the smoke reports missing `xgboost.rabit` or `xgboost.RabitTracker`, pin a compatible XGBoost version or leave Modin XGBoost unavailable.
- Object dtype columns are rejected. Encode strings/categories before building `DMatrix`.
- Feature names must be unique strings, match width, and avoid `[`, `]`, and `<`.
- Prediction data must carry compatible feature names when the booster was trained with explicit names.
- Keep `num_actors=1` for local smokes before scaling actors or boosting rounds.

## Spreadsheet

- Install `modin[spreadsheet]` or `modin-spreadsheet` explicitly.
- Widget stacks are version-sensitive. If import raises `TypeError: register() missing 1 required positional argument: 'widget'`, treat it as a widget dependency mismatch.
- `from_dataframe` requires a Modin DataFrame; passing pandas DataFrame raises `TypeError`.
- This API is UI-dependent; verify in the exact notebook/runtime where it will be displayed.

## Modin Polars

- If `import modin.polars` fails with a Polars private API error such as missing `polars._utils.various.no_default`, pin compatible Modin/Polars versions or avoid this frontend.
- Validate a tiny `pl.DataFrame(...)._to_polars()` round-trip before scaling.
- Many Polars APIs may be unimplemented; catch `NotImplementedError` and decide whether to fall back to native Polars or `modin.pandas`.

## Modin NumPy

- Modin NumPy is not complete NumPy. Some operations are absent or only support limited input shapes.
- `where` supports boolean constants and objects with `.where`; unsupported condition types raise `NotImplementedError`.
- Materializing with `_to_numpy()` collects the array locally.

## PyTorch DataLoader

- Requires `torch`. If `torch` is not installed, the module import fails.
- Native tests fetch an external CSV; do not use that pattern in a no-network smoke.
- The loader yields row batches from `.iloc[...] .to_numpy()`, so feature selection and batch size should be validated on a local fixture.

## Experimental sklearn split

The experimental `train_test_split` helper slices rows and defaults to `train_size=0.75`. It does not shuffle or stratify. Use sklearn directly if those semantics are required.
