# Extension and Environment Workflows

This reference covers MetaGPT extension workflows and external environment integrations. Treat external API keys, downloads, browser/UI services, Android devices, Minecraft servers, frontend services, datasets, and long LLM optimization/simulation loops as prerequisites or skips.

## Universal Extension Preflight

1. Confirm the installed package can import base MetaGPT and this sub-skill helper can inspect safe surfaces:
   ```bash
   python scripts/optimizer_help_check.py --target all --mode help --json
   ```
2. Confirm LLM configuration before any optimizer or simulation run. AFlow reads named models from `models` in MetaGPT `config2.yaml`; SPO initializes model names through `SPO_LLM.initialize(...)`; CR/SELA use configured MetaGPT LLM access.
3. Confirm optional dependencies per flow instead of installing everything:
   - AFlow/SPO parser help: base package plus extension modules.
   - SPO web UI: `streamlit~=1.42.0`.
   - Android Assistant: ADB, Android emulator/device, CV/OCR/model packages, local screenshot/XML directories on device.
   - Stanford Town: bundled/storage simulation state, optional Generative Agents frontend server, LLM budget.
   - Werewolf: LLM budget; optional vector-store experience dependencies when using experience retrieval.
   - Minecraft: Node.js, Mineflayer bridge, reachable Minecraft service/port, checkpoint directory access, vector-store dependencies.
   - SELA: datasets and runner-specific AutoML dependencies for the selected mode.
4. Use shortest safe checks first. Do not run dataset download scripts, optimizer loops, Android actions, frontend servers, Mineflayer bridges, or simulations unless the user confirms cost and prerequisites.

## AFlow Workflow Optimization

AFlow optimizes code-represented agent workflows with LLM-guided Monte Carlo tree search. This sub-skill bundles only a safe help/import wrapper for the inspected optimizer surfaces; full optimization should use installed Python APIs or a user-owned wrapper after prerequisites are confirmed.

Safe parser check:

```bash
python scripts/optimizer_help_check.py --target aflow --mode help
```

Minimal API run shape after datasets, templates, LLM config, output directory, and cost limits are confirmed:

```python
from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.scripts.optimizer import Optimizer

models = ModelsConfig.default()
optimizer = Optimizer(
    dataset="MATH",
    question_type="math",
    opt_llm_config=models.get("claude-3-5-sonnet-20240620"),
    exec_llm_config=models.get("gpt-4o-mini"),
    operators=["Custom", "ScEnsemble", "Programmer"],
    optimized_path="workspace/aflow",
    sample=4,
    initial_round=1,
    max_rounds=20,
    validation_rounds=5,
    check_convergence=True,
)
optimizer.optimize("Graph")
```

Key optimizer parameters:

| Option | Purpose | Safety note |
| --- | --- | --- |
| `--dataset` | Required dataset; choices are `DROP`, `HotpotQA`, `MATH`, `GSM8K`, `MBPP`, `HumanEval`. | Dataset files must exist locally unless first-time download is explicitly permitted. |
| `--sample` | Number of top rounds/workflows sampled during graph refinement. | Larger values increase LLM/evaluation cost. |
| `--optimized_path` | Root where workflow rounds, prompts, logs, and templates are stored. | Ensure template files such as `workflows/template/operator.py` and `operator.json` exist for custom workspaces. |
| `--initial_round` | First optimization round number. | Round `1` loads the initial graph for evaluation. |
| `--max_rounds` | Maximum graph optimization rounds. | This is the main cost multiplier. |
| `--validation_rounds` | Validation executions per graph evaluation. | More rounds increase dataset/LLM cost. |
| `--if_first_optimize` | When true, example code calls `download(["datasets", "initial_rounds"])`. | Set false unless user approved network downloads. |
| `--opt_model_name` / `--exec_model_name` | Named model configs from `models` in `config2.yaml`. | Missing names raise a model-not-found `ValueError`. |

What a full run does:

