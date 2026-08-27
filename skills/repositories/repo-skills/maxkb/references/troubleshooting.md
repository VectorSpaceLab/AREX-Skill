# Cross-cutting troubleshooting

## Common failure modes
- `ModuleNotFoundError` for repo packages: run through `main.py` or set `PYTHONPATH=apps` for direct inspection.
- Wrong settings loaded: confirm `SERVER_NAME` and the selected `maxkb.settings` profile.
- 404s on admin/chat URLs: verify `ADMIN_PATH` and `CHAT_PATH` from the canonical config source.
- DB/Redis errors: confirm the configured host/port or sentinel settings and that the services are running.
- Static asset issues: rebuild `ui/`, then run `python main.py collect_static`.
- Celery tasks not moving: confirm the worker is running and the queue names match the code.
- Permission errors: check the workspace/resource/user mapping and the matching permission constant.

## What to mention in a handoff
- The exact surface that failed.
- The config key or route family that controls it.
- Whether the issue was verified locally or remains inferred from static inspection.
- Any live dependency that was not available during validation.

## Preferred response style
- Keep the explanation short and actionable.
- Do not guess at missing environment state.
- Point to the smallest relevant sub-skill.
