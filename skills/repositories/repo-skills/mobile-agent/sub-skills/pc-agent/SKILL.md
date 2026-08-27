---
name: pc-agent
description: "Use PC-Agent current and v1 desktop automation workflows with
  Mac/Windows routing, SoM/OCR/accessibility configuration, safe command
  building, and config validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PC-Agent

Use this sub-skill when a task names PC-Agent, desktop automation, Mac/Windows screenshots, SoM, OCR, accessibility, coordinate ratio, font paths, `PC-Agent/config.json`, `run.py`, or `run_v1.py`.

## Route map

| Prompt signal | Workflow | Read / run |
|---|---|---|
| Current PC-Agent `run.py`, config.json model/token/url | Current PC-Agent | [`references/configuration.md`](references/configuration.md), `scripts/validate_pc_agent_config.py`, `scripts/build_pc_agent_command.py` |
| PC-Agent v1, `run_v1.py`, `--api_url`, `--api_token`, `--qwen_api` | PC-Agent v1 | [`references/configuration.md`](references/configuration.md), command builder with `--version v1` |
| Clicks offset, font issues, Mac vs Windows, SoM/A11y/OCR settings | Action/perception tuning | [`references/action-space.md`](references/action-space.md) |
| Headless CI, screenshot errors, accessibility permissions, OCR credentials | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe workflow

1. Validate the private config without printing secrets:

```bash
python sub-skills/pc-agent/scripts/validate_pc_agent_config.py --config pc_config.json
```

2. Build a current PC-Agent command:

```bash
python sub-skills/pc-agent/scripts/build_pc_agent_command.py \
  --version current \
  --os windows \
  --instruction "Open the browser and search project docs" \
  --ratio 1.0 \
  --ocr-api 1 \
  --use-a11y 1
```

3. Build a v1 command only for legacy PC-Agent v1 workflows:

```bash
python sub-skills/pc-agent/scripts/build_pc_agent_command.py \
  --version v1 \
  --os mac \
  --instruction "Summarize the active webpage" \
  --api-token-env PC_AGENT_API_TOKEN
```

4. Run live commands only on a user-approved Mac/Windows GUI session with screen and accessibility permissions.

## Important facts

- Current `run.py` reads model endpoint fields from `config.json`: `vl_model_name`, `llm_model_name`, `url`, `token`.
- Current flags include `--instruction`, `--use_som`, `--draw_text_box`, `--font_path`, `--add_info`, `--disable_reflection`, `--clear_history_each_subtask`, `--ratio`, `--use_a11y`, `--num_step_limit`, `--mac`, `--ocr_api`, and `--use_perception_info`.
- v1 flags include `--pc_type`, `--api_url`, `--api_token`, `--qwen_api`, `--location_info`, `--icon_caption`, and `--disable_reflection`.
- Mac defaults usually need ratio `2`; Windows defaults usually need ratio `1` and a Windows font path.

## Boundaries

- GUI-Owl v3.5 desktop computer-use is in [`../current-gui-owl/SKILL.md`](../current-gui-owl/SKILL.md).
- OSWorld benchmark VM workflows are in [`../benchmarks-and-evaluation/SKILL.md`](../benchmarks-and-evaluation/SKILL.md).
- UI-S1 training is in [`../ui-s1-training/SKILL.md`](../ui-s1-training/SKILL.md).

Do not run PC-Agent from a headless CI shell or paste raw config tokens into answers.
