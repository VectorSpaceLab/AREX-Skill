# Other experimental frontends

These APIs are useful when a task explicitly names them, but they are not as stable as `modin.pandas`.

| Frontend | Entry points | Dependency/status notes | Safe use |
| --- | --- | --- | --- |
| Spreadsheet | `modin.experimental.spreadsheet.from_dataframe`, `to_dataframe` | Requires `modin-spreadsheet` and a compatible widget stack. A version mismatch can raise widget-registration errors. | Verify import in the target notebook/runtime before promising UI behavior. |
| Modin NumPy | `modin.numpy.array`, `zeros_like`, `ones_like`, `tri`, `split`, `hstack`, `append`, math/logical functions | Not a complete NumPy replacement. Some unsupported inputs raise `NotImplementedError`. | Validate against NumPy on a tiny fixture and materialize with `_to_numpy()` only when bounded. |
| Modin Polars | `modin.polars.DataFrame`, `modin.polars.Series` | Wraps Polars-like objects over Modin internals and is sensitive to Polars private APIs. A mismatch can raise an import error from Polars internals. | Treat as optional; pin compatible Polars if a simple round-trip import fails. |
| Experimental sklearn | `modin.experimental.sklearn.model_selection.train_test_split` | The current helper performs a row-slice split with `train_size` defaulting to `0.75`; it is not a full sklearn replacement. | Use for simple Modin DataFrame/Series splits only. |
| PyTorch DataLoader | `modin.experimental.torch.datasets.ModinDataLoader` | Requires `torch`; native tests use an external CSV URL. | Use local fixtures only; the loader yields `to_numpy()` row batches. |

## Spreadsheet semantics

`from_dataframe(dataframe, ...)` accepts a Modin DataFrame and returns a `SpreadsheetWidget`. Passing a pandas DataFrame raises `TypeError`. `to_dataframe(spreadsheet)` returns the changed Modin DataFrame and raises `TypeError` for non-widget inputs. Because this is UI/widget dependent, no bundled runtime smoke is provided.

## Modin NumPy quick check

```python
import numpy
import modin.numpy as np

arr = np.array([[1.0, 2.0], [3.0, 4.0]])
assert (np.zeros_like(arr)._to_numpy() == numpy.zeros_like(arr._to_numpy())).all()
```

Use Modin NumPy when the task names it. Otherwise, prefer `modin.pandas` for tabular workflows and native NumPy for local arrays.

## Modin Polars quick check

```python
import polars
import polars.testing
import modin.polars as pl

actual = pl.DataFrame({"a": [1, 2, 3]})._to_polars()
expected = polars.DataFrame({"a": [1, 2, 3]})
polars.testing.assert_frame_equal(actual, expected)
```

If importing `modin.polars` fails because a Polars private symbol moved, report the version mismatch and do not route a production task through the frontend until pinned.