1. Loads dataset-specific `ExperimentConfig` with `dataset`, `question_type`, and allowed operators.
2. Looks up optimizer and executor model configs through `ModelsConfig.default().get(...)`.
3. Optionally downloads datasets and initial rounds if `--if_first_optimize true`.
4. Instantiates `metagpt.ext.aflow.scripts.optimizer.Optimizer`.
5. Runs `optimizer.optimize("Graph")`, which loops over graph generation, evaluation, experience updates, and convergence checks.

### AFlow Custom Dataset Path

For a custom dataset, plan code changes rather than a YAML-only change:

1. Add a benchmark class under the AFlow benchmark package that inherits `BaseBenchmark`.
2. Implement:
   - `async evaluate_problem(self, problem: dict, graph: Callable) -> tuple[...]`
   - `calculate_score(self, expected_output, prediction) -> tuple[float, Any]`
   - `get_result_columns(self) -> list[str]`
3. Add the benchmark to `Evaluator.dataset_configs` and update the dataset literal/type choices.
4. Add an experiment mapping equivalent to the example `EXPERIMENT_CONFIGS`, including `question_type` (`math`, `code`, or `qa`) and operator names.
5. Provide local JSONL validation/test files matching `_get_data_path(...)` expectations or adapt that path logic.
6. Ensure `optimized_path/<Dataset>/workflows/template/operator.py` and `operator.json` exist for the selected operators.
7. Run parser/import checks before any full optimization:
   ```bash
   python scripts/optimizer_help_check.py --target aflow --mode import --json
   ```

## SPO Prompt Optimization

SPO optimizes prompts through self-supervised LLM-as-judge loops. This sub-skill bundles a safe parser wrapper; full optimization should use installed Python APIs or a user-owned wrapper after LLM and template prerequisites are confirmed.

Safe parser check:

```bash
python scripts/optimizer_help_check.py --target spo --mode help
```

Template shape under the SPO settings directory:

```yaml
prompt: |
  Create poetry in the requested style and format.
requirements: |
  Use vivid imagery and keep the tone concise.
count: None
qa:
  - question: |
      Write a modern sonnet about climate change
    answer: |
      None
```

Python API shape after LLM prerequisites are confirmed:

```python
from metagpt.ext.spo.components.optimizer import PromptOptimizer
from metagpt.ext.spo.utils.llm_client import SPO_LLM

SPO_LLM.initialize(
    optimize_kwargs={"model": "claude-3-5-sonnet-20240620", "temperature": 0.7},
    evaluate_kwargs={"model": "gpt-4o-mini", "temperature": 0.3},
    execute_kwargs={"model": "gpt-4o-mini", "temperature": 0},
)
optimizer = PromptOptimizer(
    optimized_path="workspace",
    initial_round=1,
    max_rounds=10,
    template="Poem.yaml",
    name="Poem",
)
optimizer.optimize()
```

Result layout:

```text
workspace/
  Project_name/
    prompts/
      results.json
      round_1/answers.txt
      round_1/prompt.txt
      round_2/answers.txt
      round_2/prompt.txt
```

Streamlit UI is optional and requires the Streamlit dependency plus a browser session. Because Streamlit launches from an app script, use a package-provided command or user-owned launcher when available; otherwise prefer the Python API path above.

## Android Assistant

Android Assistant combines `Team`, `AndroidEnv`, and `AndroidAssistant` role logic. It can learn from automatic exploration or manual demonstration, then act using learned operation documents.

Do not run it unless ADB and a safe emulator/device are ready. Safe setup checklist:

1. Confirm the user has installed Android Studio/emulator or connected a test device.
2. Confirm `adb devices` lists the expected `device_id`, commonly `emulator-5554`.
3. Confirm the device has writable screenshot and XML directories, defaulting to `/sdcard/Pictures/Screenshots` and `/sdcard`.
4. Confirm optional CV/model dependencies are available and model downloads are allowed, because `AndroidExtEnv` loads OCR and GroundingDINO-related models.
5. Confirm the task is safe to execute on that app/device and that no private account actions will be performed without explicit authorization.

Reference-only run plan after confirmation:

