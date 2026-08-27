# Extension Configuration and Prerequisites

Use this reference to decide whether an extension request is safe to run, should be limited to parser/import checks, or must be handled as a setup plan.

## LLM Configuration

Most extension workflows eventually call configured LLMs.

| Flow | LLM config source | Required before full run |
| --- | --- | --- |
| AFlow | Named entries from `models` in MetaGPT `config2.yaml`, loaded with `ModelsConfig.default().get(name)`. | `--opt_model_name` and `--exec_model_name` must exist in `models`. |
| SPO | `SPO_LLM.initialize(...)` receives model names and temperatures. | Optimize/evaluate/execute model names must be supported by the configured provider. |
| Android Assistant | MetaGPT global `config2` plus team/role LLM calls. | Provider credentials and budget for multi-round app learning/acting. |
| Stanford Town | MetaGPT role/action LLM calls. | Provider credentials and budget for every persona/round. |
| Werewolf | MetaGPT role/action LLM calls. | Provider credentials and budget for each player/round. |
| CR | `Action.llm` through MetaGPT config. | Provider credentials for review and confirmation calls. |
| SELA | MetaGPT LLM config, plus selected runner dependencies. | Provider credentials and budget for experiments/rollouts. |
| Minecraft | MetaGPT LLM roles plus Mineflayer service. | Provider credentials when agents generate/critique code. |

Never store API keys inside generated skill files, scripts, examples, or public references. Ask the user to configure their normal MetaGPT config when credentials are missing.

## Safe Validation Modes

| Validation | Safe by default? | What it checks | What it avoids |
| --- | --- | --- | --- |
| `python scripts/optimizer_help_check.py --target all --mode help --json` | Yes | Captures bundled AFlow/SPO argparse help text without importing optimizer modules. | No module imports, dataset downloads, optimizer construction, or LLM calls. |
| `python scripts/optimizer_help_check.py --target all --mode import --json` | Yes | Module availability for AFlow/SPO examples and core optimizer modules. | No CLI execution, no downloads, no LLM calls. |
| Bundled helper `--target aflow --mode help` | Yes | AFlow argparse help through the copied safe wrapper. | Does not enter optimizer construction or download path. |
| Bundled helper `--target spo --mode help` | Yes | SPO argparse help through the copied safe wrapper. | Does not initialize `SPO_LLM` or run optimization. |
| Installed package parser help for SELA | Usually safe | SELA argparse help when the installed package exposes it. | Does not create runners or datasets. |

If importing an extension module triggers optional dependency errors, report the missing module and recommend installing only the needed optional dependency group or package for the requested path.

## AFlow Configuration

AFlow example config file shape:

```yaml
models:
  "<model_name>":
    api_type: "openai"
    base_url: "<your base url>"
    api_key: "<your api key>"
    temperature: 0
CALC_USAGE: True
```

AFlow CLI options and default considerations:

| Setting | Example/default | Configure when |
| --- | --- | --- |
| `--dataset` | required; `MATH` for math examples | Choose one of the supported datasets or implement a custom benchmark path. |
| `--sample` | `4` | Increase only when more exploration is worth added cost. |
| `optimized_path` | user workspace such as `workspace/aflow` | Prefer a workspace/output directory controlled by the user. |
| `--initial_round` | `1` | Use when resuming or organizing rounds. |
| `--max_rounds` | `20` | Main cost cap; lower for smoke experiments. |
| `--check_convergence` | `True` in parser default | Use early stop if convergence checks are desired. |
| `--validation_rounds` | `5` | Cost/evaluation quality trade-off. |
| `--if_first_optimize` | `True` in parser default | Set `false` unless dataset/initial-round downloads are approved. |
| `--opt_model_name` | `claude-3-5-sonnet-20240620` | Must match a named model config. |
| `--exec_model_name` | `gpt-4o-mini` | Must match a named model config. |

Dataset files are expected by the AFlow evaluator as `<dataset>_validate.jsonl` and `_test.jsonl` for the selected dataset path. Full reproduction may require downloading paper datasets and initial workflow rounds; do not initiate those downloads without explicit approval.

AFlow optimized workspace must include or generate:

```text
<optimized_path>/<Dataset>/
  workflows/
    template/operator.py
    template/operator.json
    round_1/graph.py
    round_1/prompt.py
    round_2/...
```

Missing template/operator files usually cause file-not-found errors during graph optimization.

## SPO Configuration

SPO example config includes both a default `llm` and named `models` entries:

```yaml
llm:
  api_type: "openai"
  model: "gpt-4o-mini"
  base_url: "<your base url>"
  api_key: "<your api key>"
  temperature: 0
models:
  "gpt-4o-mini":
    api_type: "openai"
    base_url: "<your base url>"
    api_key: "<your api key>"
    temperature: 0
```

Template YAML requirements:

| Field | Required? | Notes |
| --- | --- | --- |
| `prompt` | Yes | Initial prompt text. |
| `requirements` | Yes | Optimization target; may be `None` text but should be intentional. |
| `count` | Yes | Number-like target or `None`. |
| `qa` | Yes | List of examples with `question` and `answer`. |

SPO CLI options:

| Setting | Default | Notes |
| --- | --- | --- |
| `--workspace` | `workspace` | Output root. Results go under `<workspace>/<name>/prompts`. |
| `--initial-round` | `1` | Starting round. |
| `--max-rounds` | `10` | Cost cap. |
| `--template` | `Poem.yaml` | Template file name. |
| `--name` | `Poem` | Project/output directory name. |
| `--opt-model` / `--opt-temp` | `claude-3-5-sonnet-20240620` / `0.7` | Optimizer LLM settings. |
| `--eval-model` / `--eval-temp` | `gpt-4o-mini` / `0.3` | Judge/evaluation settings. |
| `--exec-model` / `--exec-temp` | `gpt-4o-mini` / `0` | Prompt execution settings. |

