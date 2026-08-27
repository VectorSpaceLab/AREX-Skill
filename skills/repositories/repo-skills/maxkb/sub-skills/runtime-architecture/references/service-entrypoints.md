# Service entrypoints

## Canonical startup path
- `main.py` is the primary entrypoint for development and production-style runs.
- It adds `apps/` to `sys.path`, sets `DJANGO_SETTINGS_MODULE=maxkb.settings`, and chooses the runtime profile from `SERVER_NAME`.
- `apps/manage.py` is the lower-level Django entrypoint for migrations and management commands.

## Runtime profiles
- `SERVER_NAME=web` loads the full web stack.
- `SERVER_NAME=local_model` loads the minimal model-server profile.
- `apps/maxkb/settings/__init__.py` routes to the correct settings module.
- `apps/maxkb/urls/web.py` and `apps/maxkb/urls/model.py` mirror that split.

## Commands users actually run
```bash
python main.py dev
python main.py dev celery
python main.py dev local_model
python main.py start all -d
python main.py start web -w 3
python main.py start task
python main.py stop all
python main.py status
python main.py upgrade_db
python main.py collect_static
```

## Backend wiring worth remembering
- `apps/ops/celery/__init__.py` defines the Celery app and queue behavior.
- `apps/ops/celery/hmac_signed_serializer.py` registers the custom serializer used by Celery.
- `apps/oss/tests.py` contains a route smoke test that proves the runtime URL surface is reachable.
- `apps/maxkb/conf.py` is the canonical config object; prefer it over hard-coded paths.

## Static asset and i18n flow
- Frontend assets are collected into `ui/dist` and then served by Django staticfiles.
- `python main.py collect_static` is the repo-normal path before a production-style run.
- `makemessages` and `compilemessages` live under `apps/manage.py` and are required for i18n updates.

## Notes for live checks
- Live DB and Redis access are optional for static inspection, but real startup requires them.
- If a command fails because a service is missing, describe the missing dependency explicitly instead of assuming a code bug.
