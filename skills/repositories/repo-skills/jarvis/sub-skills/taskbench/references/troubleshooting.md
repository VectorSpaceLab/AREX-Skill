# TaskBench troubleshooting

Use this reference when TaskBench inference, evaluation, graph handling, or Back-Instruct construction fails. Prefer validating fixtures before running native evaluation.

## OpenAI-compatible endpoint and API key

Symptoms:

- Connection refused or timeout.
- Response JSON lacks `choices[0].message.content`.
- Non-200 HTTP response.
- `429` rate-limit response.
- Empty or malformed generated result.

Checks:

1. Confirm the endpoint implements `POST /v1/chat/completions`.
2. Confirm `--api_addr` is only the host/address and `--api_port` is the port; native code constructs the full URL itself.
3. Confirm `--api_key` is accepted by the server. Some local servers accept any placeholder token; credentialed services require a real key.
4. Confirm `--llm` matches a model name exposed by the endpoint.
5. Start with `--multiworker 1`, `--temperature 0.2`, and `--top_p 0.1` for inference smoke tests.

Recovery:

- Reduce `--multiworker` when requests fail intermittently or rate limits appear.
- Reuse the same prediction file to resume; native inference skips ids already present.
- Enable `--log_first_detail true` for a single prompt/response trace without logging every request.
- Do not start FastChat, vLLM, or other serving backends from this sub-skill unless another verified skill covers that backend.

## Rate limits and non-200 responses

Native inference and data engine raise errors for `429` and other non-200 statuses. The failed sample is not written, so resume is usually safe.

Recovery:

- Lower `--multiworker`.
- Use smaller `user_requests.json` or a temporary fixture.
- Add endpoint-side throttling if available.
- Keep a copy of corrupt or partial prediction lines before editing a JSONL file manually.

## Malformed JSON model output

Symptoms:

- Native inference logs illegal JSON and raises a content-format error.
- Prediction JSONL contains a raw string, markdown fence, or partially formatted JSON under `result`.
- Native evaluation aborts while decoding a line or logs parsing errors and reduces support counts.

Recovery path:

1. Run the bundled validator against the prediction file.
2. If lines are not valid JSONL, isolate corrupt lines and regenerate those ids.
3. Rerun inference with `--reformat true`.
4. Use `--reformat_by self` to ask the same model to fix formatting, or `--reformat_by FORMATTER_MODEL_NAME` when a separate formatter endpoint is available.
5. Validate again before evaluation.

For temporal data, make sure reformatted output includes `task_links`. For resource data, make sure dependencies are encoded with `<node-j>` argument references when links should be inferred.

## Resource vs temporal mismatch

Symptoms:

- Assertion that resource dependency only supports HuggingFace and Multimedia domains.
- Assertion that `input-type`/`output-type` are undefined.
- Assertion that `parameters` are undefined.
- Poor or empty link metric because temporal links were treated as resource references or resource references were treated as temporal links.

Routing:

- `data_dailylifeapis` must use `--dependency_type temporal`.
- Tool libraries with `parameters` and no `input-type` must use `temporal`.
- Tool libraries with `input-type` and `output-type` must use `resource`.

Recovery:

- Re-run inference and evaluation with the correct dependency type; do not mix prediction files generated under different schemas.
- If a user selected Daily Life APIs with `resource`, explain that native inference asserts and route to temporal.
- Validate `tool_desc.json` and `graph_desc.json` to confirm the selected type.

## Prediction and metrics directory naming

Symptoms:

- Evaluation cannot find `MODEL_NAME.json`.
- Metrics are written to an unexpected directory.
- Batch evaluation skips files or evaluates the wrong prediction set.

Checks:

- Native inference writes inside `DATA_DIR/predictions...`.
- `--tag true` changes the prediction directory name by appending demo/reformat suffixes.
- Native evaluation expects `--prediction_dir` relative to `DATA_DIR`.
- If `--save_dir` is omitted, native evaluation replaces `predictions` with `metrics` in the prediction directory name.
- The bundled batch wrapper accepts an explicit data directory and prediction directory and derives model names from `*.json` files.

Recovery:

- Pass the exact prediction directory name used by inference.
- Use `--save_dir` for explicit metrics output naming.
- Avoid absolute prediction paths with native evaluation; convert them to paths relative to `DATA_DIR` or use the bundled wrapper.

## Missing Rouge or BERTScore dependencies

Symptoms:

- Metric loader errors for Rouge or BERTScore.
- BERTScore attempts to access a model cache that is unavailable.
- Offline evaluation fails only when `-m all` is used.

Recovery:

- For smoke checks, use `-m f1 -m link -m argument` instead of `-m all`.
- If full leaderboard-style metrics are required, prepare the metric packages and model cache in the TaskBench environment before evaluation.
- If `--prompting` is not `cot`, native `all` skips Rouge and BERTScore.

## Visualization output paths

Symptoms:

- Native visualization hangs or fails due to missing display.
- A PDF appears beside `graph_desc.json` unexpectedly.
- Native graph sampler writes `test.png` in the current working directory.

Recovery:

- Use `scripts/taskbench_graph_tools.py visualize` with explicit `--input` and `--output`.
- Use a non-interactive image extension such as `.png`, `.pdf`, or `.svg`.
- Keep visualization outputs in a temporary or user-approved output directory.

## Accidental writes beside data

Native scripts write in these locations:

| Native script | Write behavior |
| --- | --- |
| `inference.py` | Appends predictions and logs under `DATA_DIR/predictions...`. |
| `evaluate.py` | Writes metrics and logs under `DATA_DIR/SAVE_DIR`. |
| `generate_graph.py` | Chooses output by string replacement on the input filename. |
| `graph_sampler.py` | Writes `test.png` in the current working directory when figure saving is enabled. |
| `visualize_graph.py` | Saves a PDF beside `DATA_DIR/graph_desc.json`. |
| `data_engine.py` | Writes `data_raw.json`, `statistics.json`, logs, copied graph/tool files, and optional figures in `--data_dir`; defaults to a timestamped directory if omitted. |
| `format_data.py` | Truncates and writes `data.json`, `user_requests.json`, and `data_error.json` in `--data_dir`. |

Recovery and prevention:

- Use temporary copies for experiments.
- Prefer bundled graph tools for graph outputs.
- Pass explicit `--data_dir`, `--prediction_dir`, and `--save_dir`.
- Do not run native data construction in a source data directory unless overwrites are intended.

## Legacy data schema

Symptoms:

- Native evaluation raises key errors for `task_nodes`, `task_steps`, or `user_request`.
- Data rows contain `instruction`, `tool_steps`, `tool_nodes`, and `tool_links` instead.
- List-like fields are JSON strings.

Recovery:

- Treat legacy rows as source evidence, not direct evaluator input.
- Convert a temporary copy to normalized fields before evaluation.
- Run the bundled validator; it reports legacy rows and can distinguish warnings from invalid schemas.

## Prediction coverage mismatch

Symptoms:

- Metrics JSON reports fewer `all_samples` than expected.
- Support counts are lower than the number of predictions.

Checks:

- Evaluation intersects ids from labels and predictions; missing ids are silently dropped.
- Parse errors inside `result` can reduce `step_supports`, `node_supports`, `link_supports`, or `argument_supports`.
- Alignment filters further reduce label ids when `--alignment` is used.

Recovery:

- Compare ids in `DATA_DIR/data.json` and `DATA_DIR/PREDICTION_DIR/MODEL_NAME.json`.
- Regenerate missing ids with native inference resume behavior.
- Validate prediction result schema before re-running metrics.