SPO Streamlit UI prerequisites:

- Install `streamlit~=1.42.0` only if the user wants a web UI.
- Browser/UI access and long-running process approval are required.
- The UI reads/writes templates under the SPO settings directory and writes optimization results to the selected workspace.

## Android Assistant Prerequisites

Do not run Android Assistant automatically on an unknown machine. Ask for or verify:

| Prerequisite | Why it matters | Safe check |
| --- | --- | --- |
| ADB installed | All device actions use `adb`. | `adb devices` after user approval. |
| Emulator/device available | `AndroidExtEnv` validates `device_id` and sends real actions. | Confirm expected id such as `emulator-5554`. |
| Device paths exist/writable | Screenshots and XML dumps are saved on device. | Confirm `/sdcard/Pictures/Screenshots` and `/sdcard` or user-provided paths. |
| CV/OCR/model dependencies | `AndroidExtEnv` loads OCR detection/recognition and GroundingDINO-related model weights. | Import check or install only requested dependencies; model downloads need approval. |
| Safe app/test account | Assistant can tap/type real UI. | Ask for a sandbox app/account and task boundaries. |
| LLM credentials/budget | Learning/acting uses agent roles. | Use root config guidance before runs. |

Android Assistant CLI defaults include `stage=learn`, `mode=auto`, `n_round=20`, `investment=5.0`, `min_dist=30`, `device_id=emulator-5554`, screenshot dir `/sdcard/Pictures/Screenshots`, and XML dir `/sdcard`.

## Stanford Town Prerequisites

| Requirement | Notes |
| --- | --- |
| Simulation storage | `fork_sim_code` must name an existing base simulation directory, and `sim_code` names the new copied run. |
| Optional frontend temp storage | Needed only when docking with Generative Agents frontend. |
| Maze/static assets | Required by environment and roles. |
| LLM budget | Example defaults are expensive (`investment=30.0`, `n_round=500`). Use lower values for smoke tests. |
| Frontend server | If visual simulation is requested, user starts the frontend server separately. |

Run with short bounds only after approval, for example `--investment 5 --n_round 10`.

## Werewolf Prerequisites

| Requirement | Notes |
| --- | --- |
| LLM config | Full role gameplay uses LLM calls every round. |
| Budget and rounds | Use `investment` and `n_round` as explicit caps. |
| Human interaction | `add_human=True` requires interactive terminal input. |
| Experience retrieval | `use_experience` and memory selection may require vector-store dependencies and existing experience data. |
| Randomness | `shuffle=True` randomizes role assignments; set false when deterministic setup matters. |

For logic-only debugging, prefer direct `WerewolfExtEnv` unit-style setup instead of full game execution.

## Minecraft Prerequisites

| Requirement | Notes |
| --- | --- |
| Node.js | Mineflayer bridge is launched with `node`. |
| Mineflayer dependencies | The bridge entrypoint lives under the installed Minecraft environment module. |
| Minecraft server/port | `set_mc_port(...)` and bridge `/start` need a reachable controlled server. |
| Local HTTP port | Default bridge server URL is `http://127.0.0.1:3000`. |
| Checkpoint directory | Curriculum/action/skill JSON and vector DB directories are created and read on resume. |
| Vector-store dependencies | `ChromaVectorStore` is used for skills and QA cache. |
| User approval | `_step(code, programs)` executes code in the external environment. |

Never run Mineflayer or `_step` without explicit process/network approval and a trusted target environment.

## CR Prerequisites

| Requirement | Notes |
| --- | --- |
| `unidiff` | Required to parse patch sets. |
| Review points | `Point` objects must include language and detailed examples/standards. |
| Supported languages | Inspected review path handles `.py` and `.java` patches. |
| LLM config | Review, confirmation, and modification all call LLMs. |
| Output directory | Review logs and final JSON comments are written to provided output paths. |

Treat generated modifications as candidate patches, not automatically applied changes.

## SELA Prerequisites

SELA config files:

```yaml
# data.yaml
datasets_dir: "path/to/datasets"
work_dir: user/workspace
role_dir: storage/SELA
```

Required decisions:

| Decision | Options / notes |
| --- | --- |
| Experiment mode | `mcts`, `greedy`, `random`, `rs`, `base`, `custom`, `autogluon`, `autosklearn`. |
| Dataset/task | Built-in task such as `titanic`, `house-prices`, or `--custom_dataset_dir`. |
| Metric direction | `--low_is_better` for regression/lower-is-better tasks. |
| Search budget | `--rollouts`, `--max_depth`, `--role_timeout`. |
| Resume behavior | `--load_tree` for interrupted MCTS runs. |
| Dataset acquisition | Download or prepare datasets only after user approval. |

Optional runner dependencies vary by mode. Do not install AutoGluon/AutoSklearn or download datasets unless the requested experiment requires them and the user approves.

## Skip and Ask Conditions

Ask the user before proceeding when any of these are true:

- A command will download datasets, models, browser binaries, Android assets, or other network resources.
- A command will spend LLM credits for optimization, review, simulation, or gameplay.
- A command will start a server, frontend, Mineflayer bridge, Android emulator, or browser UI.
- A command will operate on a real Android app/account/device.
- A command will execute generated code in Minecraft or another external environment.
- Required datasets, templates, devices, credentials, or service endpoints are missing.

When prerequisites are missing, produce a setup checklist and run only parser/import checks that cannot mutate external state.
