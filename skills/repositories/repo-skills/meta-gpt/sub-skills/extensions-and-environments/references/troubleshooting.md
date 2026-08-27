# Extension and Environment Troubleshooting

Use this matrix to diagnose extension/environment issues while keeping safe validation separate from full runs.

## Safe Triage Order

1. Run the helper in import mode:
   ```bash
   python scripts/optimizer_help_check.py --target all --mode import --json
   ```
2. Run the helper in help mode:
   ```bash
   python scripts/optimizer_help_check.py --target all --mode help --json
   ```
3. If a full run is requested, confirm credentials, datasets/templates, output directories, optional dependencies, external services, and a cost/round cap.
4. Prefer direct module/API checks over full simulations. For Android, Stanford Town, werewolf, and Minecraft, use mocks or setup checklists when hardware/services are absent.

## AFlow Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| `the following arguments are required: --dataset` | AFlow CLI requires `--dataset`. | Choose one of `DROP`, `HotpotQA`, `MATH`, `GSM8K`, `MBPP`, `HumanEval`. |
| `invalid choice` for dataset | Dataset name not in `EXPERIMENT_CONFIGS`. | Use a supported dataset or implement a custom benchmark and mapping. |
| `The optimization model '...' was not found` | `--opt_model_name` missing from `models` config. | Add a named model config or pass an existing model name. Do not paste keys into skill files. |
| `The execution model '...' was not found` | `--exec_model_name` missing from `models` config. | Add/pass an existing named model config. |
| File not found for `*_validate.jsonl` or `*_test.jsonl` | Dataset files missing. | If network download is allowed, use the project’s data acquisition path; otherwise ask the user to provide local JSONL files. |
| Unexpected dataset download on first run | `--if_first_optimize` default is true in example parser. | Use `--if_first_optimize false` unless user explicitly approves downloads. |
| Missing `operator.json` or `operator.py` under `workflows/template` | Optimized workspace lacks templates. | Copy/adapt operator template files into the chosen workspace before optimizing. |
| `Unsupported dataset: ...` from evaluator | `Evaluator.dataset_configs` lacks custom dataset entry. | Add a `BaseBenchmark` subclass and dataset mapping. |
| Custom benchmark returns malformed results | `get_result_columns()` does not match tuple returned by `evaluate_problem`. | Align result tuple columns and include a `score` column for aggregation. |
| Run is very slow or expensive | `max_rounds`, `validation_rounds`, and dataset size drive cost. | Lower `--max_rounds`, `--validation_rounds`, and dataset subset logic for smoke tests. |
| Repeated poor graph modifications | Experience/check logic or operator descriptions are insufficient. | Review `operator.json`, prompt template, log data, and dataset question type. |

AFlow full optimization is not a parser check. It constructs LLM clients, evaluates datasets, writes graph rounds, and can download data.

## SPO Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| Template file not found or empty template UI | `--template` does not exist in SPO settings. | Create a YAML template with `prompt`, `requirements`, `count`, and `qa`. |
| YAML parser error | Invalid indentation, tabs, or malformed block strings. | Validate YAML before optimizing; keep multiline values under `|`. |
| Missing `qa`, `question`, or `answer` fields | Template schema incomplete. | Add a list of QA examples with both fields. |
| `SPO_LLM` not initialized | Optimizer constructed before `SPO_LLM.initialize(...)`. | Initialize optimize/evaluate/execute model kwargs first. |
| Provider/model authentication failure | LLM model names or credentials are not configured. | Use root MetaGPT config guidance; never embed keys in generated files. |
| Optimization never improves | Requirements/QA examples are too vague or judge cannot distinguish success. | Add concrete QA examples and measurable requirements. |
| Output files missing under workspace | `optimized_path` or `name` points somewhere unexpected, or run failed before first round. | Check `<workspace>/<name>/prompts/round_*`. |
| `streamlit` import/command missing | Optional UI dependency not installed. | Install Streamlit only if user wants web UI, or use CLI/Python API. |

SPO optimizer rounds call execution, evaluation, and optimization LLMs. Keep `--max-rounds` low until the template is validated.

