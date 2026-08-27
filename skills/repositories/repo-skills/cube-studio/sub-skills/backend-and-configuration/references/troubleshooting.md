# Backend and configuration troubleshooting

Use this when CubeStudio backend import, startup, auth, RBAC, Celery/watch, or
frontend proxy/build behavior fails. For cluster deployment failures, route to
`deploy-and-operate`; for domain workflows, route to the matching sibling
sub-skill.

## Fast static triage

Run the bundled read-only helper against the checkout you are inspecting:

```bash
python scripts/inspect_cube_studio_structure.py /path/to/cube-studio
```

If it reports missing overlays, empty placeholders, missing appbuilder
registrations, malformed package JSON, or proxy target surprises, fix those
before attempting live imports or service starts.

## Import and configuration failures

| Symptom | Likely cause | Safe checks | Resolution |
| --- | --- | --- | --- |
| `ImportError` or `cannot import name 'Myauthdbview' from 'myapp.project'` | Runtime `project.py` overlay was not mounted/importable; source placeholder is empty | Check `myapp/project.py` size and overlay `project.py` existence; helper reports both | Mount/copy the Docker or Kubernetes `project.py` overlay, or provide a compatible inspection module defining `Myauthdbview` and hook functions. |
| Config values such as `APP_NAME`, `SQLALCHEMY_DATABASE_URI`, namespaces, or `CLUSTERS` are missing | Runtime `config.py` overlay was not mounted/importable | Check `myapp/config.py` size and overlay `config.py` existence | Use the correct overlay path for Docker/Kubernetes; do not edit only the empty placeholder. |
| `KeyError` for `CLUSTERS[ENVIRONMENT]`, watcher logs `no cluster`, or wrong service domain | `ENVIRONMENT` lowercased value does not match `CLUSTERS` key | Compare `ENVIRONMENT` with config keys; default `DEV` becomes `dev` | Set `ENVIRONMENT` consistently or add the cluster entry to the overlay. |
| SQLite inspection fails with MySQL pool arguments | Shipped overlay has MySQL-tuned `SQLALCHEMY_POOL_SIZE`, recycle, max overflow | Inspect temporary config used for import | For private inspection, remove MySQL pool options or use a MySQL-compatible URI; live CubeStudio expects MySQL. |
| Flask 2.3 deprecation warning for `flask.Markup` | Several modules import `Markup` from Flask | Static grep can find imports | Non-fatal in the verified environment, but future fixes should import `Markup` from `markupsafe` consistently. |
| SQLAlchemy warning for `ab_user.active` column combination | `MyUser` extends FAB's user model and also declares `active` | Warning observed during overlay import | Usually non-fatal; avoid changing the user model casually and keep migrations/dependency versions aligned. |

## DB, migration, and init failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `create_db.py` does nothing | `MYSQL_SERVICE` is empty | Set a MySQL SQLAlchemy URI; this helper only creates the database when the variable is present. |
| DB connection refused during import/startup | MySQL not reachable or wrong credentials/charset | Validate `MYSQL_SERVICE`, network/service name, credentials, and that the MySQL service is ready before backend import. |
| `myapp db upgrade` fails | Overlay import failed, DB unreachable, or migration state mismatch | Fix overlay/import first; back up DB before repairing Alembic state. |
| `check_tables.py` exits and prints missing table names | Migration/init did not create all required FAB/CubeStudio tables | Re-run the documented order: create DB, `myapp db upgrade`, admin creation as needed, `myapp init`, then `check_tables.py`. Do not drop production DB without operator approval. |
| New view exists in source but menu/API permissions are missing | AppBuilder startup uses `update_perms=False` | Run `myapp init` in the runtime so `appbuilder.add_permissions(update_perms=True)` refreshes permissions. |

