---
name: model-serving
description: "Use FedML for model cards, local predictors, on-prem or cloud
  deployment, inference requests, and streaming response serving."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Model Serving

Use this sub-skill for FedML model cards, local model serving, cloud/on-prem deployment, endpoint requests, streaming responses, `FedMLPredictor`, `FedMLInferenceRunner`, and `fedml model` CLI/API workflows.

## Do not use this for

- Training a model before serving: use `../distributed-training/SKILL.md`.
- Launching a generic non-serving job: use `../launch-and-packaging/SKILL.md`.
- Multi-step workflow DAGs that include deploy/inference jobs: use `../workflow-orchestration/SKILL.md`.

## Route by serving task

| User task | Preferred path |
| --- | --- |
| local predictor smoke | subclass `FedMLPredictor`, wrap with `FedMLInferenceRunner`, test readiness/predict |
| streaming inference | use the streaming predictor pattern and stream chunks explicitly |
| model card creation | `fedml model create` or `fedml.api.model_create` |
| package/push/deploy | `fedml model package/push/deploy` or matching `fedml.api.model_*` calls |
| remote endpoint invocation | `fedml model run` or `fedml.api.model_run(endpoint_id, json_string)` |

## Local safe smoke

Run the bundled local predictor helper from the root skill directory:

```bash
python sub-skills/model-serving/scripts/local_predictor_smoke.py
python sub-skills/model-serving/scripts/local_predictor_smoke.py --streaming
```

The helper uses FedML serving classes without pushing or deploying a model card.

## Model-card CLI/API path

Discovery commands are safe:

```bash
fedml model --help
fedml model create --help
fedml model deploy --help
fedml model run --help
```

Remote operations require approval and credentials:

```bash
fedml model create <name> --model <path> --config <config.yaml>
fedml model package <name>
fedml model push <name> --api-key <key>
fedml model deploy <name> --endpoint-name <endpoint>
fedml model run <endpoint-id> '{"inputs": ...}'
```

Python equivalents are listed in `../../references/api-reference.md#public-fedmlapi-helpers`.

## Evidence anchors

- `python/fedml/serving/fedml_predictor.py` — predictor base class.
- `python/fedml/serving/fedml_inference_runner.py` — local inference runner.
- `python/examples/deploy/quick_start/src/main_entry.py` — simple predictor shape.
- `python/examples/deploy/streaming_response/src/main_entry.py` — streaming response pattern.
- `python/tests/test_model_cli/` — model CLI reference paths, credential-bound for real execution.

## Cautions

- `fedml model deploy` can create endpoints and consume resources; ask before running.
- Remote deployment can require API key, endpoint name/id, worker/master device ids, provider resources, Docker/local platform, and model artifacts.
- Do not treat a streaming predictor as a one-shot JSON predictor.
- Keep local smoke tests separate from remote model card registry actions.

## Exit criteria

A model-serving task is complete when the serving mode, predictor interface, model artifact path, endpoint/credential requirements, and local-vs-remote decision are explicit, and local smoke or remote deployment status is recorded.
