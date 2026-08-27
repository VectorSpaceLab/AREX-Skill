---
name: app-backends
description: "Operate AutoTrain Advanced FastAPI app/API, spacerunner, backend
  selection, auth, jobs, and safe route checks."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain app, API, and backends

Use this sub-skill for the local UI, training API, Space runner, backend keys, hosted backend auth, job/log inspection, and app/API task parameter routing.

## Supported entry points

- `autotrain app --help`
- `autotrain api --help`
- `autotrain spacerunner --help`
- FastAPI app object: `autotrain.app.app:app`
- Training API object: `autotrain.app.training_api:api`
- Backend keys from `autotrain.backends.base.AVAILABLE_HARDWARE`
- App parameter helper: `autotrain.app.params.get_task_params(task, param_type)`

## Safe route checks

Use the bundled script to probe importable app routes without starting uvicorn:

```bash
python skills/disco/autotrain-advanced/sub-skills/app-backends/scripts/check_app_api.py
```

Expected safe checks include:

- main app `/` redirecting toward `/ui/`;
- main app `/api/version` returning the package version;
- training API route registration for `/` and `/health` without issuing requests to that app, because its lifespan hook starts training.

## Backend families

- Local: `local`, `local-cli`, `local-ui`
- Hugging Face Spaces: keys beginning with `spaces-`
- Hugging Face endpoints: keys beginning with `ep-`
- NVIDIA GPU Cloud: keys beginning with `dgx-`
- NVIDIA Cloud Functions: keys beginning with `nvcf-`

Use the root `scripts/check_backends.py` helper to print the available key list from the installed package.

## Auth and environment signals

- `autotrain app --share` requires `NGROK_AUTH_TOKEN`.
- Hosted backends usually need a Hugging Face username/token and Hub-accessible artifacts.
- Training API startup logs environment-derived values such as `AUTOTRAIN_USERNAME`, `PROJECT_NAME`, `TASK_ID`, `DATA_PATH`, and `MODEL`.
- In hosted Spaces, `SPACE_ID` activates OAuth attachment for the main app.

## References

- `references/workflows.md` — CLI service commands and app/API probes.
- `references/backend-reference.md` — backend key families and when to use them.
- `references/troubleshooting.md` — auth, route, job, ngrok, and hosted backend issues.
