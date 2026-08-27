# SDV data-preparation API reference

This reference covers public SDV APIs that prepare data and metadata before modeling. Prefer the unified `Metadata` API unless a legacy or downstream object specifically needs `SingleTableMetadata` or `MultiTableMetadata`.

## Imports

```python
from sdv.datasets.demo import (
    download_demo, get_available_demos, get_readme, get_source, save_resource,
)
from sdv.datasets.local import load_csvs, save_csvs
from sdv.io.local import BaseLocalHandler, CSVHandler, ExcelHandler
from sdv.metadata import Metadata, SingleTableMetadata, MultiTableMetadata
from sdv.utils import drop_unknown_references, get_random_sequence_subset, load_synthesizer
from sdv.logging.utils import (
    get_sdv_logger_config, disable_single_table_logger, load_logfile_dataframe,
)
```

## Demo datasets

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `download_demo` | `download_demo(modality, dataset_name, output_folder_name=None, s3_bucket_name='sdv-datasets-public', credentials=None)` | Download and parse a demo dataset plus metadata. | `modality` must be `'single_table'`, `'multi_table'`, or `'sequential'`. Single-table and sequential demos return `(DataFrame, Metadata)`; multi-table demos return `(dict[str, DataFrame], Metadata)`. If `output_folder_name` is provided, it must not already exist. Community SDV only supports the public bucket without credentials. |
| `get_available_demos` | `get_available_demos(modality, s3_bucket_name='sdv-datasets-public', credentials=None)` | List available demo datasets for one modality. | Returns a DataFrame with dataset names plus available size/table-count columns. |
| `get_source` | `get_source(modality, dataset_name, output_filepath=None, s3_bucket_name='sdv-datasets-public', credentials=None)` | Read or save dataset source/citation text. | `output_filepath`, if given, should end in `.txt`. Missing source text emits a warning and returns `None`. |
| `get_readme` | `get_readme(modality, dataset_name, output_filepath=None, s3_bucket_name='sdv-datasets-public', credentials=None)` | Read or save dataset README text. | Same text-file behavior as `get_source`. |
| `save_resource` | `save_resource(modality, dataset_name, resource_filepath=None, output_filepath=None, s3_bucket_name='sdv-datasets-public', credentials=None, resource_filename=None)` | Save a named resource file from a demo dataset. | `resource_filepath` is required, must be relative to the dataset, and replaces deprecated `resource_filename`. `output_filepath` must not already exist. |

## Local folder helpers

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `load_csvs` | `load_csvs(folder_name, read_csv_parameters=None)` | Read every top-level `.csv` file in a folder into a table-name dictionary. | Table names are filename stems. Non-CSV files are ignored with a warning. Raises if the folder is missing or contains no CSV files. |
| `save_csvs` | `save_csvs(data, folder_name, suffix=None, to_csv_parameters=None)` | Save `dict[str, DataFrame]` to CSV files. | Validates the input is a dict of DataFrames. Creates the folder if missing. Raises `FileExistsError` if target files already exist; use `suffix` or remove files first. |
| `BaseLocalHandler.create_metadata` | `handler.create_metadata(data)` | Detect unified `Metadata` for a dict of DataFrames. | Equivalent to `Metadata.detect_from_dataframes(data)`. |

## `CSVHandler`

`CSVHandler` is the more configurable CSV local I/O interface.

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| Constructor | `CSVHandler()` | Create a handler. | It does not store delimiter/encoding state; pass read/write parameters per call. |
| `read` | `read(folder_name, file_names=None, read_csv_parameters=None, keep_leading_zeros=True)` | Read selected or all CSV files from a folder. | Default read parameters include `parse_dates=False`, `low_memory=False`, and bad-line warnings. `keep_leading_zeros=True` reloads sampled numeric-looking columns as strings when values such as zip codes contain leading zeros. `filepath_or_buffer` and `path_or_buf` are unsupported because the handler reads multiple files. |
| `write` | `write(synthetic_data, folder_name, file_name_suffix=None, mode='x', to_csv_parameters=None)` | Write a dict of DataFrames to CSV. | Default `to_csv` parameters include `index=False`. `mode='x'` raises if a file exists; `mode='w'` overwrites; `mode='a'` appends rows using pandas CSV append semantics. |

## `ExcelHandler`

`ExcelHandler` requires the Excel engines expected by pandas for the file type.

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| Constructor | `ExcelHandler(decimal='.', float_format=None)` | Create a workbook handler. | `decimal` is used for reading; `float_format` is used for writing. |
| `read` | `read(filepath, sheet_names=None)` | Read all sheets or a selected list of sheets into a dict. | `sheet_names` must be `None` or a list of strings. Dates are not auto-parsed. |
| `write` | `write(synthetic_data, filepath, sheet_name_suffix=None, mode='w')` | Write table DataFrames as workbook sheets. | `mode='w'` writes a new workbook. `mode='a'` first reads existing sheets, then either appends rows to same-named sheets or creates suffixed sheets. |

## Unified metadata API

