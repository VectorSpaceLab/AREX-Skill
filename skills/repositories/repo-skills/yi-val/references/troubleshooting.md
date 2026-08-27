# YiVal troubleshooting

## Import and installation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'yival'` | Package is not installed in the active Python. | Activate the intended environment and run `python -m pip install yival`, or from a checkout run `python -m pip install -e .`. |
| `ModuleNotFoundError: pkg_resources` during `yival --help` | `alpaca_eval` imports `pkg_resources`; very new setuptools no longer exposes it by default. | Run `python -m pip install 'setuptools<81'` in the active environment, then retry `python -m yival --help`. |
| `ImportError` warning about `SFTTrainer` or trainer modules | Optional trainer extras are not installed. | Ignore it for normal evaluation workflows. Install `yival[trainers]` only for approved local fine-tuning. |
| CLI help fails before running a subcommand | The root CLI imports the broad component surface. | First run `python scripts/check_install.py`; then install the missing package or narrow to a programmatic import path that avoids optional components. |

## Config and YAML

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unknown source type` | `dataset.source_type` is not `dataset`, `machine_generated`, or `user_input`. | Use one of those exact strings. |
| Empty data iterator | `dataset.file_path` or `dataset.reader` missing for `source_type: dataset`, or generator id missing for `machine_generated`. | Fill `file_path` + `reader`, or use `data_generators` under `machine_generated`. |
| CSV rows skipped | `CSVReader` skips rows with missing values and logs warnings. | Ensure every cell in each row is non-empty; keep `expected_result_column` populated when configured. |
| `Unsupported value_type` in variations | `WrapperVariation.value_type` is not one of `str`, `int`, `float`, `bool`, or a registered class. | Use supported primitive names or register a class in YiVal's class registry. |
| AHP selected result seems inverted | `criteria_maximization` controls sign; omitted criteria default to maximize. | Set `criteria_maximization` explicitly for latency and token usage (`false` when lower is better). |

## Custom functions and wrappers

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TypeError: got an unexpected keyword argument` | CSV/HF row keys do not match custom function parameters. | Make dataset columns match the function signature excluding `state`. |
| `StringWrapper` returns the original template instead of a variation | `ExperimentState` is inactive, the wrapper `name` does not match a variation name, or no variations were initialized. | Pass `state` into `StringWrapper(..., state=state)` and ensure YAML `variations[].name` matches. |
| `KeyError`-like template placeholders stay unresolved | `StringWrapper.__str__` catches missing keys and returns the variation unchanged. | Ensure `variables={...}` contains every `{placeholder}` needed by the active variation. |

## Provider and network workflows

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| OpenAI generator/evaluator fails | Missing `OPENAI_API_KEY`, incompatible OpenAI SDK version, or rate limits. | Use `openai==0.27.10` style environment, set credentials, reduce examples/variations, or run offline tests first. |
| Hugging Face dataset reader returns errors | URL, network, or dataset-server response changed. | Verify the full `https://datasets-server.huggingface.co/rows?...` URL manually and keep `example_limit` small. |
| Document generator fails on file/drive source | `unstructured`, OCR, Google Drive, or auth dependency issue. | Start with `source: text`; use file/drive only after the local loader dependencies and credentials are ready. |
| AlpacaEval evaluator fails | External annotator config/model access not available. | Treat as a provider-backed evaluator; use string/BERTScore/ROUGE or OpenAI prompt evaluator for smaller tests. |

## UI and output behavior

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `yival run` appears to hang after completion | Dash display thread is running because `display=True` by default. | Programmatically call `ExperimentRunner.run(display=False, output_path=...)`, or close the Dash server when finished. |
| Port conflict | Dash chooses a port starting near 8074, then increments until available. | Check the printed port or use a clean environment. |
| No output pickle found at exact `output_path` | YiVal appends the config index to the stem. | Look for `<stem>_0.pkl`, `<stem>_1.pkl`, etc. |
| `ngrok` starts unexpectedly | Environment variable `ngrok` is set. | Unset `ngrok` unless a public tunnel is intentional. |

## Safety notes

- `python_validation_evaluator` calls `exec(raw_output)`. Use only in a sandbox with trusted, tiny outputs.
- Do not run demo scripts that call external APIs or generate code unless the user approves credentials, network use, and potential billing.
- Fine-tuning workflows can download models, allocate GPUs, or create external jobs. Treat them as explicit opt-in tasks, not default YiVal use.
