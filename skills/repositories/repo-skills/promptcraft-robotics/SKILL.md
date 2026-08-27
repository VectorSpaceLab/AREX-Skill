---
name: promptcraft-robotics
description: "Route PromptCraft-Robotics requests to the AirSim sample workflow
  or the markdown robotics prompt library."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PromptCraft-Robotics

PromptCraft-Robotics is a robotics prompt library plus a sample ChatGPT-AirSim drone interface. Use this skill when a user wants to:

- run, inspect, or troubleshoot the `chatgpt_airsim/` sample;
- understand the helper functions, prompt contract, or config files used by that sample;
- find, adapt, or classify one of the markdown robotics examples under `examples/`;
- rewrite a robotics prompt in the repo's `Question` / `Code` / `Reason` style;
- compare example families such as aerial robotics, embodied navigation, manipulation, multi-robot control, or visual servoing.

This skill is router-like. It keeps the repo map small at the top level and sends detailed work to the focused sub-skills.

## First choice

- Use `sub-skills/airsim-simulator/` for the ChatGPT-AirSim drone sample, its setup/configuration, and its safety caveats.
- Use `sub-skills/prompt-examples/` for the prompt example library under `examples/`.

## Quick route map

| User request | Route |
| --- | --- |
| "How do I run the AirSim chatbot?" | `sub-skills/airsim-simulator/` |
| "What functions can the drone use?" | `sub-skills/airsim-simulator/` |
| "Why is the sample Windows-only?" | `sub-skills/airsim-simulator/` |
| "Which example matches manipulation / navigation / visual servoing?" | `sub-skills/prompt-examples/` |
| "How do I write a new robotics prompt in this repo's style?" | `sub-skills/prompt-examples/` |
| "Explain the prompt library's categories" | `sub-skills/prompt-examples/` |

## What this root skill does and does not do

### It does

- Explain the repository at a high level.
- Point to the right sub-skill for detailed commands, prompt patterns, and troubleshooting.
- Preserve the repo's public routing metadata and provenance.

### It does not

- Reproduce the full AirSim setup instructions in the root file.
- Repeat the full catalog of example prompts at the root.
- Depend on the original repository checkout for runtime instructions.

## Installation and minimal checks

No package installation is required to use the prompt-example guidance. AirSim sample work needs the Python/OpenAI/AirSim stack described in `sub-skills/airsim-simulator/references/setup-and-runtime.md`.

From this skill directory, the safe bundled checks are:

```bash
python sub-skills/airsim-simulator/scripts/check-chatgpt-airsim-config.py --config <config.json> --settings <settings.json>
python sub-skills/prompt-examples/scripts/validate-prompt-example.py <draft.md>
```

Use those checks for preflight or prompt-structure review; they do not run the AirSim simulator or call a model API.

## Repository shape

- `README.md` introduces the repository and the two major families: the simulator sample and the prompt examples.
- `chatgpt_airsim/` contains the drone chatbot sample, wrapper, and prompt/config files.
- `examples/` contains markdown prompt examples grouped by robotics task family.
- `references/` holds the distilled public knowledge for future agents.
- `sub-skills/` holds the focused workflows.

## Read these references when needed

- `references/repo-overview.md` for the high-level repo map.
- `references/repo-provenance.md` for source commit and refresh baseline.
- `references/troubleshooting.md` for cross-cutting issues.
- `references/repo-routing-metadata.json` for the managed router placement used during import.

## Minimal orientation

If a user gives only a broad question like "What is this repo for?", answer from the root overview and then route to the best sub-skill.

If the user asks about the AirSim sample, remember three recurring facts from the repository evidence:

1. The sample uses a prompt-driven loop that sends user text to the OpenAI ChatCompletion API.
2. The sample extracts code blocks from model responses and runs them directly, so it must be treated as unsafe and sandboxed.
3. The wrapper uses repository-specific coordinate conventions and exact object names, so ambiguity should trigger clarification rather than guessing.

If the user asks about the examples, remember that the library is organized by task family, not by implementation package. Choose the example that matches the user's robotics task, then adapt the prompt style and functions rather than copying the repository path.

## Safety note

The AirSim sample can execute model-produced Python code. Future agents should treat that as a security risk, not as a convenience feature.

## Provenance note

Before claiming the skill is current, check `references/repo-provenance.md`. It records the source commit and the evidence paths used to build this skill.
