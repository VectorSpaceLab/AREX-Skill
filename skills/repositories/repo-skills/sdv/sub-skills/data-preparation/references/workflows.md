# SDV data-preparation workflows

Use these recipes to prepare SDV inputs without reopening source code. For signatures and gotchas, see [API reference](api-reference.md). For failures, see [Troubleshooting](troubleshooting.md).

## 1. Download a demo dataset

```python
from sdv.datasets.demo import download_demo, get_available_demos

available = get_available_demos(modality='single_table')
real_data, metadata = download_demo(
    modality='single_table',
    dataset_name='fake_hotel_guests',
)

metadata.validate()
metadata.validate_table(real_data)
```

For multi-table demos:

```python
from sdv.datasets.demo import download_demo

data, metadata = download_demo(
    modality='multi_table',
    dataset_name='example_dataset',
)

metadata.validate()
metadata.validate_data(data)
```

If the user needs a local copy, provide a new, non-existing folder name:

```python
data, metadata = download_demo(
    modality='single_table',
    dataset_name='fake_hotel_guests',
    output_folder_name='sdv_demo_fake_hotel_guests',
)
```

Use `get_source`, `get_readme`, or `save_resource` only for demo resource text/files needed by the task. Do not pass private bucket names or credentials unless the user is explicitly on an Enterprise-capable SDV distribution.

## 2. Read a local CSV folder and detect metadata

For simple top-level CSV folders:

```python
from sdv.datasets.local import load_csvs
from sdv.metadata import Metadata

real_data = load_csvs('data/raw')
metadata = Metadata.detect_from_dataframes(real_data)

metadata.validate()
metadata.validate_data(real_data)
metadata.save_to_json('metadata.json')
```

For CSVs where identifiers may have leading zeros, use `CSVHandler`:

```python
from sdv.io.local import CSVHandler

handler = CSVHandler()
real_data = handler.read(
    folder_name='data/raw',
    file_names=['customers.csv', 'orders.csv'],
    keep_leading_zeros=True,
)
metadata = handler.create_metadata(real_data)

metadata.update_column('customer_id', table_name='customers', sdtype='id')
metadata.update_column('customer_id', table_name='orders', sdtype='id')
metadata.set_primary_key('customer_id', table_name='customers')
metadata.add_relationship(
    parent_table_name='customers',
    child_table_name='orders',
    parent_primary_key='customer_id',
    child_foreign_key='customer_id',
)

metadata.validate()
metadata.validate_data(real_data)
```

`CSVHandler.read` table names come from CSV filename stems. If `file_names` is omitted, it reads all `*.csv` files in the folder.

## 3. Detect metadata from in-memory data

Single table:

```python
from sdv.metadata import Metadata

metadata = Metadata.detect_from_dataframe(
    data=real_data,
    table_name='customers',
    infer_sdtypes=True,
    infer_keys='primary_only',
)
metadata.update_column('signup_date', sdtype='datetime', datetime_format='%Y-%m-%d')
metadata.update_column('email', sdtype='email', pii=True)
metadata.validate()
metadata.validate_table(real_data, table_name='customers')
```

Multi-table:

```python
from sdv.metadata import Metadata

metadata = Metadata.detect_from_dataframes(
    data=real_data,
    infer_sdtypes=True,
    infer_keys='primary_and_foreign',
    foreign_key_inference_algorithm='column_name_match',
)
metadata.validate()
metadata.validate_data(real_data)
```

After detection, inspect `metadata.to_dict()` and correct sdtypes, keys, or relationships. Auto-detection is a starter, not proof that the schema is semantically correct.

## 4. Edit and validate metadata explicitly

```python
from sdv.metadata import Metadata

metadata = Metadata()
metadata.add_table('customers')
metadata.add_column('customer_id', table_name='customers', sdtype='id')
metadata.add_column('age', table_name='customers', sdtype='numerical', computer_representation='Int64')
metadata.add_column('joined_at', table_name='customers', sdtype='datetime', datetime_format='%Y-%m-%d')
metadata.add_column('email', table_name='customers', sdtype='email', pii=True)
metadata.set_primary_key('customer_id', table_name='customers')

metadata.add_table('orders')
metadata.add_column('order_id', table_name='orders', sdtype='id')
metadata.add_column('customer_id', table_name='orders', sdtype='id')
metadata.add_column('amount', table_name='orders', sdtype='numerical', computer_representation='Float')
metadata.set_primary_key('order_id', table_name='orders')
metadata.add_relationship('customers', 'orders', 'customer_id', 'customer_id')

metadata.validate()
metadata.validate_data(real_data)
```

Validation order matters:

