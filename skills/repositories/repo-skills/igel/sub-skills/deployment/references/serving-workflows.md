# Serving workflows

Use these workflows when the user already has a fitted igel model. If they need to create or locate `model_results/`, route to [tabular-workflows](../../tabular-workflows/SKILL.md). For package-wide routing, use the [root router](../../../SKILL.md).

## 1. Handoff from fitting

A normal `igel fit ...` run creates a `model_results/` directory in the working directory where fitting ran. For serving, keep the directory together and deploy/copy it as a unit.

Before starting the endpoint, check:

```text
model_results/
  model.joblib
  description.json
  predictions.csv        # may be absent before the first served prediction; it is the endpoint output path
```

`model.joblib` and `description.json` are required. `predictions.csv` is written or overwritten when `/predict` runs.

## 2. Start a local server

```bash
igel serve --model_results_dir model_results --host localhost --port 8080
```

Equivalent short form:

```bash
igel serve -res_dir model_results -h localhost -p 8080
```

Notes:

- On the `serve` subcommand, `-h` is the host option. Use `igel serve --help` for help.
- The CLI sets `IGEL_MODEL_RESULTS_PATH` internally before running the FastAPI app with uvicorn.
- Keep the process running in the foreground while testing, or run it under your normal process manager for longer-lived service use.
- Igel's endpoint does not add authentication, TLS, rate limiting, or request validation beyond FastAPI/Python errors. Put it behind appropriate network controls for shared environments.

## 3. Smoke-test the endpoint

The server has a minimal GET route:

```bash
curl -s http://localhost:8080/
```

Expected success body:

```json
{"success": true}
```

## 4. Call `/predict` with curl

Single-row scalar payload:

```bash
curl -X POST http://localhost:8080/predict \
  --header 'Content-Type: application/json' \
  --data '{"preg": 1, "plas": 180, "pres": 50, "skin": 12, "test": 1, "mass": 456, "pedi": 0.442, "age": 50}'
```

Batch payload, with every column as an equally sized list:

```bash
curl -X POST http://localhost:8080/predict \
  --header 'Content-Type: application/json' \
  --data '{"preg": [1, 6, 10], "plas": [192, 52, 180], "pres": [40, 30, 50], "skin": [25, 35, 12], "test": [0, 1, 1], "mass": [456, 123, 155], "pedi": [0.442, 0.22, 0.19], "age": [50, 40, 29]}'
```

The exact columns must match the feature columns expected by the fitted model. The example column names are only illustrative.

## 5. Call with the bundled helper

From this sub-skill directory:

```bash
python scripts/predict_client.py \
  --host localhost \
  --port 8080 \
  --json '{"preg": 1, "plas": 180, "pres": 50, "skin": 12, "test": 1, "mass": 456, "pedi": 0.442, "age": 50}'
```

From the generated skill root:

```bash
python sub-skills/deployment/scripts/predict_client.py --host localhost --port 8080 --json-file payload.json
```

For CSV rows, the helper converts a headered CSV into the column-oriented JSON object that igel expects:

```bash
python sub-skills/deployment/scripts/predict_client.py --host localhost --port 8080 --csv rows_to_score.csv
```

Use `--dry-run` to print the JSON payload without sending it:

```bash
python sub-skills/deployment/scripts/predict_client.py --csv rows_to_score.csv --dry-run
```

The helper validates that list-valued columns have equal lengths and rejects mixed scalar/list JSON by default. If you intentionally want scalars repeated to match a batch list length, pass `--broadcast-scalars`.

## 6. Manual uvicorn path

Prefer `igel serve` because it sets the model-results environment variable correctly. If a process manager requires direct uvicorn invocation, set the environment variable first:

```bash
export IGEL_MODEL_RESULTS_PATH=model_results
python -m uvicorn igel.servers.fastapi_server:app --host localhost --port 8080
```

The manual path uses the same FastAPI app and `/predict` behavior as the CLI path.

## 7. Stop or restart

- Stop a foreground server with `Ctrl-C`.
- If changing the fitted model directory, restart the server with the new `--model_results_dir` or update `IGEL_MODEL_RESULTS_PATH` before launching uvicorn.
- If a failed request leaves `post_req_data.csv` in the server working directory, remove it before retrying to avoid confusion during debugging.
