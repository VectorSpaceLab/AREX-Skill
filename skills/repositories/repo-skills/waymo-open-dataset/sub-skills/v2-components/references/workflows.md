# V2 Workflows

## List available components

```python
from waymo_open_dataset import v2
print(v2.ALL_TAGS)
```

Use tags to identify component directories or Parquet partitions. Keep the tag name and component class together; avoid hard-coding only a filename when a class exists.

## Create and round-trip a component-like dataclass

```python
import dataclasses
import pyarrow as pa
from waymo_open_dataset.v2 import component

@dataclasses.dataclass
class TinyKey(component.Key):
    segment_context_name: str = component.create_column(arrow_type=pa.string())

@dataclasses.dataclass
class TinyComponent(component.Component):
    key: TinyKey
    score: float = component.create_column(arrow_type=pa.float32())

row = TinyComponent(key=TinyKey('ctx'), score=0.5)
flat = row.to_flatten_dict()
restored = TinyComponent.from_dict(flat)
schema = TinyComponent.schema()
```

Check that leaf fields declare Arrow types and repeated fields use `is_repeated=True`. A missing Arrow type usually appears later as a schema failure.

## Merge component DataFrames

```python
from waymo_open_dataset import v2
merged = v2.merge(left_df, right_df, left_nullable=False, right_nullable=True)
```

`v2.merge` selects common key columns using `key_prefix` (default `key.`). If one table has extra key columns and you want grouped lists instead of a cross product, pass `left_group=True` or `right_group=True` for the side with extra keys.

## Read Parquet components

Use ordinary Pandas, PyArrow, or Dask readers for Parquet, then keep WOD column names intact. For large splits, prefer Dask to avoid loading every component into memory. After loading, join tables through `v2.merge` rather than manual joins so key grouping semantics stay aligned with WOD tests.
