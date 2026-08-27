# Troubleshooting

This reference focuses on validation and permission problems for datasets, metadata tables, dimensions, SQLLab, and ETL pipelines.

## Permission and ownership errors

- `Not authorized to download dataset` — the dataset owner list does not contain the current user and the record is not public (`*`).
- `no permission` during dataset backup — the current user cannot edit that dataset.
- `only creator can edit/delete` or `只有创建者或管理员可修改` — the record is protected by creator/admin checks.
- `no perms to run pipeline` — the ETL pipeline project is not joined by the current user.
- SQLLab requests are always user-owned; if the task record is missing, verify the username and the selected engine scope.

## Dataset issues

- Dataset paths are stored as newline-separated entries, not a single comma-separated path.
- Missing local files are dropped when the dataset is saved.
- `path_html` only links files that exist under the platform’s mounted workspace mapping.
- `preview()` returns a placeholder row; do not expect a real sample unless a dedicated preview handler is added later.
- Partition downloads depend on the `segment` JSON map being present and keyed by the requested partition.

## Metadata and dimension issues

- `数据库连接串地址无法访问` or `测试数据库连通性失败` — the remote database is unreachable or the URI shape is invalid.
- `csv首行header与数据库字段不对应` — the upload header does not match the remote model fields.
- `不识别的csv文件编码格式，请转为utf-8编码格式` — re-encode the file to UTF-8 or GBK.
- `检测到唯一性字段重复` — the dimension upload hit a unique-column conflict.
- `更新远程表` / `创建新表成功` failures — confirm that the remote schema matches the `columns` JSON and that the connection uses MySQL or PostgreSQL, which are the only supported form-view URIs.
- If a dimension schema changes, the cached generated model may need to be rebuilt by refreshing the view instance.

## SQLLab issues

- `添加任务参数缺失` — the request is missing `engine_arg1`, `engine_arg2`, or `sql`.
- `引擎未实现` — the engine name is not one of the approved engine ids.
- `任务数据库记录不存在` — the task id is invalid or the row was removed.
- `查询sql必须包含limit` — add a `LIMIT` clause before submission.
- `返回值异常，检查引擎实现，需包含...` — the engine adapter returned the wrong key set.
- `暂未实现远程数据库kill操作` — the stop action is metadata-only.
- If the URI looks right but the request still fails, use `scripts/validate_sqllab_request.py` before trying a real submission.

## ETL pipeline issues

- `只有创建者或管理员可修改` — the user is not the creator or admin.
- If a node disappears from the saved graph, the save path removed an upstream or task reference that no longer exists in the graph.
- If a copied pipeline still collides with existing task names, re-run the copy flow so the task-name remapping can regenerate unique suffixes.
- If the remote scheduler page is wrong, check the workflow adapter name (`airflow`, `azkaban`, or `dolphinscheduler`) and its host URL.
- If the task catalog looks incomplete, verify the adapter-specific template list instead of looking for general Argo details here.

## Data import/export issues

- `job-template/job/dataset` expects a dataset name, version, optional partition, and a save directory.
- `job-template/job/datax` expects either a raw DataX JSON file or the form-based CSV export fields.
- DataX export problems are usually path or column mismatches, not cluster issues.
- If you are troubleshooting generic pipeline graph mechanics or Argo workflow generation, route that work to `../pipelines-and-job-templates/`.

## Good first checks

1. Validate the SQLLab request with the bundled script.
2. Inspect the owner, public, and status fields before assuming a permission bug.
3. Confirm the URI template shape before trying to connect to a database.
4. For ETL, confirm the workflow adapter and then inspect the seeded example JSON.