| Parameter | Example value | Why it matters |
| --- | --- | --- |
| `task_desc` | `Send a test message in a sandbox app` | Natural-language app task. |
| `stage` | `learn` | Choose `learn` for operation-doc creation or `act` for execution. |
| `mode` | `manual` | Use manual demonstration when avoiding autonomous exploration. |
| `app_name` | `Messenger` | Names the app-specific operation documents. |
| `n_round` | `20` | Caps app operation rounds. |
| `device_id` | `emulator-5554` | Must match `adb devices`. |
| `android_screenshot_dir` | `/sdcard/Pictures/Screenshots` | Device-side screenshot path. |
| `android_xml_dir` | `/sdcard` | Device-side UI XML path. |

Important options:

| Option | Values / default | Meaning |
| --- | --- | --- |
| `TASK_DESC` | required | Natural-language phone/app task. |
| `--stage` | `learn` or `act`; default `learn` | Learn operation docs or execute with learned docs. |
| `--mode` | `auto` or `manual`; default `auto` | Automatic exploration or human demonstration during learning. |
| `--app-name` | default `demo` | App label used for operation docs. |
| `--n-round` | default `20` | Max operation rounds. |
| `--refine-doc` | boolean | Refine existing operation docs from latest observations. |
| `--min-dist` | default `30` | Minimum label distance for UI element labeling. |
| `--device-id` | default `emulator-5554` | ADB device id. |

## Stanford Town Simulation

Stanford Town wraps Generative Agents-style town simulation. It requires storage state and often a frontend server if visual interaction is needed.

Safe planning steps:

1. Confirm storage contains a base simulation code such as `base_the_ville_isabella_maria_klaus`.
2. Choose a new `sim_code` output name and keep the run short for smoke tests.
3. Confirm LLM budget; defaults in the example are expensive (`investment=30.0`, `n_round=500`).
4. If docking with a Generative Agents frontend, confirm that frontend storage/temp paths and server lifecycle are managed by the user.

Reference-only run plan after confirmation: use an `idea` such as `Host an open lunch party at 13:00 pm`, an existing `fork_sim_code`, a new `sim_code`, a small `investment` such as `5`, and a short `n_round` such as `10`. Frontend docking is optional. If used, the user must start the frontend service separately and provide a compatible temp storage path.

## Werewolf Game

Werewolf creates a game environment, moderator, special roles, villagers, and werewolves. It can run fully with LLM agents or include a human player.

Reference-only short-run plan after LLM cost confirmation: use low `investment` such as `3`, low `n_round` such as `5`, `shuffle=True` only when randomness is acceptable, `add_human=False` for noninteractive runs, `use_reflection=True` when role reflection is desired, and `use_experience=False` unless vector-store experience prerequisites are ready.

Main toggles:

| Option | Default | Notes |
| --- | --- | --- |
| `investment` | example `20.0` in CLI wrapper | Budget guard; lower for smoke tests. |
| `n_round` | example `100` in CLI wrapper | Main simulation length. |
| `shuffle` | `True` | Randomizes role assignment. |
| `add_human` | `False` | Adds interactive human role assignment. |
| `use_reflection` | `True` | Enables reflective role behavior. |
| `use_experience` | `False` | May touch experience retrieval/vector-store paths. |
| `use_memory_selection` | `False` | Enables memory selection behavior. |
| `new_experience_version` | `""` | Labels new experience records. |

Use environment-level APIs for isolated logic tests instead of full LLM gameplay when possible: `WerewolfExtEnv.init_game_setup(...)`, `step(...)`, `curr_step_instruction()`, `get_players_state(...)`, and role-specific actions.

## CR Code Review Extension

The CR extension performs LLM-assisted patch review and optional code modification.

High-level flow:

1. Build a `unidiff.PatchSet` from a PR patch.
2. Load review `Point` objects with fields such as `id`, `text`, `language`, `file_path`, `start_line`, `end_line`, examples, and detailed guidance.
3. Run `CodeReview.cr_by_points(...)` or `CodeReview.run(...)` to produce JSON comments for Python/Java patches.
4. Optionally run `ModifyCode.run(...)` to generate patch fixes from confirmed comments.

