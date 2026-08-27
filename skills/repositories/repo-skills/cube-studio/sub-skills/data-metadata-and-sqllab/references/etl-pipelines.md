# ETL pipelines

This reference covers the ETL pipeline catalog, task sync behavior, scheduler adapters, and bundled data-movement templates.

## Model schema

### `ETL_Pipeline`

| Field | Meaning |
| --- | --- |
| `name` | English pipeline name, normalized to lowercase and hyphenated on save |
| `describe` | Human-readable pipeline description |
| `project_id` / `project` | Owning project |
| `workflow` | Scheduler adapter: `airflow`, `azkaban`, or `dolphinscheduler` |
| `dag_json` | Task graph and node metadata |
| `config` | Pipeline-level configuration JSON |
| `expand` | Extra metadata |

### `ETL_Task`

| Field | Meaning |
| --- | --- |
| `etl_pipeline_id` | Owning pipeline |
| `name` | Node name in the DAG |
| `describe` | Node label |
| `template` | Selected task template |
| `task_args` | Per-node parameter JSON |
| `etl_task_id` | Remote scheduler task id |
| `expand` | Extra metadata |

## Adapter contract

Each scheduler adapter class follows the same shape.

- `AIRFLOW_ETL_PIPELINE`
- `AZKABAN_ETL_PIPELINE`
- `DOLPHINSCHEDULER_ETL_PIPELINE`

Shared responsibilities:

- `pipeline_config_ui` describes pipeline-level form fields.
- `pipeline_jump_button()` points users to the remote scheduler UI.
- `pipeline_run_button()` points users back to the CubeStudio submit action.
- `submit_pipeline()` returns the remote submission redirect URL.
- `delete_pipeline()` is where remote cleanup would live.
- `all_template` describes the data-movement and compute task catalog.

Example scheduler hosts:

- Airflow: `http://airflow.oa.com`
- Azkaban: `http://azkaban.oa.com`
- DolphinScheduler: `http://dolphinscheduler.oa.com`

## Lifecycle in CubeStudio

### Editing and sync

- `pipeline_config/<id>` merges incoming `config` and `dag_json` updates.
- Missing upstream nodes are removed from the saved graph.
- Every node gets a `task_id` if one is missing.
- `fix_pipeline_task()` keeps the `ETL_Task` rows in sync with the current graph.

### Submission and deletion

- `submit_etl_pipeline/<id>` loads the adapter for the selected workflow and calls `submit_pipeline()`.
- `pre_delete()` loads the same adapter and calls `delete_pipeline()` before removing local task rows.
- `copy_pipeline()` clones the pipeline and remaps task names and upstream references so the copy stays unique.

### UI routing

- `web/<id>` redirects into the front-end ETL editor (`visonPlus`) rather than the raw scheduler UI.
- `template_list/<id>` returns the adapter’s template catalog, with created/changed metadata filled in for the UI.

## Data-movement templates

The built-in template catalog focuses on data import/export and common data processing tasks.

Common groups include:

- binding tasks
- import/export
- data compute
- script execution

Common examples include:

- `cos导入hdfs`
- `hdfs入库至hive`
- `SQL`
- `SparkScala`
- `pyspark`
- `hive出库至hdfs`
- `hdfs导入cos`

These examples are also reflected in `myapp/init/init-etl-pipeline.json`, which seeds a `dau` pipeline example.

## Seed catalogs

- `myapp/init/init-project.json` seeds organization groups and job-template group labels.
- `myapp/init/init-etl-pipeline.json` seeds an example ETL pipeline and its DAG graph.

## Boundary note

This sub-skill covers scheduler adapters only at the data-pipeline contract level.

- General Argo workflow mechanics belong in the pipeline sub-skill.
- Do not treat this reference as a cluster-deployment guide.