`Metadata` represents single-table, multi-table, and sequential metadata using spec version `V1`.

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| Constructor | `Metadata()` | Start an empty unified metadata object. | Use mutating methods or classmethod detection to populate it. |
| Detect single table | `Metadata.detect_from_dataframe(data, table_name='table', infer_sdtypes=True, infer_keys='primary_only', verbose=False)` | Return a new `Metadata` object for one DataFrame. | `infer_keys` may be `'primary_only'` or `None`. Column names are converted to strings. |
| Detect multi-table | `Metadata.detect_from_dataframes(data, infer_sdtypes=True, infer_keys='primary_and_foreign', foreign_key_inference_algorithm='column_name_match', verbose=False)` | Return a new `Metadata` object for a dict of DataFrames. | `infer_keys` may be `'primary_and_foreign'`, `'primary_only'`, or `None`. The only public foreign-key inference algorithm is `'column_name_match'`. |
| Load JSON | `Metadata.load_from_json(filepath, single_table_name=None)` | Load unified or compatible older metadata JSON. | Older single-table metadata is converted into unified metadata with a table name; save the converted object for future use. |
| Load dict | `Metadata.load_from_dict(metadata_dict, single_table_name=None)` | Build `Metadata` from a metadata dictionary. | A dict with `tables` is multi-table; otherwise it is interpreted as a single table. |
| Save JSON | `save_to_json(filepath, mode='write')` | Persist metadata. | `mode='write'` refuses to overwrite. Use `mode='overwrite'` only when intentional. |
| Validate metadata | `validate()` | Check internal metadata consistency. | Run before validating data or fitting. |
| Validate all data | `validate_data(data)` | Check a full multi-table dataset conforms to metadata. | For unified `Metadata`, `data` must be a dict of DataFrames keyed by table name; foreign keys must reference known parent keys. |
| Validate one table | `validate_table(data, table_name=None)` | Validate one DataFrame against unified metadata. | Use this after `Metadata.detect_from_dataframe(...)`; if metadata contains multiple tables, `table_name` is required. |
| Visualize | `visualize(show_table_details='full', show_relationship_labels=True, output_filepath=None)` | Return a `graphviz.Digraph` and optionally render it. | `show_table_details` accepts `'full'`, `'summarized'`, or `None` for multi-table metadata. Rendering to a file needs the Graphviz executable. |
| Anonymize | `anonymize()` | Return metadata with table/column names obfuscated. | Sdtypes and key structure are retained while names become generic. |
| Copy | `copy()` | Deep-copy metadata. | Useful before destructive edits. |

### Common metadata edit methods

For `Metadata`, `table_name` is optional when exactly one table exists and required when more than one table exists.

| Method | Use |
| --- | --- |
| `add_table(table_name)` / `remove_table(table_name)` | Manage tables. Removing a table also removes its relationships. |
| `add_column(column_name, table_name=None, **kwargs)` | Add a column and required `sdtype`. |
| `update_column(column_name, table_name=None, **kwargs)` | Replace one column's metadata. Include `sdtype` when changing sdtype-specific parameters. |
| `update_columns(column_names, table_name=None, **kwargs)` | Apply the same metadata to multiple columns. |
| `update_columns_metadata(column_metadata, table_name=None)` | Update multiple columns with per-column metadata dicts. |
| `remove_column(column_name, table_name=None)` | Remove a column and any related key/relationship references. |
| `set_primary_key(column_name, table_name=None)` / `remove_primary_key(table_name=None)` | Configure primary keys, including composite primary keys as lists. |
| `add_alternate_keys(column_names, table_name=None)` | Add alternate key columns. |
| `set_sequence_key(column_name, table_name=None)` / `set_sequence_index(column_name, table_name=None)` | Configure sequential metadata. The sequence index must be numerical or datetime. |
| `add_relationship(parent_table_name, child_table_name, parent_primary_key, child_foreign_key)` | Add a parent-child relationship. Primary and foreign key lengths and sdtypes must match. |
| `remove_relationship(parent_table_name, child_table_name)` | Remove all relationships from that parent to that child. |
| `add_column_relationship(relationship_type, column_names, table_name=None)` | Add supported multi-column relationships such as address or GPS. |
| `get_column_names(table_name=None, **kwargs)` | Filter columns by metadata fields such as `sdtype='id'` or `pii=True`. |
| `get_table_metadata(table_name=None)` | Return a single-table metadata view as unified `Metadata`. |

### Column metadata vocabulary

| `sdtype` | Key parameters | Notes |
| --- | --- | --- |
| `numerical` | `computer_representation` such as `Float`, `Float64`, `Int64`, `Int32`, `UInt64`, etc. | Invalid representations raise metadata errors. |
| `datetime` | `datetime_format` | Missing format for object-typed datetime data is a warning during data validation. |
| `categorical` | `order` or `order_by` | Do not set both. `order_by` accepts `alphabetical` or `numerical_value`. |
| `boolean` | none | Values must be booleans or missing. |
| `id` | `regex_format` | Keys must use `id` or another PII/Faker sdtype. Integer primary keys with regexes that allow leading zeroes can be invalid. |
| `unknown` or PII/Faker sdtypes | `pii` for unknown/PII cases | PII sdtypes support anonymized generation downstream. |