1. `metadata.validate()` checks metadata consistency.
2. `metadata.validate_data(data_dict)` checks all tables in multi-table data; `metadata.validate_table(dataframe, table_name=...)` checks one table. Both paths check columns, key uniqueness, missing key values, and sdtype validity; multi-table validation also checks referential integrity.
3. Use `metadata.validate_table(table, table_name='orders')` when the full multi-table dataset is not available.

## 5. Fix unknown foreign-key references

When `metadata.validate_data(data)` reports unknown references, decide whether child rows with bad references may be discarded. If yes:

```python
from sdv.utils import drop_unknown_references

clean_data = drop_unknown_references(
    data=real_data,
    metadata=metadata,
    drop_missing_values=False,
    verbose=True,
)
metadata.validate_data(clean_data)
```

Set `drop_missing_values=True` only when rows with null foreign keys should also be removed.

For difficult relational folders, handle this before fitting multi-table synthesizers:

```python
try:
    metadata.validate_data(real_data)
except Exception:
    clean_data = drop_unknown_references(real_data, metadata, drop_missing_values=True)
    metadata.validate_data(clean_data)
```

## 6. Visualize metadata

```python
graph = metadata.visualize(show_table_details='full')
```

To save an image or PDF:

```python
metadata.visualize(
    show_table_details='summarized',
    show_relationship_labels=True,
    output_filepath='metadata_graph.png',
)
```

Use `show_table_details=None` for multi-table metadata when only table names and relationships should be shown. If rendering fails, first try `output_filepath=None` to confirm the Python graph object can be created, then fix the Graphviz executable issue using [Troubleshooting](troubleshooting.md#graphviz-and-metadata-visualization).

## 7. Read and write local CSV/Excel outputs

Simple CSV save:

```python
from sdv.datasets.local import save_csvs

save_csvs(clean_data, folder_name='prepared_csvs', suffix='_clean', to_csv_parameters={'index': False})
```

CSV handler with overwrite or append control:

```python
from sdv.io.local import CSVHandler

handler = CSVHandler()
handler.write(clean_data, folder_name='prepared_csvs', file_name_suffix='_clean', mode='x')
```

Excel read/write:

```python
from sdv.io.local import ExcelHandler

excel = ExcelHandler(decimal='.', float_format='%.2f')
real_data = excel.read('input.xlsx', sheet_names=['customers', 'orders'])
metadata = excel.create_metadata(real_data)
metadata.validate_data(real_data)

excel.write(real_data, 'prepared.xlsx', sheet_name_suffix='_prepared', mode='w')
```

Excel append mode reads existing sheets and rewrites the workbook with merged content. If `sheet_name_suffix` is provided, new suffixed sheets are created; without a suffix, same-named sheets are concatenated row-wise.

## 8. Save, load, anonymize, and upgrade metadata

Save/load unified metadata:

```python
from sdv.metadata import Metadata

metadata.save_to_json('metadata.json')
metadata = Metadata.load_from_json('metadata.json')
metadata.validate()
```

Overwrite intentionally:

```python
metadata.save_to_json('metadata.json', mode='overwrite')
```

Create a shareable schema without private column/table names:

```python
anonymized_metadata = metadata.anonymize()
anonymized_metadata.save_to_json('metadata_anonymized.json')
```

Upgrade older metadata files with legacy classes when needed:

```python
from sdv.metadata import SingleTableMetadata, MultiTableMetadata

single = SingleTableMetadata.upgrade_metadata('old_single_metadata.json')
single.validate()
single.save_to_json('single_metadata_v1.json')

multi = MultiTableMetadata.upgrade_metadata('old_multi_metadata.json')
multi.validate()
multi.save_to_json('multi_metadata_v1.json')
```

If `Metadata.load_from_json` warns that an older single-table object was converted with a placeholder table name, save the converted `Metadata` object immediately with a deliberate table name.

## 9. Prepare sequential subsets

For long sequential data, define sequence metadata first and then subset sequences:

```python
from sdv.metadata import Metadata
from sdv.utils import get_random_sequence_subset

metadata = Metadata.detect_from_dataframe(data=events, table_name='events')
metadata.set_sequence_key('session_id')
metadata.set_sequence_index('event_time')
metadata.validate_table(events, table_name='events')

subset = get_random_sequence_subset(
    data=events,
    metadata=metadata,
    num_sequences=100,
    max_sequence_length=50,
    long_sequence_subsampling_method='first_rows',
)
```

Use the sequential synthesis sub-skill for `PARSynthesizer` modeling after this prep step.

## 10. Inspect SDV logs

```python
from sdv.logging.utils import load_logfile_dataframe

logs = load_logfile_dataframe('sdv_logs.csv')
fit_events = logs[logs['EVENT'] == 'Fit']
```

Use log inspection for provenance, fit/sample event checks, and debugging. Use the modeling sub-skills for synthesizer behavior and the evaluation sub-skill for quality reports.
