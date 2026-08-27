# Igel serving API reference

This reference covers only igel's fitted-model serving path. For creating the `model_results/` directory, use [tabular-workflows](../../tabular-workflows/SKILL.md). For package-wide routing, use the [root router](../../../SKILL.md).

## `igel serve` CLI

Start from a shell where the `igel` command is installed:

```bash
igel serve -res_dir model_results --host localhost --port 8080
```

| Option | Short form | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `--model_results_dir` | `-res_dir` | yes | none | Directory produced by igel fitting; used to locate the persisted model and description metadata. |
| `--host` | `-h` | no | `localhost` | Host/interface passed to uvicorn. Use `127.0.0.1` or `localhost` for local-only serving; use `0.0.0.0` only when the network boundary is intentional. |
| `--port` | `-p` | no | `8080` | Port passed to uvicorn. The current CLI help/source default is `8080`; older docs may mention `8000`. |
| `--help` | none on this subcommand | no | n/a | Show serve help. On `igel serve`, `-h` means host, not help. |

The CLI converts `--port` to an integer and calls igel's FastAPI app through uvicorn.

## Environment variable contract

`IGEL_MODEL_RESULTS_PATH` is the environment variable read by the FastAPI `/predict` handler.

- When you launch with `igel serve --model_results_dir ...`, the CLI sets `IGEL_MODEL_RESULTS_PATH` for the server process automatically.
- If you launch the FastAPI app manually with uvicorn, set it yourself:

  ```bash
  export IGEL_MODEL_RESULTS_PATH=model_results
  python -m uvicorn igel.servers.fastapi_server:app --host localhost --port 8080
  ```

The path should point to the fitted-model results directory. It is not a model file path.

## Expected results directory contents

The service builds these paths under `IGEL_MODEL_RESULTS_PATH` on each prediction request:

| File | Role |
| --- | --- |
| `model.joblib` | Persisted scikit-learn model loaded for prediction. |
| `description.json` | Metadata from fitting, including target names, model type, and dataset/preprocessing settings. |
| `predictions.csv` | Output CSV written/overwritten by the prediction call. |

The request body is temporarily written as `post_req_data.csv` in the server process current working directory, then removed after the normal success path. If a failure interrupts cleanup, remove the stale temp file before retrying.

## FastAPI routes

| Method | Path | Purpose | Success response |
| --- | --- | --- | --- |
| `GET` | `/` | Minimal health/test route. | `{"success": true}` |
| `POST` | `/predict` | Convert JSON body to a temporary CSV, run `Igel(cmd="predict", ...)`, and return predictions. | `{"prediction": [[...], ...]}` |

## `/predict` request shape

Send `Content-Type: application/json` and a JSON object:

```json
{
  "feature_a": 1,
  "feature_b": 2.5,
  "feature_c": "category"
}
```

or a batch object where every value is a list of the same length:

```json
{
  "feature_a": [1, 2, 3],
  "feature_b": [2.5, 3.5, 4.5],
  "feature_c": ["x", "y", "z"]
}
```

Rules:

- Keys are prediction input columns. Include every feature column the fitted model expects.
- Do not include the training target column unless the model was intentionally trained to expect it as an input feature.
- All scalar values mean a single-row request.
- All list values mean a batch request; all lists must have the same length.
- Avoid mixed scalar/list payloads unless a client deliberately broadcasts the scalars to match the list length before sending.
- Bad JSON, missing feature columns, mismatched list lengths, unseen categorical values, or preprocessing mismatches can surface as server-side prediction errors.

## `/predict` response shape

A successful response is JSON with a top-level `prediction` key:

```json
{"prediction": [[0.0]]}
```

For batch requests, there is one inner list per row:

```json
{"prediction": [[1.0], [0.0], [0.0]]}
```

For multi-output models, each inner list can contain more than one value. The output target names come from `description.json`, while the HTTP response exposes only the nested list.