## View/API registration failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| API route 404 after adding a class | The module did not call `appbuilder.add_api(...)`, or the module is not imported by `myapp/views/__init__.py` | Add the registration call and import the module from `views/__init__.py`; then run migrations/init. |
| Form metadata is incomplete in frontend | Missing `list_columns`, `add_columns`, `edit_columns`, `show_columns`, `search_columns`, `label_title`, or labels on the model/view | Mirror established `MyappModelRestApi` patterns and keep domain-specific fields in the owning sub-skill. |
| Access checks behave too broadly or too narrowly | `has_access`/`can_access` in `MyappSecurityManager` are intentionally permissive for authenticated users | Customize auth with care in a subclass or overlay; preserve anonymous rejection and required AppBuilder bindings. |
| Frontend URL for a model is blank/wrong | `MODEL_URLS` in the runtime config overlay lacks the backend model name or points to an old SPA route | Update the overlay `MODEL_URLS` entry and redeploy/restart the relevant frontend. |

## Auth and RBAC failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Header auth works internally but not externally | Short username auth requires `AUTH_PLATFORM_ACCESS` or an internal dashboard host | Use JWT-style Authorization externally, or deliberately enable platform access only in trusted networks. |
| JWT token rejected | `JWT_PASSWORD` mismatch, malformed token, or user missing/inactive | Use the same overlay secret that generated the token; confirm the user exists and `active=True`. |
| Login auto-creates a user unexpectedly | Default `Myauthdbview.login` can create missing DB users | Override `Myauthdbview` in the runtime `project.py` overlay if your organization requires pre-provisioned users. |
| User cannot see expected resources | Role/project membership data missing after registration or init | Check `Gamma` role, project membership (`project_user`), and any domain-specific project/resource filters. |

## Redis, Celery, and watcher failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Cache or Celery connection errors | `REDIS_HOST`, `REDIS_PORT`, or `REDIS_PASSWORD` mismatch | Set the same Redis env vars for backend, worker, schedule, and watcher processes; remember broker/result use DB 0 and cache uses DB 1. |
| Beat schedules do not fire | Beat process not running or `CELERY_CONFIG` not loaded | Confirm command `celery --app=myapp.tasks.celery_app:celery_app beat --loglevel=info` and that overlay config imports `myapp.tasks`. |
| Tasks stay queued | Worker process not running, wrong queue/broker, or import failure | Confirm worker command, Redis DB 0, and no import errors in `myapp.tasks.schedules`/`async_task`. |
| `watch_workflow.py` or `watch_service.py` exits immediately | Missing `ENVIRONMENT`, missing `CLUSTERS` entry, missing kubeconfig, or no in-cluster config | Fix overlay cluster config or pod service account. Do not start watchers during static verification. |
| Watcher or scheduled task deletes/updates unexpected resources | These tasks operate on Kubernetes CRDs/pods and database records | Route operational cleanup to `deploy-and-operate`; require operator review before starting or changing watchers. |

## Frontend proxy and build failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Local frontend API requests go to the wrong backend | Edited the wrong package's `setupProxy.js`, or did not restart dev server | Each of `frontend`, `vision`, and `visionPlus` has its own proxy file; update the one you run. |
| `/frontend` without slash fails | Main frontend relies on redirect to `/frontend/` and nginx SPA handling | Preserve the redirect middleware and deployment nginx `/frontend/` route. |
| Local dev loops through login or returns 401 | Backend auth cookie/header not established, backend unavailable, or cookie domain unsuitable | Use documented login bootstrap URL, check proxy target, and review `COOKIE_DOMAIN`. |
| Build fails on local machine but not in container | Node/npm/yarn version mismatch or platform-specific line endings | Use Node 16.15+/npm 6.14.8+ as documented, or build in the backend container after permission; normalize CRLF/LF. |

## Escalate or reroute

- Kubernetes resource ordering, PVC/namespace/secret/registry/image-pull issues:
  `deploy-and-operate`.
- Notebook, GPU selector, resource group, image catalog issues:
  `compute-notebooks-and-images`.
- Pipeline DAG/task/template/CronWorkflow/Argo issues:
  `pipelines-and-job-templates`.
- Dataset/SQLLab/ETL engine issues: `data-metadata-and-sqllab`.
- Inference/AIHub/chat/LLM gateway issues: `serving-aihub-and-llm`.
