# Backend lifecycle, AppBuilder registration, RBAC, and async services

This reference distills the backend operating contract from CubeStudio's Flask
AppBuilder source. It is self-contained: it names evidence paths for orientation
but does not require this generated skill to link to or depend on the original
checkout.

## Safe-use boundary

The backend modules are service code, not standalone scripts. Do not import
`myapp`, run `myapp init`, run migrations, or start worker/watch processes until
a real runtime overlay, DB, Redis, and operator-approved environment are in
place. For static inspection, use the bundled `scripts/inspect_cube_studio_structure.py`.

## Application startup sequence

Evidence: `myapp/__init__.py`, `myapp/security.py`, `myapp/views/__init__.py`,
`install/docker/config.py`, and installed inspection facts.

1. **Flask app and config import**
   - `app = Flask(__name__)` is created at import time.
   - The config module is loaded from `MYAPP_CONFIG`; if unset it defaults to
     `myapp.config`.
   - In the checked-out source tree, `myapp/config.py` is an empty placeholder.
     A real Docker/Kubernetes overlay must be mounted or otherwise made
     importable before a meaningful app import.
   - `DATA_DIR` is created if configured, static asset manifest helpers are
     registered, optional blueprints are registered, and FAB logging can be
     silenced by `SILENCE_FAB`.
2. **Backend services are bound to the app**
   - `db = SQLA(app)` binds Flask-SQLAlchemy.
   - CSRF protection is optional and controlled by `WTF_CSRF_ENABLED` plus
     `WTF_CSRF_EXEMPT_LIST`.
   - `pessimistic_connection_handling(db.engine)` is installed immediately, so
     the configured SQLAlchemy URI must be usable for the chosen inspection or
     runtime mode.
   - `cache = setup_cache(app, CACHE_CONFIG)` uses Redis in the supplied
     overlays.
   - `Migrate(app, db, directory=APP_DIR + "/migrations")` wires Alembic.
3. **Flask AppBuilder is constructed**
   - `CUSTOM_SECURITY_MANAGER` may override security, but it must subclass
     `MyappSecurityManager`.
   - `AppBuilder(app, db.session, base_template="myapp/base.html",
     indexview=MyIndexView, security_manager_class=custom_sm,
     update_perms=False)` is created inside an app context.
   - Startup alone does not refresh all permissions because `update_perms` is
     false here; `myapp init` explicitly calls `appbuilder.add_permissions(update_perms=True)`.
4. **Request hooks are installed**
   - `check_login` allows static/login/register/health/wechat/wework/dingtalk,
     proxy, and message API paths; all other unauthenticated requests abort 401.
   - Header authentication uses `Authorization`: a short username is accepted
     only when platform access is enabled or when the request host is an
     internal dashboard host; otherwise it is decoded as a JWT using
     `JWT_PASSWORD` and can also accept the compact two-segment token emitted by
     `MyUser.secret`.
   - After each request, cookies such as `myapp_username` and optional `id` are
     set; `HTTP_HEADERS` are added globally.
5. **Views are imported last**
   - `from myapp import views` imports `myapp/views/__init__.py`.
   - Each view module registers APIs with `appbuilder.add_api(...)` or a view
     with `appbuilder.add_view_no_menu(...)` during import.
   - Installed inspection with the Docker-style overlay proved an AppBuilder app
     with **684 Flask routes**. Treat a much smaller route set as an overlay,
     import, or registration problem.

## Runtime initialization and DB order

Evidence: `install/docker/entrypoint.sh`, `myapp/create_db.py`,
`myapp/check_tables.py`, `myapp/cli.py`.

The backend container entrypoint performs this order before running the server:

1. create runtime static symlinks for workspace, dataset, AIHub, and global
   directories;
2. `export FLASK_APP=myapp:app`;
3. `python myapp/create_db.py` to create the MySQL database named by
   `MYSQL_SERVICE` if it does not exist;
4. `myapp db upgrade` to apply Alembic migrations;
5. `myapp fab create-admin --username admin ... --password admin` to create the
   default admin account;
6. `myapp init` to refresh permissions, roles, and seed catalogs;
7. for `STAGE=dev` or `STAGE=prod`, `python myapp/check_tables.py` verifies the
   required tables before `python myapp/run.py` or gunicorn starts.

Do not skip `myapp init` after adding view/API classes; otherwise new view-menu
permissions may not be visible. `check_tables.py` expects FAB tables plus
CubeStudio tables such as `project`, `project_user`, `repository`, `images`,
`job_template`, `pipeline`, `task`, `run`, `workflow`, `notebook`, `service`,
`inferenceservice`, `dataset`, `metadata_table`, `metadata_metric`, `dimension`,
`docker`, `model`, `nni`, `logs`, and `alembic_version`.

## What `myapp init` seeds

`myapp/cli.py` defines the Flask CLI factory and `init` command. It:

- calls `appbuilder.add_permissions(update_perms=True)`;
- creates/syncs `Gamma` and `Admin` roles;
- creates the public org project and job-template category projects;
- creates the default `hubsecret` repository record using `REPOSITORY_ORG`;
- imports seed catalogs from `myapp/init/`, including job templates, pipelines,
  datasets, train models, services, inference services, AIHub entries, chat
  entries, ETL pipelines, AutoML entries, and image catalogs;
