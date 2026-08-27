# Data workflows

This reference covers the data catalog objects owned by this sub-skill: datasets, metadata tables, metric catalogs, and dimension tables.

## Dataset records

`Dataset` is the user-facing data catalog entry.

### Important fields

| Area | Fields / behavior |
| --- | --- |
| Identity | `name`, `label`, `describe`, `version`, `subdataset`, `split`, `segment`, `doc` |
| Provenance | `source_type`, `source`, `industry`, `field`, `usage`, `research`, `years`, `owner` |
| Storage | `storage_class`, `file_type`, `status`, `url`, `path`, `download_url`, `storage_size`, `entries_num`, `duration`, `price`, `secret` |
| Content hints | `info`, `features`, `metric_info`, `icon` |
| Access | `owner` defaults to `<current-user>,*` for visible uploads; `*` means public visibility |

### Runtime behavior

- `path` and `download_url` are newline-separated lists.
- `path_html` turns mounted `/mnt/...` paths into clickable `/static/...` links when the file exists in the platform workspace mapping.
- `download_dataset` checks dataset ownership before exposing URLs.
- `segment` is a JSON map of partition names to file lists and is used when a partition is requested.
- `pre_list_res` groups older dataset versions under the newest record so the UI shows a version tree.
- `preview` is a UI-facing placeholder response; it wires the preview route but does not extract a real sample automatically.
- `save_store` starts the backup flow that copies an external dataset into the local store.

### Validation notes

- Missing local files in `path` are dropped during save.
- Invalid `features` JSON is normalized to a pretty-printed JSON object.
- The dataset form expects newline-separated URLs and paths rather than a single comma-separated string.

## Metadata tables

`Metadata_table` is the warehouse catalog entry for database tables.

### Main semantics

- `node_id` is auto-derived as `db::table`.
- `app`, `db`, `table`, `describe`, and `field` identify the business catalog entry.
- `warehouse_level`, `security_level`, `value_score`, and `ttl` describe governance and retention.
- `storage_cost`, `storage_size`, `visits_seven`, `visits_thirty`, `visits_sixty`, and `recent_visit` track cost and usage.
- `create_table_ddl`, `col_info`, `partition_update_mode`, `is_privilege`, and `data_source` capture table-management details.

### UI / API behavior

- `pre_add` sets `owner` to the current user, fills `node_id`, and records `creator`.
- `import_data` and `download_data` are enabled.
- `pre_upload` normalizes missing `recent_visit` values.
- `pre_list_res` rounds `storage_cost` for display.

## Metric catalog

`Metadata_metric` stores business metrics.

### Main semantics

- `app`, `name`, `label`, `describe`, and `caliber` describe the metric.
- `metric_type` distinguishes atomic and derived metrics.
- `metric_level`, `metric_dim`, and `metric_data_type` classify importance and reporting cadence.
- `metric_responsible`, `status`, `task_id`, `public`, `remark`, and `expand` control ownership and lifecycle.

### Validation notes

- `remark` is stored as JSON and rendered as a structured list of notes.
- The list view is filtered to public metrics or metrics whose responsible user contains the current username.
- `clone()` copies the core metadata fields for reuse in new metric definitions.

## Dimension tables

`Dimension_table` defines remote dimension-table metadata and the connection string used to reach the remote database.

### Main semantics

- `sqllchemy_uri` accepts only MySQL or PostgreSQL connection strings in the form view.
- `table_name`, `label`, `describe`, `app`, `owner`, and `columns` define the remote table contract.
- `columns` is a JSON map keyed by column name.
- The supported column metadata fields are `name`, `describe`, `column_type`, `unique`, `nullable`, `primary_key`, and `choices`.

### Runtime behavior

- `pre_add` auto-creates an `id` primary key when none is provided.
- `pre_add` also normalizes ownership and prevents custom primary keys from leaking into the default URI path.
- `post_add` tests database connectivity and clears the URI if the remote database is unreachable.
- `table_html` only renders a remote-table link when the current user has visibility.
- `operate_html` only exposes the remote-table refresh action to admins or explicit owners.
- `create_external_table` manages PostgreSQL and MySQL schema creation or column additions.
- `external()` renders a Hive DDL string derived from the current schema.

### Remote dimension API

`Dimension_remote_table` builds a dynamic model class from the `columns` JSON and exposes CRUD, upload, download-template, download, copy-row, and bulk-action endpoints.

- `upload()` accepts CSV, XLS, or XLSX files.
- Column values are cast to integers or floats when the metadata says so.
- Unique-column checks run before inserts.
- `download_template()` and `download()` are inherited from the generated REST view.

## Data import/export templates

This sub-skill also covers the repo’s bundled data movement templates.

- `job-template/job/dataset` downloads datasets from the current platform, Hugging Face, or ModelScope.
- `job-template/job/datax` supports both raw DataX JSON jobs and the form-based CSV export helper.
- Dataset downloads use `--src_type`, `--name`, `--version`, `--partition`, and `--save_dir`.
- The form-based DataX exporter uses `--db_type`, `--host`, `--database`, `--table`, `--columns`, and `--save_path`.
- These templates are the right place for data transfer recipes; general pipeline graph mechanics still belong to the pipeline sub-skill.
