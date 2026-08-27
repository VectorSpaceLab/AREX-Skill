# Repo Provenance

## Source snapshot

- Repository family: MobileAgent / GUI-Owl / UI-S1 monorepo.
- Source commit: `11cea575561fb7800b5fb6b6cafa56f7a91de11f`.
- Branch: `main`.
- Exact tag: none detected.
- Remote URL: omitted-private-or-unknown.
- Working tree state at construction: dirty only because repo-local generated skill artifacts/logs were being written under `skills/`.
- Canonical generated skill id: `mobile-agent`.
- Import policy at construction: user requested `not import`; no managed repo-skills import was performed.

## Package/version signals

- `Mobile-Agent-v3.5/android_world_v3.5/pyproject.toml`: distribution `android_world`, version `0.1.0`.
- `Mobile-Agent-v3/android_world_v3/pyproject.toml`: distribution `android_world`, version `0.1.0`.
- `UI-S1/setup.py` / `UI-S1/verl/version/version`: distribution `verl`, version `0.4.0.dev`.
- Most Mobile-Agent, PC-Agent, GUI-Critic, browser, and benchmark workflows are script-oriented rather than one unified installable package.

## Evidence paths used

Root and family documentation:

- `README.md`
- `Mobile-Agent-v3.5/README.md`
- `Mobile-Agent-v3/README.md`
- `Mobile-Agent-E/README.md`
- `PC-Agent/README.md`
- `UI-S1/README.md`
- `GUI-Critic-R1/README.md`

Current GUI-Owl / v3.5 workflows:

- `Mobile-Agent-v3.5/mobile_use/run_gui_owl_1_5_for_mobile.py`
- `Mobile-Agent-v3.5/mobile_use/utils.py`
- `Mobile-Agent-v3.5/computer_use/run_gui_owl_1_5_for_pc.py`
- `Mobile-Agent-v3.5/computer_use/utils.py`
- `Mobile-Agent-v3.5/browser_use/run_gui_owl_1_5_for_web.py`
- `Mobile-Agent-v3.5/browser_use/agent.py`
- `Mobile-Agent-v3.5/browser_use/requirements.txt`

Benchmark and evaluation workflows:

- `Mobile-Agent-v3.5/android_world_v3.5/run_ma35.py`
- `Mobile-Agent-v3.5/android_world_v3.5/README.md`
- `Mobile-Agent-v3/android_world_v3/run_ma3.py`
- `Mobile-Agent-v3/os_world_v3/run_multienv_mobileagent_v3.py`
- `Mobile-Agent-v3/os_world_v3/run_multienv_owl.py`
- `Mobile-Agent-v3.5/web_benchmark/main_for_eval.py`
- `Mobile-Agent-v3.5/grounding_and_kb/eval_grounding_benchmarks.py`
- `Mobile-Agent-v3.5/grounding_and_kb/eval_gui_knowledge_benchmark.py`
- `GUI-Critic-R1/test.py`
- `GUI-Critic-R1/statistic.py`

Other workflow families:

- `Mobile-Agent-E/run.py`
- `Mobile-Agent-E/data/custom_tasks_example.json`
- `Mobile-Agent-E/scripts/run_task.sh`
- `Mobile-Agent-E/scripts/run_tasks_evolution.sh`
- `PC-Agent/run.py`
- `PC-Agent/run_v1.py`
- `PC-Agent/config.json`
- `Mobile-Agent-v1/run.py`
- `Mobile-Agent-v1/run_api.py`
- `Mobile-Agent-v2/run.py`
- `Mobile-Agent-v3/mobile_v3/run_mobileagentv3.py`
- `UI-S1/examples/qwen_gui_static_grpo/config/traj_grpo.yaml`
- `UI-S1/scripts/train_example.sh`
- `UI-S1/scripts/model_merger.py`
- `UI-S1/evaluation/eval_qwenvl.py`
- `UI-S1/x/data/agent/json.py`
- `UI-S1/x/qwen/image.py`

## Refresh guidance

Refresh this skill when the upstream checkout changes command-line flags, task JSON schemas, UI-S1/verl training config keys, GUI-Owl action formats, AndroidWorld/OSWorld runner flags, or PC-Agent/Mobile-Agent-E runtime configuration behavior.