## Android Assistant Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| `adb: command not found` | Android Debug Bridge is not installed or not on PATH. | Ask user to install Android platform tools; do not proceed with device actions. |
| `device-id: ... not found` | `AndroidExtEnv` did not find the requested id in `adb devices`. | Ask user to start emulator/connect device or pass the correct `--device-id`. |
| ADB returns no devices or unauthorized | Emulator/device not running, USB debugging not authorized, or driver issue. | Have user unlock/authorize device and rerun `adb devices`. |
| Screenshot/XML pull fails | Device directories missing or permission issue. | Confirm/create screenshot/XML dirs on device and use writable local save dirs. |
| `uiautomator dump` fails | App/device state blocks XML dump or Android version issue. | Fall back to screenshot-only setup checklist; avoid blind taps. |
| OCR/GroundingDINO/model import or download failure | Optional CV dependencies/model weights missing or network blocked. | Ask whether model downloads are allowed; install only needed packages. |
| TensorFlow/Torch/model package conflicts | CV stack versions incompatible. | Use a dedicated environment for Android Assistant; do not alter unrelated project envs without approval. |
| Manual mode waits for input | `--mode manual` requires terminal responses. | Inform user it is interactive and pause for their operation. |
| Real app side effects | Assistant taps/types on a live device. | Use sandbox app/account and explicit task boundaries; do not run sensitive actions. |

When no emulator/device is available, provide a setup checklist and stop after parser/import checks.

## Stanford Town Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| Missing `fork_sim_code` storage | Base simulation directory not present. | Ask user to provide/copy a compatible base simulation directory. |
| Missing `meta.json` or persona memory files | Storage state incomplete. | Validate storage tree before running. |
| Frontend does not show updates | Temp storage path is not docked to frontend server. | Confirm frontend service storage/temp paths and server status. |
| Very long or costly run | Defaults are high (`n_round=500`, investment around `30`). | Reduce `--n_round` and `--investment` for smoke tests. |
| Maze asset assertion/import failure | Required Stanford Town static assets are missing. | Verify asset package/storage before running. |
| Persona behavior seems stuck | LLM config, memory state, or frontend sync issue. | Check logs, reduce rounds, and test environment observation separately. |

Do not start external frontend services or long simulation loops without explicit approval.

## Werewolf Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| Game consumes too many LLM calls | High `n_round`, many players, reflection/experience enabled. | Lower `n_round` and investment; disable experience for smoke tests. |
| Human role blocks execution | `add_human=True` requires interactive input. | Ask user whether interactive play is intended. |
| Experience retrieval import/vector errors | `use_experience` needs vector-store/RAG dependencies and stored experiences. | Disable `use_experience` or install/configure the needed store. |
| Role action ignored | Werewolf environment guards by role type and step index. | Check current `step_idx`, role profile, and living player state. |
| Vote/hunt result unexpected | Step order or living-player state does not match action. | Use `curr_step_instruction()` and `get_players_state(...)` to inspect state. |
| Random roles make debugging hard | `shuffle=True`. | Set `shuffle=False` for deterministic role order. |

For deterministic debugging, create a `WerewolfExtEnv(players_state=...)` and call environment APIs directly instead of running full LLM roles.

## Minecraft Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| `node` not found | Node.js missing. | Ask user to install Node.js before Mineflayer bridge. |
| Mineflayer process fails to start | Missing Node dependencies or bridge script issue. | Check bridge dependencies and logs; do not retry indefinitely. |
| HTTP `/start` or `/step` fails | Server not running, wrong port, timeout, or Minecraft target unavailable. | Confirm `server_host`, `server_port`, `mc_port`, and server lifecycle. |
| `Environment has not been reset yet` | `_step` called before `_reset`. | Call `_reset` with safe options after explicit approval. |
| Inventory option assertion | Inventory specified with non-`hard` reset mode. | Use `options={"mode": "hard", "inventory": {...}}` or omit inventory. |
| Vectordb count assertion on resume | Chroma skill/QA cache is out of sync with JSON files. | Reset/repair the checkpoint vector DB after backing up user data. |
| Executing untrusted code risk | `_step(code, programs)` executes code via external bridge. | Never run generated/untrusted code without user approval and a sandboxed server. |

