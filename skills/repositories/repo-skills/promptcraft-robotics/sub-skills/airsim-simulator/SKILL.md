---
name: airsim-simulator
description: "Explain and preflight the PromptCraft-Robotics ChatGPT-AirSim
  drone sample, its helper API, and its config/runtime caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# AirSim simulator

Use this sub-skill when a user asks about the ChatGPT-AirSim drone sample, its prompt contract, its helper API, or the setup/configuration needed to reason about it safely.

This sub-skill is intentionally focused on the sample's public behavior and preflight checks. It does not try to execute unreviewed model output, and it does not depend on the original repository checkout being present.

## Use this sub-skill for

- explaining how the AirSim chatbot sample is structured;
- checking the required config and settings files before a user tries the sample;
- listing the helper functions available to the drone prompt;
- explaining the sample's coordinate and object-name conventions;
- diagnosing OpenAI / AirSim / import / relative-path failures;
- warning users about the direct code execution risk in the runtime loop.

## Do not use this sub-skill for

- browsing the markdown robotics example catalog;
- choosing among aerial, embodied, manipulation, or visual-servoing prompt examples;
- generic robotics prompt rewriting that is not specific to the AirSim sample.

## Start here

1. Read `references/setup-and-runtime.md` for the sample shape and the environment assumptions.
2. Read `references/available-functions.md` for the helper API and coordinate conventions.
3. Read `references/prompt-contract.md` for the prompt style and clarification rules.
4. Run `scripts/check-chatgpt-airsim-config.py` against the configuration files you want to validate.
5. Read `references/troubleshooting.md` if anything about the environment, API key, or simulator connection looks wrong.

## Common decisions

- If the user only wants a prompt-library example, route to `../prompt-examples/`.
- If the user wants a safe preflight without live calls, use `scripts/check-chatgpt-airsim-config.py`.
- If the user wants to run generated code, first warn about direct execution and require sandbox/review.
- If the user asks what the drone can do, read `references/available-functions.md`.
- If the user asks how to phrase the prompt, read `references/prompt-contract.md`.
- If the user reports an API key, import, simulator, or relative-path error, read `references/troubleshooting.md`.
- If the user asks about adding a new helper, explain that runtime implementation and prompt contract must change together.

## What future agents should remember

- The sample uses the OpenAI ChatCompletion-style API that matched the inspected `openai 0.27.2` environment.
- The sample extracts fenced code blocks from model responses and executes them directly, so the runtime must be treated as unsafe.
- The wrapper exposes only a small set of drone helpers, and the prompt contract expects exact object names and clarification when the scene is ambiguous.
- The AirSim coordinate handling in the wrapper is not the same as the human-facing prompt wording, so sign conventions must be checked carefully before describing motion.

## Reading guidance

- Use `references/setup-and-runtime.md` when the user wants setup, runtime, or configuration context.
- Use `references/available-functions.md` when the user asks what the drone can do or how the wrapper maps to AirSim.
- Use `references/prompt-contract.md` when the user asks how the prompt should be phrased or why a clarification question is needed.
- Use `references/troubleshooting.md` when a setup or import failure needs a concrete recovery path.

## Bundled helper

- `scripts/check-chatgpt-airsim-config.py` is the safe preflight helper. It validates a user-supplied config/settings pair and reports whether the runtime prerequisites look consistent.

## Boundary with the prompt-examples sub-skill

If the user is really asking for a drone example from `examples/`, route to `prompt-examples` unless the question is specifically about the ChatGPT-AirSim sample itself.

## Safety note

Never present the sample's generated code as inherently safe. The runtime executes code blocks directly, so any live use must be sandboxed and reviewed.
