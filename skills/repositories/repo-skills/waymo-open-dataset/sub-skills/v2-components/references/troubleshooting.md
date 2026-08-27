# V2 Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pyarrow` missing or schema construction fails | Incomplete WOD runtime install or leaf columns without Arrow types | Install the WOD wheel dependencies and ensure every leaf dataclass field uses `create_column(arrow_type=...)`. |
| Merge returns a Cartesian product | Left and right tables share only a subset of key columns | Use `left_group=True` or `right_group=True` on the side with extra key columns, and inspect `key.` columns before merging. |
| Reconstructed component misses repeated values | Repeated nested column names lack `[*]` | Use `create_column(is_repeated=True)` on repeated dataclass fields; do not hand-write column names. |
| Dask merge behaves differently from Pandas | Dtype mismatch in key columns or lazy computation hides errors | Cast key dtypes consistently and compute a small sample before running a large join. |
| Object-asset payload cannot be decoded as numeric columns | Ray payloads are compressed/encoded | Use object-asset codec utilities and keep codec config with the payload. |
| Tiny custom component raises an assertion on a field type | Dataclass annotations were postponed to strings, so WOD type introspection cannot see the nested `Key` or dataclass type | Avoid `from __future__ import annotations` in small WOD component definitions or resolve annotations before calling schema/flatten helpers. |
