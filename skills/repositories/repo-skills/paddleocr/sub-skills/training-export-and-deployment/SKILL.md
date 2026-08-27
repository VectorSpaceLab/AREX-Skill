---
name: training-export-and-deployment
description: "Routes PaddleOCR users to training, export, deployment, and
  config-maintenance workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training, Export, and Deployment

Use this route when the task is about training, evaluating, exporting, or deploying PaddleOCR models, or when the user needs to inspect config-driven launch paths rather than run a simple inference command.

## Handle these tasks here

- Config-driven training and evaluation.
- Exporting models and inspecting training/program YAML.
- Deployment decisions across serving, ONNX, C++, mobile, and high-performance inference paths.
- TIPC and other long-tail regression evidence.

## Route away from here

- Everyday local OCR inference belongs in `local-ocr-pipelines`.
- Document parsing and Office conversion belong in `document-parsing-and-conversion`.
- Hosted API or MCP work belongs in `cloud-api-and-integrations`.

## Read these references

- [`references/training-and-export.md`](references/training-and-export.md) for config structure, train/eval/export flow, and common command patterns.
- [`references/deployment-reference.md`](references/deployment-reference.md) for deployment path selection and backend expectations.
- [`references/troubleshooting.md`](references/troubleshooting.md) for YAML, dataset, checkpoint, and backend failures.

## Use the bundled script

- [`scripts/inspect_training_config.py`](scripts/inspect_training_config.py) safely summarizes PaddleOCR-style YAML configs without running training.

## What future agents should know

- The source `tools/` scripts and `deploy/` tree are evidence for the public workflow, but they are not the runtime skill's execution surface.
- Training and export are long-running and backend-sensitive. Use the references to choose the command shape, then validate the config before starting a job.
- Treat `tests/test_program_safe_yaml.py` and similar config-safety tests as evidence for parser behavior, not as a substitute for real training.
- Keep deployment choices separate: a serving path, an ONNX path, a C++ path, and a mobile path are not interchangeable.

## Common triggers

- "How do I train PaddleOCR on my dataset?"
- "What config keys does program.py understand?"
- "How do I export a model or choose a deployment backend?"
- "Why did my deployment or checkpoint step fail?"