## CR Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| `Only code reviews for Python and Java languages are supported.` | Patch files are not `.py` or `.java`. | Route to another review method or add language support. |
| JSON parse error from review output | LLM did not return valid JSON. | Retry with stricter prompt or validate/repair manually before confirmation. |
| Empty comments despite defects | Points too broad, patch filtering removed lines, or confirmation rejected comments. | Inspect cleaned patch, point details, and intermediate `.log` output. |
| Generated patch has bad hunk headers | LLM modification output changed diff structure. | Treat output as a candidate; review and regenerate rather than applying blindly. |
| Review is expensive/slow | Points are chunked and reviewed with LLM calls. | Reduce points or patch scope for smoke checks. |

## SELA Failures

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| Dataset directory missing | `data.yaml` has placeholder `datasets_dir` or datasets not prepared. | Ask user to provide/download datasets; do not download without approval. |
| AutoGluon/AutoSklearn import errors | Selected runner dependency not installed. | Install only the dependency for the selected `--exp_mode`. |
| MLE custom dataset task not recognized | `--custom_dataset_dir` layout or metadata unsupported. | Validate custom dataset directory and task id mapping. |
| Run exceeds expected time | `--rollouts`, `--role_timeout`, and `--max_depth` too high. | Lower rollouts/depth or use parser-only check. |
| Wrong metric direction | Missing `--low_is_better` for regression/lower-is-better tasks. | Set metric direction explicitly. |
| Resume loads stale tree | `--load_tree` points to incompatible prior state. | Start without `--load_tree` or clean/rename experiment state after user approval. |

## Environment API Misuse

| Symptom | Likely cause | Fix / safe response |
| --- | --- | --- |
| `KeyError: api_name: ... not found` | API was not decorated or name is wrong. | Check `env.get_all_available_apis(mode="read"/"write")`. |
| `ValueError: None not exists` | `read_from_api`/`write_thru_api` received empty API name or missing registry function. | Pass a non-empty registered `api_name`. |
| Parameter mismatch | `EnvAPIAbstract.args`/`kwargs` do not match function signature. | Prefer `kwargs` and inspect registry schema from `get_all_available_apis`. |
| `observe`/`step` returns `None` unexpectedly | Base `Environment` methods are stubs. | Use a concrete env subclass or implement `reset`, `observe`, and `step`. |
| Unsupported action space | Action enum/value does not match concrete env-space class. | Use the correct `EnvAction` and `EnvActionType` for Android, Stanford Town, werewolf, or Minecraft. |
| Message not delivered to roles | `send_to` does not match environment addresses. | Inspect roles, addresses, and `publish_message` behavior for the chosen env. |

## Import Failures by Optional Surface

| Missing module / package family | Likely surface | Response |
| --- | --- | --- |
| `streamlit` | SPO UI | Use CLI or install Streamlit for web UI. |
| `opencv-python`, `pyshine`, OCR/model packages, `clip`, `modelscope` | Android Assistant | Install Android/CV dependencies only if device flow is requested. |
| `unidiff` | CR patch review | Install CR dependency before review. |
| AutoML libraries | SELA runner modes | Install runner-specific dependencies. |
| Chroma/LlamaIndex vector store packages | Minecraft resume, werewolf experience, RAG-backed experience retrieval | Disable experience/resume or install vector-store dependencies. |
| Node/Mineflayer dependencies | Minecraft | Prepare Node bridge environment before starting processes. |

## When to Stop and Ask

Stop after safe checks and ask for user confirmation if the next step would:

- Spend LLM credits or run many optimizer/simulation rounds.
- Download datasets, model weights, browser binaries, or external assets.
- Start Android, frontend, Mineflayer, browser, or server processes.
- Act on a real device, app, account, or external game/server.
- Execute generated code or apply LLM-generated patches.
