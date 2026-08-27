# Troubleshooting

## Common runtime problems
- `ModuleNotFoundError` or `ImportError`: run through `main.py` or use `PYTHONPATH=apps`.
- Wrong settings profile: confirm `SERVER_NAME` before assuming the URL or settings tree is wrong.
- `404` on admin/chat routes: check `ADMIN_PATH` and `CHAT_PATH` in `apps/maxkb/conf.py`.
- Database or Redis errors: verify the configured host/port, password, and sentinel settings.
- Celery tasks appear stuck: make sure the worker for the right queue is running.
- Static files missing in production mode: rebuild `ui/` and rerun `python main.py collect_static`.
- Local-model runtime unreachable: confirm the `local_model` profile and the host/port settings.

## Safe response pattern
1. Identify the entrypoint.
2. Identify the active settings profile.
3. Identify the dependency that is missing.
4. State whether the issue was verified or only inferred from static evidence.

## Do not do
- Do not hard-code route prefixes in the answer if the config object already exposes them.
- Do not claim a service is healthy unless you actually verified it.
