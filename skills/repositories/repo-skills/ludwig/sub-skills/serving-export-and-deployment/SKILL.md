---
name: serving-export-and-deployment
description: "Guides agents serving Ludwig models, building prediction payloads,
  exporting artifacts, using Ray/KServe/vLLM shims, and uploading model
  outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving, Export, and Deployment

Use this sub-skill when the task is about `ludwig serve`, FastAPI endpoints, Ray Serve, KServe, vLLM serving, request payloads, export formats, MLflow export, or Hub uploads.

## Start here

1. Confirm a complete trained model artifact exists. Use the inspection helper from [prediction-evaluation-and-inspection](../prediction-evaluation-and-inspection/SKILL.md) if needed.
2. Check serving/export optional dependencies:

```bash
python scripts/check_serving_prereqs.py
```

3. Build a payload before starting a server:

```bash
python scripts/build_serving_payload.py --config config.yaml --mode predict --output payload.json
```

4. Read [workflows.md](references/workflows.md) for local server, Ray Serve, KServe, vLLM, export, and upload patterns.

## Core commands

```bash
ludwig serve --model_path results/experiment_run/model --host 0.0.0.0 --port 8000
ludwig export_model --model_path results/experiment_run/model --output_path exported_model --format safetensors
ludwig export_mlflow --model_path results/experiment_run/model --output_path mlflow_model
ludwig upload hf_hub --repo_id owner/name --model_path results/experiment_run/model
```

Do not run servers or uploads unless the user approves long-running processes or remote side effects.
