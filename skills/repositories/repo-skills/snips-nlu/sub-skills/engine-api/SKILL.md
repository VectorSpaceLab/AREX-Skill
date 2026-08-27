---
name: engine-api
description: "Use SnipsNLUEngine's Python API for fitting datasets, parsing
  text, inspecting intents and slots, configuring training, and persisting or
  loading engines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Snips NLU engine API

Use this sub-skill when the task is to operate Snips NLU through Python code:
create a `SnipsNLUEngine`, fit an already-valid dataset, parse user text,
retrieve intent or slot-only outputs, control random state or `force_retrain`,
and persist or load an engine artifact.

## Route here when

- The user has a Snips dataset dict or JSON file and wants Python API code.
- The task involves `SnipsNLUEngine.fit`, `parse`, `get_intents`, `get_slots`,
  `persist`, `from_path`, or `NLUEngineConfig`.
- The user needs to understand parsing result shapes, None-intent behavior,
  intent filters, `top_n`, or model-version/resource persistence behavior.

## Route elsewhere

- Dataset YAML/JSON authoring, resource acquisition details, or dataset schema
  repair: read `../dataset-and-resources/SKILL.md`.
- CLI commands, batch command lines, command metrics, or evaluation workflows:
  read `../cli-workflows/SKILL.md`.
- Custom processing-unit implementation: use this sub-skill only for how such
  units are plugged into `NLUEngineConfig`; keep implementation details outside
  this engine API route unless the task explicitly asks for integration code.

## Required references

Read only the references needed for the task:

- `references/api-reference.md` for signatures, result shapes, None intent,
  filters, `top_n`, `get_intents`, and `get_slots`.
- `references/workflows.md` for fit/parse code patterns and the bundled smoke
  helper usage.
- `references/configuration-and-persistence.md` for default language configs,
  random state, `force_retrain`, resources, and persisted model compatibility.
- `references/troubleshooting.md` when exceptions, missing resources,
  nondeterminism, loading failures, or dependency/Python-version issues appear.

## Safe helper

For a quick API smoke test against a user-provided dataset JSON, run the bundled
helper from this sub-skill directory:

```bash
python scripts/snips_nlu_engine_smoke.py \
  --dataset path/to/dataset.json \
  --query "turn on the kitchen lights" \
  --intent-filter sampleTurnOnLight \
  --top-n 2
```

The helper never uses an embedded source-relative dataset path and never
overwrites an existing persistence directory. It prints a JSON report and, when
language resources are unavailable, reports the resource name and next steps.

## Operating guardrails

- Treat a fitted engine as required before parsing or retrieving intents/slots.
- Pass Python `str` text, not bytes, into `parse` or `get_slots`.
- Preserve `None`/JSON `null` intent semantics: intent filters do not remove
  the None intent, and `get_slots(text, None)` returns an empty list.
- Do not promise probabilities sum to 1.0; they are confidence scores.
- For reproducible training, pass a fixed `random_state` to `SnipsNLUEngine` and
  keep the same package/model version and language resources.
- Do not load persisted engines across incompatible Snips NLU model versions
  unless the caller deliberately accepts `bypass_version_check=True` risk.
