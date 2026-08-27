---
name: benchmarks-and-evaluation
description: "Prepare and troubleshoot MobileAgent GUI benchmark and evaluation
  workflows: AndroidWorld, OSWorld, WebArena/WebVoyager/VisualWebArena,
  grounding, GUI knowledge, and GUI-Critic-R1."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Benchmarks and Evaluation

Use this sub-skill when a user asks about evaluation, benchmark task suites, trajectories, score/judge models, GUI-Critic-R1 datasets, AndroidWorld, OSWorld, WebArena, WebVoyager, VisualWebArena, grounding benchmarks, or GUI knowledge benchmarks.

This route builds and validates evaluation commands/data safely. Live benchmark execution still requires emulators, VMs, browsers, datasets, checkpoints, APIs, and explicit user authorization.

## Route map

| Prompt signal | Workflow | Read / run |
|---|---|---|
| AndroidWorld, MiniWoB, emulator ports, `suite_family`, `run_ma35.py`, `run_ma3.py` | AndroidWorld/MiniWoB | [`references/androidworld-osworld.md`](references/androidworld-osworld.md), `scripts/build_androidworld_command.py` |
| OSWorld, VM path, domains, parallel environments, `run_multienv_*` | OSWorld | [`references/androidworld-osworld.md`](references/androidworld-osworld.md), `scripts/build_osworld_command.py` |
| WebArena, WebVoyager, VisualWebArena, web benchmark task id, judge, `main_for_eval.py` | Web benchmarks | [`references/web-benchmarks.md`](references/web-benchmarks.md), `scripts/build_web_benchmark_command.py` |
| GUI-Critic-R1 JSONL, score tags, critic labels, hard-coded key risk | GUI-Critic-R1 | [`references/grounding-and-gui-critic.md`](references/grounding-and-gui-critic.md), `scripts/validate_gui_critic_dataset.py` |
| Grounding benchmark, GUI knowledge benchmark, `model_path`, `ds_path`, `eval_benchmark_type` | Local VLM checkpoint evaluation | [`references/grounding-and-gui-critic.md`](references/grounding-and-gui-critic.md), `scripts/build_grounding_eval_command.py` |
| Emulators, browsers, checkpoints, APIs, score interpretation, skip policy | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe usage pattern

1. Identify the benchmark family and required backend/service.
2. Build a command with the relevant script. Example AndroidWorld:

```bash
python sub-skills/benchmarks-and-evaluation/scripts/build_androidworld_command.py \
  --version v35 \
  --model-env GUI_OWL_MODEL \
  --api-key-env GUI_OWL_API_KEY \
  --base-url-env GUI_OWL_BASE_URL \
  --grpc-port 8554 \
  --console-port 5554 \
  --tasks ContactsAddContact,ClockStopWatchRunning \
  --n-task-combinations 2 \
  --fixed-task-seed \
  --traj-output-path runs/androidworld-traj
```

3. For data/schema tasks, validate locally before any inference. Example GUI-Critic:

```bash
python sub-skills/benchmarks-and-evaluation/scripts/validate_gui_critic_dataset.py --jsonl sample.jsonl
```

4. Report live prerequisites separately from safe checks. Do not claim scores from generated templates.

## Boundaries

- Ordinary current v3.5 mobile/desktop/browser task execution belongs to [`../current-gui-owl/SKILL.md`](../current-gui-owl/SKILL.md).
- Mobile-Agent-E task evolution belongs to [`../mobile-agent-e/SKILL.md`](../mobile-agent-e/SKILL.md).
- UI-S1 training/eval JSONL and checkpoint merge belongs to [`../ui-s1-training/SKILL.md`](../ui-s1-training/SKILL.md).
- Generic LLM benchmark harnesses unrelated to GUI agents are outside this skill.

## Verification stance

Command builders and validators are safe CPU checks. Live benchmark results require the real backend and should be recorded as live evidence only when actually run.
