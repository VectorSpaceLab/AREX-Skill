# Repository overview

PromptCraft-Robotics is a small robotics prompt library plus a sample ChatGPT-AirSim drone interface.

## Main user-facing families

| Family | What users ask | Primary files |
| --- | --- | --- |
| AirSim sample | Run the drone chatbot, learn the helper API, inspect the config files, or troubleshoot startup problems | `chatgpt_airsim/` |
| Prompt examples | Find, classify, or adapt a robotics prompt example | `examples/` |

## Directory map

- `README.md` — top-level introduction, categories, and citation guidance.
- `chatgpt_airsim/` — sample drone chatbot, AirSim wrapper, config, and prompt templates.
- `examples/` — markdown prompt examples grouped by robotics task family.
- This generated skill's own `references/` and `sub-skills/` provide the self-contained runtime guidance.

## Example families at a glance

| Category | Representative examples | Typical request |
| --- | --- | --- |
| Aerial robotics | `airsim_turbine_inspection.md`, `airsim_solarpanel_inspection.md`, `airsim_obstacleavoidance.md`, `tello_example.md` | inspect, navigate, or inspect objects from a drone prompt |
| Embodied agents | `airsim_objectnavigation.md`, `visual_language_navigation_1.md`, `visual_language_navigation_2.md` | search for objects and navigate with visual clues |
| Manipulation | `manipulation_zeroshot.md`, `pick_stack_msft_logo.md` | pick, place, stack, or push blocks |
| Multiple robots | `multiple_robots.md` | compare or coordinate different robot types |
| Spatial-temporal reasoning | `visual_servoing_basketball.md` | camera-based control and visual servoing |
| Basic robotics | `problems.md` | generic robotics reasoning, control, or transforms |

## Shared conventions

- Many examples use a `Question` / `Code` / `Reason` response style.
- Clarification is preferred when an object name is ambiguous or there are multiple same-type objects.
- The AirSim sample and the examples both depend on exact object names and careful coordinate conventions.
- The AirSim sample is the only part that executes code; the markdown examples are evidence and adaptation material.

## How to use this overview

Read this file first when you only need the broad shape of the repository. Then move to:

- `sub-skills/airsim-simulator/` for runtime AirSim questions.
- `sub-skills/prompt-examples/` for example selection or prompt rewriting.
