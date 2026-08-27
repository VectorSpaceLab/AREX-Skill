# BentoML Cross-Cutting Troubleshooting

Use this reference for failures that span multiple BentoML workflows. For workflow-specific symptoms, read the nearest sub-skill troubleshooting file.

## Install Or Import Fails

- Symptom: `ModuleNotFoundError: No module named 'bentoml'` or `bentoml: command not found`.
- Likely cause: package installed in a different environment than the shell or editor.
- Recovery: run `python -m pip install -U bentoml`, then check `python -c "import bentoml; print(bentoml.__version__)"` and `python -m bentoml --help` or `bentoml --help`.

## Optional Dependency Missing

- Symptom: importing a framework helper, IO type, gRPC server, tracing exporter, or image support raises `ImportError`.
- Likely cause: core BentoML is installed but the optional package is not installed.
- Recovery: install the narrow dependency set: examples include `bentoml[grpc]`, `bentoml[io-image]`, `bentoml[io-pandas]`, `bentoml[tracing-otlp]`, `bentoml[monitor-otlp]`, or the model framework package such as `scikit-learn`, `torch`, `transformers`, `xgboost`, or `mlflow`.

## Service Target Cannot Load

- Symptom: `bentoml serve service:MyService` or `bentoml build` cannot import the target.
- Likely cause: wrong `module:object`, wrong working directory, source layout not on `PYTHONPATH`, dependency import at module scope, or service class not decorated.
- Recovery: use `sub-skills/service-authoring/scripts/validate_service_target.py --target service:MyService --working-dir .`, then route to `sub-skills/service-authoring/SKILL.md`.

## Build Or Containerization Fails

- Symptom: missing files in Bento, dependency resolution errors, Docker failures, platform mismatch, or model tag missing.
- Likely cause: invalid build context, include/exclude issue, dependency file path wrong, Docker not running, or local model store state absent.
- Recovery: statically check `bentofile.yaml` with `sub-skills/packaging-and-containerization/scripts/validate_bentofile.py`, then read `sub-skills/packaging-and-containerization/references/troubleshooting.md`.

## Server Or Client Fails

- Symptom: port conflict, readiness timeout, 404 endpoint, wrong request shape, token failure, or gRPC import error.
- Likely cause: stale server, wrong `--working-dir`, method name mismatch, JSON payload schema mismatch, missing `bentoml[grpc]`, or missing authentication token.
- Recovery: route to `sub-skills/serving-and-clients/SKILL.md`; build dry-run commands with `sub-skills/serving-and-clients/scripts/serve_command_builder.py`.

## Model Store Fails

- Symptom: model tag not found, framework import error, serialization failure, or model not included in a built Bento.
- Likely cause: model saved in a different store, tag/version mismatch, optional framework dependency missing, or `BentoModel` not declared where packaging can discover it.
- Recovery: route to `sub-skills/model-management/SKILL.md` and use `sub-skills/model-management/scripts/check_framework_extra.py` for dependency checks.

## BentoCloud Or CLI Fails

- Symptom: not logged in, wrong context/cluster, missing secret, invalid deployment config, wait timeout, quota error, or push/pull auth failure.
- Likely cause: credential/context mismatch, absent BentoCloud resource, invalid config shape, or cloud-side capacity/permission issue.
- Recovery: route to `sub-skills/cli-and-cloud/SKILL.md`; lint deployment configs locally before a cloud call with `sub-skills/cli-and-cloud/scripts/deployment_config_lint.py`. Do not paste raw API tokens into transcripts or logs.

## Observability Or Operations Fails

- Symptom: metrics missing, traces absent, log format wrong, config ignored, GPU not used, autoscaling behaves unexpectedly, or gateway rules do not route traffic.
- Likely cause: config file path or env var mismatch, missing exporter dependency, wrong service-level resources, collector unreachable, or cloud scaling settings in the wrong layer.
- Recovery: route to `sub-skills/observability-and-operations/SKILL.md`; use local config checks before starting external collectors or changing cloud resources.