Safety boundaries:

- CR uses LLM calls for review and confirmation; do not run without provider config and user approval.
- Source only supports Python and Java patch review in the inspected code path.
- Generated modification patches should be reviewed before application.

## SELA AutoML Extension

SELA runs tree-search-enhanced LLM AutoML experiments. It is dataset-, dependency-, and LLM-heavy.

Safe parser-only command:

```bash
python -m metagpt.ext.sela.run_experiment --help
```

Example run shapes after dataset and dependency confirmation:

```bash
python -m metagpt.ext.sela.run_experiment --exp_mode mcts --task titanic --rollouts 10
python -m metagpt.ext.sela.run_experiment --exp_mode mcts --task house-prices --rollouts 10 --low_is_better
python -m metagpt.ext.sela.run_experiment --exp_mode rs --task titanic --rs_mode single
```

Important options:

| Option | Values / default | Purpose |
| --- | --- | --- |
| `--exp_mode` | `mcts`, `rs`, `base`, `custom`, `greedy`, `autogluon`, `random`, `autosklearn` | Chooses runner. |
| `--task` | default `titanic` | Dataset/task id. |
| `--rollouts` | default `5` | MCTS rollout count and cost driver. |
| `--role_timeout` | default `1000` | Timeout per simulation role. |
| `--from_scratch` | false | Generate a new insight pool. |
| `--load_tree` | false | Resume an existing tree. |
| `--custom_dataset_dir` | optional | Switches to custom MLE-style task setup. |
| `--low_is_better` | false | Regression/lower-metric mode. |

Config files include:

- `datasets.yaml`: task prompts, metrics, target columns.
- `data.yaml`: `datasets_dir`, `work_dir`, and `role_dir`.
- MetaGPT `config2.yaml`: LLM settings.

## Minecraft Environment

Minecraft integrates an external Mineflayer bridge and HTTP server with `MinecraftExtEnv`/`MinecraftEnv`. Treat it as unsafe to start automatically.

Preconditions:

1. Node.js and Mineflayer dependencies are installed.
2. The Minecraft server/port is under user control.
3. Checkpoint directories can be created and persisted.
4. Vector-store dependencies are available when resuming skills or QA caches.
5. The user approves process startup and network/local port usage.

Core write APIs include `check_process`, `_reset`, `_step`, `pause`, `unpause`, and `close`. `_step(code, programs)` executes JavaScript-like action code through the bridge and must never be run on an untrusted server or without explicit confirmation.

## Custom Environment Integration

Use the environment API pattern when a user wants a new external environment or a safe test harness for one.

Minimal pattern:

```python
from typing import Any, Optional
from metagpt.base.base_env_space import BaseEnvAction, BaseEnvObsParams
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.environment.base_env import Environment, mark_as_readable, mark_as_writeable

class CounterEnv(Environment):
    value: int = 0

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None):
        self.value = 0
        return {"value": self.value}, {}

    def observe(self, obs_params: Optional[BaseEnvObsParams] = None):
        return {"value": self.value}

    def step(self, action: BaseEnvAction):
        return {"value": self.value}, 1.0, False, False, {}

    @mark_as_readable
    def read_value(self):
        return self.value

    @mark_as_writeable
    def add(self, amount: int):
        self.value += amount
        return self.value

# async context
# await env.write_thru_api(EnvAPIAbstract(api_name="add", kwargs={"amount": 3}))
# await env.read_from_api("read_value")
```

Design rules:

- Implement `reset`, `observe`, and `step` even if the external API methods are the main access path.
- Decorate every public read/write API so agents can discover it with `get_all_available_apis(mode="read")` and `mode="write"`.
- Use `EnvAPIAbstract(api_name="...", kwargs={...})` for parameterized calls.
- Keep destructive external actions behind explicit user confirmation.
- Model action/observation spaces with concrete env-space classes when building a reusable environment.
