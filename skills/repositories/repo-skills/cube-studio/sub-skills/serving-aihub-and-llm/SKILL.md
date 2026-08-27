---
name: serving-aihub-and-llm
description: "Route CubeStudio model serving, AIHub, chat, and inference-service workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Serving, AIHub, and LLM

Use this sub-skill for CubeStudio tasks that deploy or inspect models, manage inference services, configure AIHub cards, or tune chat / LLM gateway behavior.

## Use when

- you need to publish a trained model into a serving object or edit an existing service
- you need to choose between `serving`, `ml-server`, `tfserving`, `torch-server`, `triton-server`, or related options
- you need to explain model path formats, ports, health checks, metrics, HPA, canary, or shadow settings
- you need to inspect AIHub application cards or the chat configuration and prompt/service payloads
- you need to map a training-model record to an inference-service record

## Start here

1. Read [references/serving-workflows.md](references/serving-workflows.md) for the service lifecycle and the training-model → inference-service path.
2. Read [references/inference-frameworks.md](references/inference-frameworks.md) for service types, model-path rules, ports, health, metrics, and sidecar semantics.
3. Read [references/aihub-and-chat.md](references/aihub-and-chat.md) for AIHub card fields and chat/gateway payloads.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for common serving and LLM failures.
5. Before relying on the service defaults, run the bundled helper:

   ```bash
   python scripts/render_inference_defaults.py --help
   python scripts/render_inference_defaults.py
   python scripts/render_inference_defaults.py --framework tfserving
   ```

## Safety contract

This sub-skill is for explanation, cataloging, and validation. Do not start model-serving pods, call deployment endpoints against a live cluster, or treat the original serving image Dockerfiles as generic validation commands. Keep deployment-side side effects under the operator's control.

Never run blindly: live deploy/update endpoints, image builds, cluster install scripts, or service-start commands.

## Route elsewhere

- Notebook/resource group/GPU selector work: `compute-notebooks-and-images`
- Pipeline / training-job creation that produces a model later deployed here: `pipelines-and-job-templates`
- Platform install, private registry, cluster bring-up, PVC/CRD ordering: `deploy-and-operate`
- Shared backend plumbing, auth, permissions, or frontend build/proxy changes: `backend-and-configuration`

## Expected operating output

Return a plan or explanation that makes the following clear:

- which serving family is being discussed;
- which model-path format, port set, metrics path, and health path apply;
- whether the service came from a trained model, a hand-authored service, or an AIHub card;
- which bundled reference or helper to inspect next;
- what the most likely failure mode is when a service does not come up or cannot be queried.

Keep the detailed constant tables and card payloads in the bundled references, not here.
