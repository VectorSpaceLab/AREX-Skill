---
name: models-and-flavors
description: "Use this sub-skill for MLflow Models, pyfunc, flavor APIs,
  signatures, input examples, dependencies, local serving/prediction, and
  mlflow.evaluate workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MLflow Models and Flavors

Use this sub-skill when the task involves packaging, loading, validating, evaluating, or locally serving MLflow Models.

## Route here for

- Logging, saving, loading, or inspecting MLflow Models and `MLmodel` metadata.
- Custom pyfunc models using `mlflow.pyfunc.PythonModel`, callables, model-as-code files, artifacts, `model_config`, and `params`.
- Flavor APIs such as `mlflow.sklearn`, `mlflow.pytorch`, `mlflow.transformers`, and `mlflow.langchain` when the issue is model packaging/loading rather than framework training.
- Model signatures, input examples, schema enforcement, model dependency files, environment reconstruction, and optional flavor dependency failures.
- `mlflow.evaluate`, custom metrics/artifacts, model validation thresholds, and precomputed prediction evaluation.
- `mlflow models` CLI commands for local model serving, prediction, environment preparation, Dockerfile generation, Docker builds, and pip requirement updates.

## Route elsewhere

- Registry aliases, versions, stages, registered model lifecycle, and model IDs as governance objects belong in `tracking-and-registry`.
- Deployment endpoint creation, server authentication, production serving infrastructure, and MLflow Projects execution belong in `serving-and-projects`.
- GenAI scoring, tracing, prompts, judges, and app observability belong in `genai-observability`; use this sub-skill only for shared model packaging/evaluation mechanics.

## Start with these references

- `references/api-reference.md` for concrete API signatures and call patterns.
- `references/model-packaging.md` for pyfunc, model-as-code, flavor, signature, and dependency packaging recipes.
- `references/evaluation-and-serving.md` for `mlflow.evaluate`, local scoring, and `mlflow models` CLI workflows.
- `references/troubleshooting.md` for schema mismatch, dependency, URI, optional-package, serving payload, and evaluation repair playbooks.

## Bundled smoke scripts

Run these from any writable directory with MLflow installed:

```bash
python skills/mlflow/sub-skills/models-and-flavors/scripts/pyfunc_smoke.py
python skills/mlflow/sub-skills/models-and-flavors/scripts/evaluate_smoke.py
```

The scripts use temporary local tracking directories and tiny fixtures only. They do not require network access, model registry services, optional deep-learning packages, or the MLflow source checkout.
