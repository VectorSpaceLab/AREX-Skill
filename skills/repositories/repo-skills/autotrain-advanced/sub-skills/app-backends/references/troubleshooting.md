# App/API/backend troubleshooting

## App startup

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `autotrain app --share` raises `NGROK_AUTH_TOKEN not set` | Share mode requires ngrok auth | Set `NGROK_AUTH_TOKEN` or run without `--share`. |
| UI starts but no public URL appears | Share mode failed before/inside ngrok | Check ngrok token and port conflicts; run local first. |
| `autotrain.log` contains import errors | Service imports failed before uvicorn stabilized | Run root install/backend checks and the safe FastAPI route probe. |
| `/` redirects unexpectedly | Expected behavior | Main app redirects `/` to `/ui/`, preserving query params. |

## API and route probes

- Main app version endpoint is `/api/version` because `api_router` is mounted at `/api`.
- Training API health endpoint is `/health` on `autotrain.app.training_api:api`.
- Use `check_app_api.py` for importable route checks before opening ports.

## Backend auth and jobs

- Spaces/endpoints/NGC/NVCF routes require external credentials and may create remote resources.
- Hosted backends usually need Hub-accessible data and model artifacts.
- If hosted launch fails, reduce to local config/data validation first.
- Preserve job ids and logs when troubleshooting a partially created backend job.

## Space runner format errors

- `--env` entries must be semicolon-separated `NAME=value` pairs.
- `--args` entries are semicolon-separated; `name=value` creates a value argument and a bare name creates a store-true style flag.
- `--backend` must be a `spaces-*` key; SpaceRunner does not accept endpoint/NGC/NVCF keys.

## Task parameter confusion

- App/API task keys can use colon subtypes such as `llm:sft`, `st:triplet`, and `vlm:vqa`.
- YAML config aliases differ for some tasks, especially LLM (`llm-sft`, `llm-dpo`, etc.). Use `cli-config` for parser normalization.
- VLM has app/API/config parameters but no top-level `autotrain vlm` command.
