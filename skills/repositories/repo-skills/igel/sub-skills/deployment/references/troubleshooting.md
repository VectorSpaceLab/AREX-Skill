# Deployment troubleshooting

Use this for igel serving and client-call failures. For fit/evaluate/predict/export troubleshooting, route to [tabular-workflows](../../tabular-workflows/SKILL.md). For route selection, use the [root router](../../../SKILL.md).

## Quick triage

1. Verify the server was started by `igel serve --model_results_dir ...` or that `IGEL_MODEL_RESULTS_PATH` was set before manual uvicorn startup.
2. Verify the results directory has `model.joblib` and `description.json`.
3. Verify the client sends `Content-Type: application/json` and that feature columns match the fitted model.
4. Reproduce with a one-row scalar JSON payload before debugging batch requests.
5. Use `scripts/predict_client.py --dry-run` to inspect payload shape before sending.

## Symptoms and fixes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `POST /predict` returns `null`, empty body, or only logs a warning about the model-results path. | FastAPI app was launched without `IGEL_MODEL_RESULTS_PATH`; this can happen with direct uvicorn startup. | Prefer `igel serve --model_results_dir model_results ...`. If using uvicorn directly, run `export IGEL_MODEL_RESULTS_PATH=model_results` before startup. |
| Server logs `FileNotFoundError` or fails while loading metadata/model. | Wrong directory, missing `model.joblib`, missing `description.json`, or a path to the file was passed instead of the directory. | Point `--model_results_dir`/`IGEL_MODEL_RESULTS_PATH` at the fitted `model_results/` directory. Recreate it via fitting in [tabular-workflows](../../tabular-workflows/SKILL.md) if needed. |
| `predictions.csv` is not where expected. | Served predictions write to `predictions.csv` under `IGEL_MODEL_RESULTS_PATH`, not necessarily the caller's shell directory. | Inspect the configured model-results directory. Remember each request can overwrite the same prediction file. |
| HTTP 500 or pandas error such as mismatched lengths. | Batch JSON has list-valued columns of different lengths, or mixes a scalar with a multi-row list. | Use all scalars for one row, or all equal-length lists for batches. The bundled helper rejects these shape errors before sending. |
| Prediction fails after a syntactically valid request. | Payload columns differ from the features seen at fitting time, a required feature is missing, an unexpected target column is included, values have incompatible types, or preprocessing differs from the fitted description. | Compare payload keys against the fitted training features. Start with one complete row. Missing-column tests are useful synthetic cases because they exercise the endpoint's failure path. |
| JSON with missing values fails or produces bad model inputs. | JSON has no valid `NaN` token; empty CSV fields become ambiguous. | Fill or impute missing values before sending. With the bundled helper, either fix the CSV or pass `--fill-empty VALUE` intentionally. |
| `igel serve -h` does not show help. | On the `serve` subcommand, `-h` is the host option. | Use `igel serve --help`. For host use `--host` or `-h`. |
| Server starts on the wrong port compared with old docs. | The current CLI/source default is port `8080`; some docs text mentions `8000`. | Check `igel serve --help` in the installed package. Pass `--port` explicitly when writing instructions or scripts. |
| Port is already in use. | Another server owns the port. | Pick a different `--port`, stop the other process, or use a process manager/reverse proxy with a clear binding plan. |
| Remote clients cannot connect. | Bound to `localhost`, firewall blocks the port, or container/network mapping is missing. | Bind to an intentional interface such as `0.0.0.0` only inside a controlled network; expose the port via your platform's networking controls. Add auth/TLS outside igel if needed. |
| Stale `post_req_data.csv` appears in the server working directory. | The endpoint writes request payloads to a temp CSV and removes it on the normal success path; some failures can leave it behind. | Stop the server if needed, remove the stale file, then retry with a known-good request. |

## Docker and GUI notes

- Treat the bundled Dockerfile from the package source as **stale reference evidence**, not as a verified deployment helper: it expects build inputs such as `requirements.txt` and `setup.py` that are not present in the current package layout and repeats setup-copy steps.
- The public docs mention a published container image and local Docker builds. Do not present the stale source Dockerfile as a self-contained, guaranteed build path. If a user needs Docker, either use a trusted published image after independent validation or write a fresh Dockerfile for the installed package and fitted `model_results/` contract.
- Do not bundle or run GUI clone/npm behavior as a helper. `igel gui` clones an external UI repository and runs Node/npm commands, so it is networked, non-self-contained, and outside this deployment sub-skill's safe serving path.
