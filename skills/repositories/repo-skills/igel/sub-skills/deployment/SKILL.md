---
name: deployment
description: "Serve fitted igel models through FastAPI/uvicorn and call the
  prediction API safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Deployment

Use this sub-skill when the user asks to serve a fitted igel model, start the REST endpoint, call the prediction API, use the client example, debug `IGEL_MODEL_RESULTS_PATH`, or reason about host/port options for serving.

## Routing contract

- **Prerequisite route:** serving depends on a fitted classic igel model and its `model_results/` directory. If the user has not already run `fit` or does not have a results directory, route them to [tabular-workflows](../tabular-workflows/SKILL.md) first.
- **Root route:** for broader package routing or uncertainty about whether this is a serving task, return to the [root router](../../SKILL.md).
- **Stay here for:** `igel serve`, FastAPI/uvicorn startup, `IGEL_MODEL_RESULTS_PATH`, `/predict` JSON shape, curl/client calls, deployment-specific failure modes, stale Docker/GUI deployment notes.
- **Route elsewhere for:** training, evaluation, CLI `predict`, export/ONNX, model catalogs, config schemas, tabular preprocessing, or AutoKeras workflows.

## Minimal operating workflow

1. Confirm the fitted model directory contains the artifacts described in [API reference](references/api-reference.md): at minimum `model.joblib` and `description.json`; `predictions.csv` is the endpoint output path.
2. Start the server with the package CLI:

   ```bash
   igel serve -res_dir model_results --host localhost --port 8080
   ```

   The CLI sets `IGEL_MODEL_RESULTS_PATH` before running igel's FastAPI app with uvicorn.
3. Call `POST /predict` with a JSON object whose keys are the feature columns used for prediction. Use [serving workflows](references/serving-workflows.md) for curl and bundled-client examples.
4. If the request fails, inspect [troubleshooting](references/troubleshooting.md) before changing the model or retraining.

## Bundled helper

Use [`scripts/predict_client.py`](scripts/predict_client.py) to format JSON or CSV rows and call the service without relying on the original source example. It supports `--json`, `--json-file`, `--csv`, `--host`, `--port`, `--path`, `--dry-run`, and shape validation for scalar-vs-list payloads.

## Reference map

- [API reference](references/api-reference.md): `serve` options, environment variable contract, FastAPI routes, request/response shape.
- [Serving workflows](references/serving-workflows.md): fitted-model handoff, local startup, curl calls, helper usage, manual uvicorn path.
- [Troubleshooting](references/troubleshooting.md): missing results paths/files, bad payload shapes, host/help confusion, stale Dockerfile, external GUI path.