## Legacy metadata classes

Use these when a downstream legacy API asks for them or when upgrading older metadata.

| Class/API | Signature | Notes |
| --- | --- | --- |
| `SingleTableMetadata()` | constructor | Instance detection methods mutate the object and return `None`. |
| `SingleTableMetadata.detect_from_dataframe` | `detect_from_dataframe(data)` | Detect from a DataFrame. |
| `SingleTableMetadata.detect_from_csv` | `detect_from_csv(filepath, read_csv_parameters=None)` | Detect from one CSV file. |
| `SingleTableMetadata.validate_data` | `validate_data(data, sdtype_warnings=None)` | Validate a DataFrame. |
| `SingleTableMetadata.visualize` | `visualize(show_table_details='full', output_filepath=None)` | `show_table_details` is `'full'` or `'summarized'`. |
| `SingleTableMetadata.save_to_json` | `save_to_json(filepath, mode='write')` | `mode='overwrite'` allows replacement. |
| `SingleTableMetadata.load_from_json` | `load_from_json(filepath)` | Requires compatible metadata spec. |
| `SingleTableMetadata.upgrade_metadata` | `upgrade_metadata(filepath)` | Convert an older single-table metadata file; warnings may identify unsupported legacy constraints. |
| `MultiTableMetadata()` | constructor | Instance detection methods mutate the object and return `None`. |
| `MultiTableMetadata.detect_from_dataframes` | `detect_from_dataframes(data, verbose=False)` | Detect every table and infer column-name-matched relationships. |
| `MultiTableMetadata.detect_from_csvs` | `detect_from_csvs(folder_name, read_csv_parameters=None)` | Recursively detects CSV files under a folder. |
| `MultiTableMetadata.validate_data` | `validate_data(data)` | Validates every table and referential integrity. |
| `MultiTableMetadata.visualize` | `visualize(show_table_details='full', show_relationship_labels=True, output_filepath=None)` | Same visualization options as unified multi-table metadata. |
| `MultiTableMetadata.upgrade_metadata` | `upgrade_metadata(filepath)` | Convert older multi-table metadata files. |

## Preparation utilities

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `drop_unknown_references` | `drop_unknown_references(data, metadata, drop_missing_values=False, verbose=True)` | Drop child rows whose foreign keys do not appear in parent keys. | Calls `metadata.validate()` and `metadata.validate_data(data)` first. If data is already valid, returns the input data. If invalid, returns a pruned copy. With `drop_missing_values=True`, null foreign keys are also invalid. |
| `get_random_sequence_subset` | `get_random_sequence_subset(data, metadata, num_sequences, max_sequence_length=None, long_sequence_subsampling_method='first_rows')` | Sample a subset of sequences before fitting a sequential model. | Metadata must define `sequence_key`, and the key must be a data column. Long-sequence methods are `'first_rows'`, `'last_rows'`, and `'random'`. Set NumPy randomness outside the call if reproducibility matters. |
| `load_synthesizer` | `load_synthesizer(filepath)` | Safely load a saved synthesizer for diagnostics or routing to modeling. | Checks SDV version compatibility, logs a load event, and raises a clear error when a GPU-created synthesizer is loaded on CPU-only hardware. Route actual sampling to the modeling sub-skills. |

## Logging helpers

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `get_sdv_logger_config` | `get_sdv_logger_config()` | Return SDV logging configuration as a dict. | May return `{}` on read-only or permission-restricted systems. |
| `disable_single_table_logger` | `disable_single_table_logger()` | Context manager to temporarily remove single-table logger handlers. | Use around noisy prep/model calls when logs are not needed. |
| `load_logfile_dataframe` | `load_logfile_dataframe(logfile)` | Read an SDV log CSV into a DataFrame. | Columns are `LEVEL`, `EVENT`, `TIMESTAMP`, `SYNTHESIZER CLASS NAME`, `SYNTHESIZER ID`, `TOTAL NUMBER OF TABLES`, `TOTAL NUMBER OF ROWS`, and `TOTAL NUMBER OF COLUMNS`. |

## Low-level data-processing support

`sdv.data_processing.DataProcessor` is exposed but usually owned by synthesizers, not end-user data-prep workflows. Use it only when debugging transformations or extending SDV internals.

Key signatures: `DataProcessor(metadata, enforce_rounding=True, enforce_min_max_values=True, model_kwargs=None, table_name=None, locales=['en_US'], id_columns_use_old_behavior=None)`, `prepare_for_fitting(data)`, `fit(data)`, `transform(data, is_condition=False)`, `reverse_transform(data, reset_keys=False, conditions=None)`, `filter_valid(data)`, `generate_keys(num_rows, reset_keys=False)`, `update_transformers(column_name_to_transformer)`, `to_dict()`, `from_dict(metadata_dict, enforce_rounding=True, enforce_min_max_values=True)`, `to_json(filepath)`, and `from_json(filepath)`.

`DatetimeFormatter(datetime_format=None)` and `NumericalFormatter(enforce_rounding=False, enforce_min_max_values=False, computer_representation='Float')` provide lower-level format learning and formatting helpers, but metadata-driven synthesizers normally select them automatically.
