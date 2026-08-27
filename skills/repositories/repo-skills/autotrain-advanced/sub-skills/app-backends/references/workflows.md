# App/API/backend workflows

## Local UI

Inspect:

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py app --help
```

Run locally:

```bash
autotrain app --host 127.0.0.1 --port 7860 --workers 1
```

Share with ngrok only when explicitly requested and `NGROK_AUTH_TOKEN` is set:

```bash
autotrain app --share --port 7860
```

The command writes process output to `autotrain.log` in the current working directory.

## Training API

Inspect:

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py api --help
```

Run:

```bash
autotrain api --host 127.0.0.1 --port 7860
```

The CLI imports `autotrain.app.training_api:api` and starts uvicorn.

## Safe route probe

Use this before starting long-running services:

```bash
python skills/disco/autotrain-advanced/sub-skills/app-backends/scripts/check_app_api.py
```

The script uses FastAPI `TestClient` for the main app and inspects training API routes without issuing requests to that app, because the training API lifespan hook starts training. It does not open a network listener.

## Space runner

Inspect:

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py spacerunner --help
```

Required arguments:

- `--project-name`
- `--script-path`
- `--username`
- `--token`
- `--backend` with a `spaces-*` backend key

Optional semicolon-separated dictionaries:

- `--env FOO=bar;FOO2=bar2`
- `--args key=value;flag_without_value`

## App task parameters

Use `autotrain.app.params.get_task_params(task, param_type)` to inspect app/API-visible parameters without launching a job. Useful keys include:

- `llm:sft`, `llm:dpo`, `llm:orpo`, `llm:reward`, `llm:generic`
- `st:pair`, `st:pair_class`, `st:pair_score`, `st:triplet`, `st:qa`
- `vlm:captioning`, `vlm:vqa`
- `tabular:classification`, `tabular:regression`

## Backend-first routing

If the user asks about auth, launch target, logs, job ids, app routes, or hosted hardware, stay in this sub-skill even when the underlying task is LLM, text, or vision. Route back to the task sub-skill only for config fields and data schemas.
