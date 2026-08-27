---
name: export-and-prompt
description: "Prompt trained experiments locally, tune generation parameters,
  and publish or export to Hugging Face Hub."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# export-and-prompt

Use this sub-skill when a trained experiment already exists and the task is to
interactively prompt it, adjust generation settings during the prompt session,
preflight the saved artifacts, or prepare a Hugging Face Hub export.

## Route here when
- The user wants to chat with a saved experiment locally.
- The user wants to change generation settings at prompt time.
- The user wants to verify that the experiment directory is ready for prompt or export.
- The user wants to publish a trained checkpoint to Hugging Face Hub.
- The user wants to hand a downloaded or published model to h2oGPT.

## Route elsewhere when
- The user still needs dataset preparation or experiment creation.
- The user needs to train, resume, or compare experiments.
- The user wants model internals, loss logic, or metric behavior.

## Bundled references
- `references/prompting-and-generation.md`
- `references/hugging-face-export.md`
- `references/troubleshooting.md`

## Bundled scripts
- `scripts/check_experiment_artifacts.py`
- `scripts/check_publish_inputs.py`

## Fast checks
- `python scripts/check_experiment_artifacts.py --help`
- `python scripts/check_publish_inputs.py --help`
- `python llm_studio/prompt.py -h`
- `python llm_studio/publish_to_hugging_face.py -h`

## Working rule
Use the preflight scripts first, then the runtime command that matches the
user's goal. Prompt-session parameter changes are local to that session and do
not rewrite the saved experiment.