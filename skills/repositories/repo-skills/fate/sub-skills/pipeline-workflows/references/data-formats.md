# Pipeline data formats, table names, namespaces, and roles

This reference summarizes the FATE example-data conventions used by service-backed Pipeline workflows and upload config YAML files. It is intentionally local and safe: it describes what to send to FateFlow, but does not contact a service.

## Table and namespace conventions

The example data documentation uses these conventions:

- Uploaded tables commonly use namespace `experiment`.
- Table `name` / `table_name` usually matches the data file stem: `breast_hetero_guest.csv` becomes `breast_hetero_guest`.
- Dataset names follow the guideline:

```text
{content}_{mode}_{size}_{role}_{role_index}
```

Where:

- `content`: short dataset/content label, e.g. `breast`, `default_credit`, `vehicle_scale`.
- `mode`: data partitioning, usually `homo` or `hetero`; some data names omit it.
- `size`: includes `mini` when the dataset is a truncated version.
- `role`: `guest` or `host`.
- `role_index`: optional host split index, starting at 1, when several hosts share portions of a dataset.

Examples used by pipeline recipes:

| Scenario | Guest table | Host table(s) | Namespace |
| --- | --- | --- | --- |
| Hetero breast binary | `breast_hetero_guest` | `breast_hetero_host` | `experiment` |
| Hetero breast mini | `breast_hetero_mini_guest` | `breast_hetero_mini_host` | `experiment` |
| Homo breast binary | `breast_homo_guest` | `breast_homo_host`; optional `breast_homo_test` | `experiment` |
| Default-credit hetero | `default_credit_hetero_guest` | `default_credit_hetero_host` | `experiment` |
| Multi-host motor hetero | `motor_hetero_guest` | `motor_hetero_host_1`, `motor_hetero_host_2` | `experiment` in examples where listed |
| Tag/value demos | `tag_value_1`, `tag_value_2`, `tag_value_3` from `tag_value_1000_140.csv` | local table operation | `experiment` |

Always copy the exact namespace and table names used during upload into `Reader.task_parameters(...)` during training or prediction.

## Party-role conventions

The example pipeline config uses string party ids. Common defaults are:

```yaml
parties:
  guest:
    - '9999'
  host:
    - '10000'
    - '9999'
  arbiter:
    - '10000'
```

Typical pipeline setup:

```python
pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000")
```

With an arbiter:

```python
pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000", arbiter="10000")
```

With multiple hosts:

```python
hosts = ["10000", "9999"]
pipeline = FateFlowPipeline().set_parties(guest="9999", host=hosts)
reader_0.hosts[[0, 1]].task_parameters(namespace="experiment", name="breast_hetero_host")
```

Upload config files also use role labels such as `guest_0`, `host_0`, and `host_1`. Treat these as upload/test-suite mapping labels, not replacements for the `set_parties(...)` ids used in a Pipeline DAG.

## Upload YAML structure

The example upload configs are YAML documents with a top-level `data` list. Each item describes one local file to transform into a FATE table.

Canonical shape:

```yaml
data:
  - file: examples/data/breast_hetero_guest.csv
    meta:
      delimiter: ","
      dtype: float64
      input_format: dense
      label_type: int64
      label_name: y
      match_id_name: id
      match_id_range: 0
      tag_value_delimiter: ":"
      tag_with_value: false
      weight_type: float64
    partitions: 4
    head: true
    extend_sid: true
    table_name: breast_hetero_guest
    namespace: experiment
    role: guest_0
```

Observed field names:

| Field | Required by validator | Meaning |
| --- | --- | --- |
| `data` | Yes | Top-level list of upload items. |
| `file` | Yes | Local file path to transform. Use an absolute path in runtime code when possible. |
| `meta` | Yes | Reader/table metadata passed to `transform_local_file_to_dataframe(...)`. |
| `table_name` | Yes | FATE table name; usually the file stem. In Python upload calls this is passed as `name=...`. |
| `namespace` | Yes | FATE namespace; examples use `experiment`. |
| `head` | Recommended | Whether the source file has a header row; examples use `true`. |
| `extend_sid` | Recommended | Whether to create/extend sample id from an existing id when only one id is present; examples often use `true`. |
| `partitions` / `partition` | Recommended | Partition count. Both spellings appear in example upload YAML; normalize them when generating configs. |
| `role` | Recommended | Upload/test-suite role label such as `guest_0`, `host_0`, `host_1`. |

## `meta` fields

Common dense CSV metadata:

| Meta field | Meaning and notes |
| --- | --- |
| `delimiter` | CSV delimiter. Examples use `","`. |
| `dtype` | Feature dtype, often `float64` or `float32`. |
| `input_format` | Examples use `dense`; tag-value data uses tag/value-specific settings. |
| `label_name` | Label column name. Supervised guest tables usually set `y`; hosts usually omit labels. |
| `label_type` | Label dtype, often `int64`/`int32` for classification or compatible type for regression. |
| `match_id_name` | Match-id column used by PSI. Examples use `id`. |
| `match_id_range` | Examples set `0`. |
| `sample_id_name` | Used by SID-specific upload when a sample-id column already exists. |
| `tag_with_value` | Whether tag data includes values. Examples set `false` for dense CSV. |
| `tag_value_delimiter` | Separator for tag-value inputs; examples use `":"`. |
| `weight_type` | Optional row-weight dtype. |

FATE 2.x note from PSI documentation: uploaded data should have both sample id and match id. If the original file only has one id column, use `extend_sid=True`; if it already has a sample id column, set `sample_id_name` and use `extend_sid=False` like the SID upload example.

## Reader mapping from uploaded tables

Reader table names must match the upload exactly:

```python
reader_0 = Reader("reader_0")
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")
```

For homo examples, guest and host tables usually have the same feature schema but different rows:

```python
reader_0 = Reader("reader_0", runtime_parties=dict(guest="9999", host="10000"))
reader_0.guest.task_parameters(namespace="experiment", name="breast_homo_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_homo_host")
```

For hetero examples, guest and host tables have overlapping match ids but different feature columns. Add `PSI` before model components unless the component recipe explicitly avoids alignment.

## Data-format preflight checklist

Before running a service-backed pipeline:

1. Validate upload YAML structure locally with `scripts/validate_upload_config.py`.
2. Confirm every runtime `Reader` table `(namespace, name)` matches an uploaded table.
3. Confirm guest table has labels for supervised training; host tables normally do not.
4. Confirm `match_id_name` is present for hetero PSI workflows.
5. Confirm `extend_sid`/`sample_id_name` choice matches the source file id columns.
6. Confirm multi-host pipelines have enough host party ids for every `reader.hosts[...]` index.
7. Confirm prediction data uses the same schema and id conventions expected by the deployed components.
