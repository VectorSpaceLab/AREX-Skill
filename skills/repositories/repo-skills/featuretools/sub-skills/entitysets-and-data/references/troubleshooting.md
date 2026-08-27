# EntitySets Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `EntitySet.plot` fails | Graphviz Python package or `dot` binary is missing | Install both Graphviz layers or skip plotting and use path inspection instead. |
| `to_parquet` raises `ImportError` | `pyarrow` is missing | Install `pyarrow` or use `to_pickle` / `to_csv`. |
| `to_parquet` fails on a path object | The method expects a string path in this release | Convert the path with `str(path)` before calling the method. |
| `set_secondary_time_index` rejects a mapping | The time column type does not match the entityset time type, or the column is not recognized as time-like | Use a datetime-to-datetime or numeric-to-numeric mapping and confirm the named columns exist. |
| `normalize_dataframe` errors on `additional_columns` or `copy_columns` | The helper expects lists | Wrap the column names in a list even when only one column is used. |
| `query_by_values` returns surprising rows | The entityset graph or time index is not the one you expected | Recheck the dataframe name, column name, and time column before querying. |
| Demo loader fetches fail | The loader is network-backed or depends on external data | Switch to `load_mock_customer` for offline work. |

## Extra Notes

- `to_pickle` is the safest serialization smoke.
- `load_retail`, `load_flight`, and `load_weather` are optional demos, not the default path.
- If a graph path or data path is written successfully but the reload still fails, verify that the directory is writable and that the saved file name is the same one you pass back into `read_entityset`.
