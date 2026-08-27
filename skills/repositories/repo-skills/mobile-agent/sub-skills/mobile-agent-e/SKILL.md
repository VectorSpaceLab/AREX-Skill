---
name: mobile-agent-e
description: "Use Mobile-Agent-E individual and self-evolution Android
  workflows, task-list JSON, persistent tips, shortcuts, and repeated-action
  troubleshooting safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Mobile-Agent-E

Use this sub-skill for Mobile-Agent-E, especially individual vs evolution mode, task-list JSON, persistent task memory, specified tips/shortcuts, repeated-action stopping, and Mobile-Eval-E-style task files.

## Route map

| Prompt signal | Workflow | Read / run |
|---|---|---|
| Single Android task with Mobile-Agent-E | Individual mode | [`references/task-memory-and-evolution.md`](references/task-memory-and-evolution.md), `scripts/build_mobile_agent_e_command.py --instruction ...` |
| Multi-task list, `tasks_json`, evolution setting, persistent tips/shortcuts | Evolution mode | [`references/task-memory-and-evolution.md`](references/task-memory-and-evolution.md), `scripts/validate_mobile_agent_e_tasks.py`, command builder |
| Custom task JSON, `length`, `scenario`, `apps`, `type` | Data format | [`references/data-formats.md`](references/data-formats.md), validator script |
| Repeated actions, early stop, stale memory, task logs | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe workflow

1. Validate a task list before live runs:

```bash
python sub-skills/mobile-agent-e/scripts/validate_mobile_agent_e_tasks.py --tasks-json tasks.json
```

2. Build an individual command:

```bash
python sub-skills/mobile-agent-e/scripts/build_mobile_agent_e_command.py \
  --instruction "Open Notes and write a joke" \
  --log-root private-logs/mobile-agent-e \
  --run-name notes-smoke
```

3. Build an evolution command:

```bash
python sub-skills/mobile-agent-e/scripts/build_mobile_agent_e_command.py \
  --tasks-json tasks.json \
  --setting evolution \
  --log-root private-logs/mobile-agent-e \
  --run-name two-task-evolution
```

4. Before running the printed command, verify ADB/device authorization, model/perception configuration in the runtime checkout, and private log directory policy.

## Important facts

- `run.py` requires exactly one of `--instruction` or `--tasks_json`.
- `--setting` is either `individual` or `evolution`.
- Evolution mode creates persistent `persistent_tips.txt` and `persistent_shortcuts.json` under `log_root/run_name`, optionally seeded from `--specified_tips_path` and `--specified_shortcuts_path`.
- Early-stop knobs include `--max_consecutive_failures` and `--max_repetitive_actions`.
- The task JSON example uses root fields `length`, `scenario`, `scenario_id`, and `tasks`, where each task has `task_id`, `instruction`, `type`, and `apps`.

## Boundaries

- Current GUI-Owl v3.5 one-off Android/desktop/browser runs belong to [`../current-gui-owl/SKILL.md`](../current-gui-owl/SKILL.md).
- Legacy Mobile-Agent v1/v2/v3 preservation or migration belongs to [`../legacy-agents/SKILL.md`](../legacy-agents/SKILL.md).
- Benchmark scoring belongs to [`../benchmarks-and-evaluation/SKILL.md`](../benchmarks-and-evaluation/SKILL.md).

Do not claim a Mobile-Agent-E task succeeded unless the live device/API run actually completed.
