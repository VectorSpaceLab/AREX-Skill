# SQLLab and engines

This reference covers the SQLLab request record, engine selection, lifecycle, and result handling.

## Query record

`Sqllab_Query` stores each request.

| Field group | Fields |
| --- | --- |
| Timing | `submit_time`, `start_time`, `end_time` |
| Connection | `engine_arg1`, `engine_arg2`, `engine` |
| SQL | `qsql` |
| Execution state | `stage`, `status`, `task_id`, `err_msg` |
| Result routing | `log_url`, `ui_url`, `result_url`, `result_line_num` |
| Ownership | `username` |
| Misc | `deli`, `expand` |

### Lifecycle

- `stage`: `START` → `execute` → `end`
- `status`: `INIT` → `running` → `success` or `failure`

The API uses the record as the source of truth for status polling and result download.

## Supported engines

The UI/API accepts these engine names:

| Engine | Documented URI template |
| --- | --- |
| `mysql` | `mysql+pymysql://$username:$password@$host:3306/$database` |
| `postgres` | `postgresql+psycopg2://$username:$password@$host:5432/$database` |
| `presto` | `presto://$username:$password@$host:8080/$catalog/$schema` |
| `clickhouse` | `clickhouse+native://$username:$password@$host:9000/$database` |
| `hive` | `hive://$host:10000/default?auth=NOSASL` |
| `impala` | `impala://host:port/database` |

Notes:

- The shared `Base_Impl` adapter is registered for all six names.
- The current executor only performs real SQL reads for `mysql` and `postgres`.
- For the other engine names, treat the URI template and request shape as the primary contract unless a dedicated adapter has been added elsewhere.

## Request flow

`Sqllab_Query_View` exposes the following endpoints under `route_base = /idex`:

- `GET/POST /config` — returns the engine selector and recent successful connection templates.
- `POST /submit_task` — creates the query record and dispatches the task.
- `GET /look/<task_id>` — returns task state.
- `GET /result/<task_id>` — returns the result table.
- `GET /download_url/<task_id>` — returns a downloadable CSV URL.
- `GET /stop/<task_id>` — currently only returns a not-implemented message for remote kill.

## Request validation rules

Use the bundled validator to catch shape errors before any runtime submission.

- `engine_arg1` must be one of the allowed engine names.
- `engine_arg2` must match the documented URI shape for that engine.
- `sql` must be present and non-empty.
- The current executor expects a `LIMIT` clause in the SQL text.
- The request must be a JSON object or a JSON object nested under `request`.

## Result handling

`Base_Impl` applies the shared lifecycle.

- `submit_task()` creates the task record and uses Celery for asynchronous execution.
- `check_task_status()` returns `stage`, `state`, `err_msg`, `spark_log_url`, and `spark_ui_url`.
- `get_result()` reads the saved CSV from `/data/k8s/kubeflow/global/sqllab/result/<task_id>.csv` and returns a table-like list.
- `download_url()` rewrites the saved CSV with the requested separator and returns a static URL under `/static/global/sqllab/result/`.
- `stop()` only reports that remote database kill is not implemented.

## Configuration hooks

- `conf['SQLLAB']` can replace the default engine-select payload.
- `conf['SQLLAB_ARGS']` can inject extra request fields before submission.
- Recent successful URI choices are gathered per user for the last 30 days.

## Common failure modes

- `添加任务参数缺失` — missing request keys.
- `引擎未实现` — engine name not in the approved set.
- `任务数据库记录不存在` — the task id is invalid or the row was deleted.
- `查询sql必须包含limit` — the SQL does not satisfy the current executor contract.
- `返回值异常，检查引擎实现，需包含...` — an adapter returned the wrong key set.