- rewrites seed Git/image URLs using configured `GIT_URL` and `REPOSITORY_ORG`.

This command mutates the database. Run it only in a prepared runtime.

## Adding or changing backend model-view/API registrations

Use this recipe for shared AppBuilder plumbing. Put domain semantics in the
owning sibling sub-skill.

1. **Model**: define or update a SQLAlchemy model in the relevant
   `myapp/models/model_*.py` module. Most CubeStudio models inherit shared base
   mixins and expose `label_columns`/computed HTML properties.
2. **API/view class**: define a `MyappModelRestApi`, form API, FAB model view,
   or base-class-derived view in `myapp/views/view_*.py`.
   - Set `datamodel` to a SQLA interface for the model.
   - Set `route_base` for public API paths when the default class-based path is
     not intended.
   - Maintain `list_columns`, `add_columns`, `edit_columns`, `show_columns`,
     `search_columns`, and `label_title` so the frontend can render metadata.
   - Put validation in `pre_add_req`, `pre_update_req`, `pre_add`, `pre_update`,
     and response transforms instead of ad hoc route-only logic.
3. **Register**: call `appbuilder.add_api(Your_ModelView_Api)` or the correct
   AppBuilder registration function in the module.
4. **Import**: add `from . import view_your_module` to `myapp/views/__init__.py`.
   If the module is not imported there, startup will not register its routes.
5. **Migrate/init**: add an Alembic migration for schema changes, then run the
   runtime initialization sequence and `myapp init` so FAB permissions exist.
6. **Frontend mapping**: if the entity needs a shared frontend route, update the
   `MODEL_URLS` map in the runtime config overlay. Domain-specific UI route
   details belong to the matching sibling sub-skill.

Static sanity checks before touching a live runtime:

```bash
python scripts/inspect_cube_studio_structure.py /path/to/cube-studio
```

Look for the expected view imports, appbuilder registrations, and overlay files.

## RBAC, login, and project hooks

Evidence: `myapp/security.py`, `install/docker/project.py`.

- `MyUser` extends FAB's `ab_user` with `nickname`, `org`, `quota`, `active`,
  `balance`, contact, coupon/voucher/billing, real-name, and subaccount fields.
- `MyRole` extends `ab_role` and exposes permissions display helpers.
- `MyappSecurityManager` supports only `AUTH_DB`, installs the security API,
  uses `MyUserRemoteUserModelView`, and binds `authdbview` to
  `Myauthdbview` imported from `myapp.project`.
- `sync_role_definitions` ensures `Admin` and `Gamma` exist.
- `has_access` returns true for authenticated users or JWT-authenticated users;
  `can_access` rejects anonymous users and otherwise returns true.
- The default `Myauthdbview` in the runtime `project.py` overlay supports
  `/login/api/`, `/login/`, and `/logout`. Missing users can be auto-created
  through `auth_user_remote_org_user`; the post-login path can create user
  workspace directories and copy example pipeline files.
- The overlay `project.py` also defines notification/resource hook functions:
  `push_resource_apply`, `push_resource_approve`, `push_admin`, and
  `push_message`. They are no-ops in the default overlay and are the safest
  place to integrate organization-specific messaging or approvals.

When customizing auth, edit the runtime overlay `project.py` or provide a
`CUSTOM_SECURITY_MANAGER` subclass that still extends `MyappSecurityManager`.
Do not edit only the empty root placeholder and expect containers or Kubernetes
pods to pick it up.

## Celery worker, beat, and watcher lifecycle

Evidence: `install/docker/config.py`, `myapp/tasks/celery_app.py`,
`myapp/tasks/schedules.py`, `myapp/tasks/async_task.py`, `myapp/tools/*.py`, and
Kubernetes deployment manifests.

- `myapp/tasks/celery_app.py` creates the global Celery app from
  `get_celery_app(conf)` and imports `myapp.tasks` from the overlay's
  `CeleryConfig`.
- Redis DB 0 is used for Celery broker/results, Redis DB 1 for Flask cache, and
  Redis DB 2 for the socket/message queue in the default config.
- Worker command used by Kubernetes:
  `celery --app=myapp.tasks.celery_app:celery_app worker --loglevel=info --pool=prefork -Ofair -c 20 -n worker@%h`.
- Beat command used by Kubernetes:
  `celery --app=myapp.tasks.celery_app:celery_app beat --loglevel=info`.
- Scheduled tasks include workflow cleanup, timerun config generation, old-data
  cleanup, pipeline-run checks, debug docker cleanup, GPU/pod utilization
  watches, node-resource adjustment, and pod-terminating checks. Some optional
  schedules are commented out in the overlay.
- Async tasks include docker commit checks, notebook commit checks, service
  upgrades, dataset updates, and Kubernetes resource queries.
- Watch services are managed by `supervisord.conf`: `watch_workflow.py` and
  `watch_service.py` run as long-lived programs.
- Watchers require `ENVIRONMENT` to match a key in `CLUSTERS`, then use that
  cluster's `KUBECONFIG` or in-cluster config. They update DB state and send
  messages from Kubernetes watch events.

These workers and watchers are side-effectful and may delete or update
Kubernetes resources and database records. For verification or planning, inspect
source and manifests only; do not start them unless operating a real cluster.
