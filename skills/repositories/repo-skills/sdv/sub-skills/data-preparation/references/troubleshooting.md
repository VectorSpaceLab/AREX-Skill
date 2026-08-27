# SDV data-preparation troubleshooting

Use this when a data-loading, metadata, local I/O, utility, or logging step fails. For method signatures, see [API reference](api-reference.md); for recipes, see [Workflows](workflows.md).

## Demo dataset download

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: 'modality' must be in ['single_table', 'multi_table', 'sequential']` | The modality string is not one of the supported values. | Use exactly `single_table`, `multi_table`, or `sequential`. |
| Download/listing raises a demo resource not found error mentioning bucket, dataset, or modality. | Network/S3 access failed, the dataset name is wrong, the bucket is wrong, or the demo resource is missing. | First call `get_available_demos(modality)` for the correct modality. Check spelling and network access. Retry later if S3/network is transient. |
| Error says private buckets or DataCebo credentials are only supported in SDV Enterprise. | Community SDV rejects custom bucket names and credentials. | Use the default public bucket without credentials, or switch to an Enterprise-capable environment before retrying. |
| `Folder '...' already exists` from `download_demo(..., output_folder_name=...)`. | Demo download refuses to write into an existing folder. | Choose a new folder name. If the goal is to read an existing local copy, use `load_csvs` or `CSVHandler.read` instead. |
| Warning says files were skipped from `data.zip`, followed by no CSV files found. | The archive contains non-CSV files or no readable CSV files. | Pick a different demo dataset, retry the download, or load the local files manually if you already have the CSVs. |
| `get_source` or `get_readme` returns `None` with a warning. | The demo dataset has no text resource of that type. | Treat it as missing optional documentation; do not block data prep unless the source/citation text is required. |

## Local CSV and Excel I/O

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `The folder '...' cannot be found` or no CSV files exist. | `load_csvs` points at the wrong folder or the files do not end in `.csv`. | Verify the folder and file suffixes. For recursive CSV detection, use `MultiTableMetadata.detect_from_csvs`; for actual data loading, collect the intended CSV files explicitly. |
| Warning about incompatible files in a CSV folder. | `load_csvs` found non-CSV files. | Usually safe to ignore. Move metadata or README files elsewhere if the warning is distracting. |
| Zip codes or IDs lose leading zeroes after CSV read. | Pandas inferred numeric dtype. | Prefer `CSVHandler.read(..., keep_leading_zeros=True)` or pass pandas `dtype` settings in `read_csv_parameters`. |
| `CSVHandler` rejects `filepath_or_buffer` or `path_or_buf`. | The handler reads a folder and optional file list, not a single pandas path argument. | Pass `folder_name` and `file_names` to `CSVHandler.read`; place pandas options such as `sep`, `encoding`, or `nrows` in `read_csv_parameters`. |
| `FileNotFoundError` names missing CSV files. | The `file_names` list includes files absent from the folder. | Update `file_names` to existing filenames including `.csv`, or omit it to read all CSV files in the folder. |
| `save_csvs` or `CSVHandler.write(mode='x')` fails because target files already exist. | Default write mode protects existing files. | Use a new folder, pass a `suffix`/`file_name_suffix`, remove old files, or intentionally overwrite with `CSVHandler.write(..., mode='w')`. |
| CSV append produces duplicated header-looking rows. | Pandas CSV append writes the DataFrame as-is with default header behavior unless overridden. | For append workflows, pass suitable `to_csv_parameters` such as `header=False` when appending rows to existing files. |
| Excel read/write fails with missing engine errors. | Required pandas Excel optional dependency is unavailable for the workbook format. | Install the appropriate pandas Excel backend in the active runtime or convert the data to CSV. |
| `ExcelHandler.read` says `sheet_names` must be `None` or a list of strings. | A single string was passed. | Use `sheet_names=['Sheet1']` or omit `sheet_names` to read every sheet. |
| Excel append overwrites or unexpectedly merges sheets. | `ExcelHandler.write(mode='a')` reads the workbook, merges same-named sheets row-wise when no suffix is given, and rewrites the workbook. | Use `sheet_name_suffix` to create new sheets instead of row-wise append, or write to a new workbook with `mode='w'`. |

## Metadata validation and editing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `The provided dictionary must contain only pandas DataFrame objects.` | Multi-table detection was given non-DataFrame values. | Build `dict[str, pandas.DataFrame]` before calling `Metadata.detect_from_dataframes`. |
| Metadata already exists when detecting. | Legacy `SingleTableMetadata` or `MultiTableMetadata` detection mutates an empty instance and refuses to re-detect into a populated one. | Create a fresh metadata object, or use classmethod `Metadata.detect_from_dataframe(s)` to return a new unified object. |
| `Metadata contains more than one table, please specify the table_name`. | A unified metadata method could not infer which table to operate on. | Pass `table_name='...'` to column/key validation and update methods. |
| Unknown table or column errors. | Metadata edit refers to a name not present in metadata. | Inspect `metadata.to_dict()` or `metadata.tables.keys()` and correct table/column names before retrying. |
| Invalid sdtype or invalid sdtype-specific kwargs. | Metadata column configuration is inconsistent. | Use supported sdtypes and parameters: `numerical` with `computer_representation`, `datetime` with `datetime_format`, `categorical` with either `order` or `order_by`, `id` with optional `regex_format`, and PII/Faker sdtypes with `pii` where applicable. |
| Primary/alternate/sequence key validation fails. | Key columns are missing, have wrong sdtype, repeat, contain null values, or overlap with incompatible special columns. | Set key columns to `id` or a valid PII/Faker sdtype, remove nulls, ensure uniqueness for primary/alternate keys, and keep sequence key/index distinct. |
| Data validation reports columns missing from metadata or metadata columns missing from data. | Metadata and DataFrame columns are not the same set. | Add/remove/update metadata columns or adjust the DataFrame columns. Re-run `metadata.validate_data(data_dict)` for multi-table data or `metadata.validate_table(dataframe, table_name=...)` for one table. |
| Warning says metadata lists columns in a different order than data. | Same columns exist but order differs. | Usually non-fatal. If output column order matters, rebuild or save metadata in the same order as the data columns. |
| Warning says no `datetime_format` is present for object datetime columns. | Metadata has `sdtype='datetime'` but no explicit parse format. | Add `metadata.update_column('date_col', sdtype='datetime', datetime_format='...')`. |
| Integer primary key with regex that allows leading zeroes is invalid. | Integer storage cannot represent leading-zero IDs that the regex permits. | Load the key column as string or change the regex/metadata so the stored dtype and regex agree. |
| `metadata.validate()` fails on relationships. | Parent/child table names, key names, key lengths, sdtypes, or relationship graph are invalid. | Verify parent primary key and child foreign key exist, have matching sdtypes and equal composite-key lengths, and do not create circular or disjoint relationships. |

## Referential integrity and `drop_unknown_references`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `validate_data` reports foreign key columns contain unknown references and suggests `drop_unknown_references`. | Child rows contain foreign-key values absent from parent primary keys. | If dropping those rows is acceptable, run `drop_unknown_references(data, metadata, drop_missing_values=False)` and validate the returned data. If not, repair parent or child keys manually. |
| Null foreign keys remain after cleaning. | `drop_unknown_references` defaults to keeping null foreign keys. | Set `drop_missing_values=True` if null foreign-key rows should be removed. |
| Error says all references in a table are unknown and must be dropped. | Cleaning would remove every row from a child table. | Do not blindly drop. Check relationship direction, key sdtypes, and whether the parent table is missing the expected keys. |
| Output summary shows unexpected invalid-row counts. | A relationship was inferred incorrectly or keys have mismatched types, whitespace, or formatting. | Inspect relationship definitions and normalize key columns before cleaning. Re-run `metadata.validate_data`. |

## Graphviz and metadata visualization

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Metadata `visualize` returns a graph object but saving to file fails. | Python `graphviz` package is present, but the Graphviz executable is missing or not on `PATH`. | Install the Graphviz system executable in the runtime, or call `visualize(..., output_filepath=None)` and render elsewhere. |
| `visualize` rejects `show_table_details`. | Invalid option. | Use `'full'`, `'summarized'`, or `None` for unified/multi-table metadata. For legacy single-table metadata use `'full'` or `'summarized'`. |
| Boolean `show_table_details` triggers a deprecation warning. | Older calls used `True`/`False`. | Replace `True` with `'full'` and `False` with `None`. |
| Relationship labels make the graph too cluttered. | Multi-table graph contains many relationships or composite keys. | Use `show_relationship_labels=False` or `show_table_details='summarized'`. |

## Metadata save, load, anonymize, and upgrade

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `save_to_json(..., mode='write')` refuses to overwrite. | Safe write mode protects existing metadata files. | Choose a new filename or use `mode='overwrite'` intentionally. |
| Loading metadata warns about an older single-table object and a placeholder table name. | `Metadata.load_from_json` converted legacy single-table metadata into unified metadata. | Reload with `single_table_name='desired_name'` if needed, then save the converted `Metadata` object. |
| `upgrade_metadata` succeeds but warns that converted metadata is not valid. | Legacy metadata contained stale fields, unsupported constraints, or invalid keys. | Inspect the warning, edit the returned metadata object, run `validate()`, then save. Route constraint rewrites to the constraints sub-skill. |
| Anonymized metadata does not match original column/table names. | This is expected; `anonymize()` obfuscates names while preserving structure and sdtypes. | Keep the original metadata separately if name mapping is needed. Do not use anonymized metadata with non-anonymized data unless names have been mapped consistently. |

## Saved synthesizers and version/device warnings

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `load_synthesizer` warns about SDV version mismatch. | The saved synthesizer was fit with a different SDV or SDV Enterprise version. | Prefer refitting with the current version when possible. If only loading for diagnostics, record the warning and avoid making unsupported compatibility claims. |
| `load_synthesizer` errors that a GPU-created synthesizer is loaded on a CPU-only machine. | Serialized torch state was created on CUDA and current runtime cannot deserialize it through SDV's loader. | Sample/load on a compatible GPU-enabled runtime, or recreate and save the synthesizer on CPU if the model supports that workflow. Route follow-up sampling to the appropriate modeling sub-skill. |
| Loading succeeds but task asks to sample or refit. | Loading is only a prep/diagnostic step here. | Route sampling, refitting, condition handling, and model-specific save/load behavior to the relevant modeling sub-skill. |

## Logging helpers

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_sdv_logger_config()` returns `{}`. | SDV cannot create/read its per-user logging config due to permission or read-only filesystem restrictions. | Continue without SDV file logging, or choose a runtime with writable user data storage if logs are required. |
| `load_logfile_dataframe` columns look shifted or malformed. | The logfile is not the SDV CSV logger format expected by the helper. | Verify the file is an SDV log CSV with events such as `Instance`, `Fit`, and `Sample`; otherwise parse it manually. |
| Logging is too noisy during local prep. | Single-table logger has active handlers. | Use `with disable_single_table_logger():` around the noisy block when logs are not needed. |

## Low-level data-processing internals

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DataProcessor` transform/reverse-transform fails before fitting. | The processor was not prepared or fit. | Prefer using synthesizer APIs. If debugging internals, call `prepare_for_fitting(data)`/`fit(data)` before `transform` or `reverse_transform`. |
| Locale-related anonymization errors. | A PII sdtype is not supported by the selected locale. | Add `en_US` or choose locales compatible with the requested PII sdtype. |
| Low-level processing behavior differs from synthesizer behavior. | Synthesizers configure processors, constraints, transformers, and key generation. | Treat `DataProcessor` as internal support. Use metadata and synthesizer public APIs for normal workflows. |
