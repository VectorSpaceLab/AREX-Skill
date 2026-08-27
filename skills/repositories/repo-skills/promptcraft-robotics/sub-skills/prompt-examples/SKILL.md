---
name: prompt-examples
description: "Find, classify, adapt, and validate PromptCraft-Robotics markdown
  prompt examples across robotics task families."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Prompt examples

Use this sub-skill when a user asks for help with the PromptCraft-Robotics markdown examples: selecting an example family, adapting a prompt to a new scene, preserving the repo's response style, or checking whether a draft prompt follows the repository patterns.

This sub-skill covers text prompt examples. For the ChatGPT-AirSim runtime sample, route to `../airsim-simulator/`.

## Use this sub-skill for

- choosing an example category from a user request;
- summarizing the repository's robotics example families;
- adapting an aerial, embodied, manipulation, multi-robot, visual-servoing, or basic robotics prompt;
- preserving the `Question` / `Code` / `Reason` response pattern;
- validating a new draft prompt before it is shared or used.

## Do not use this sub-skill for

- installing or running the AirSim chatbot sample;
- diagnosing OpenAI API keys or AirSim simulator connectivity;
- generic LLM prompting that has no robotics control, scene, object, or robot-function context.

## Start here

1. Read `references/category-map.md` to choose the relevant example family.
2. Read `references/prompt-patterns.md` to preserve the repo's style.
3. Read `references/adaptation-guide.md` before rewriting an example for a new robot, scene, object set, or sensor.
4. Run `scripts/validate-prompt-example.py` against a draft markdown prompt when a structural check is useful.
5. Use `references/troubleshooting.md` when the prompt is ambiguous, invents functions, or mixes coordinate conventions.

## Common decisions

- If the user wants to run the AirSim sample, route to `../airsim-simulator/`.
- If the user wants a prompt to match a robotics task, choose the category by robot, sensor, and action family.
- If the scene has duplicate objects, keep the repository's clarification behavior.
- If the user provides a draft markdown prompt, run or recommend `scripts/validate-prompt-example.py`.
- If the adaptation involves manipulation, check safe-height and top-surface placement rules.
- If the adaptation involves navigation, check turn/move or waypoint conventions before writing code.
- If the request combines prompt adaptation and live execution, split the response across this sub-skill and `../airsim-simulator/`.

## Category routing

| User intent | Best route inside this sub-skill |
| --- | --- |
| drone inspection, obstacle avoidance, Tello-like object search | `references/category-map.md#aerial-robotics` |
| visual object navigation, turn/move step traces | `references/category-map.md#embodied-agents` |
| pick/place/stack/push manipulation | `references/category-map.md#manipulation` |
| comparing robot, car, and drone controllers | `references/category-map.md#multiple-robots` |
| camera-based ball catching or SVG-style image reasoning | `references/category-map.md#spatial-temporal-reasoning` |
| generic robotics control, coordinate transforms, or controllers | `references/category-map.md#basic-robotics` |

## Prompt adaptation principles

- Preserve the list of allowed functions for the chosen robot.
- Ask a clarification question when object identity is ambiguous.
- Use only functions stated in the prompt context.
- Keep coordinate frames, units, and signs explicit.
- Prefer small, reviewable code snippets over large scripts unless the original example demonstrates an end-to-end script.
- Include an explanation when the repo's example style expects one.

## Bundled helper

- `scripts/validate-prompt-example.py` checks a draft markdown prompt for core PromptCraft-Robotics structure signals.

## Boundary with AirSim simulator

Some example categories mention AirSim drones, but example selection and adaptation still belongs here. Move to `../airsim-simulator/` only when the user asks about the runtime sample, its config files, wrapper functions, or API/runtime failures.
