# Environment and Install Reference

## Purpose

Read this when deciding whether an environment can inspect or run InvokeAI, or when troubleshooting import/server/backend setup before using a sub-skill.

## Package Facts

- Distribution name: `InvokeAI`.
- Import root: `invokeai`.
- Version captured for this skill: `6.13.0.post1`.
- Python requirement: `>=3.11,<3.13`.
- Public console scripts: `invokeai-web`, `invoke-useradd`, `invoke-userdel`, `invoke-userlist`, and `invoke-usermod`.
- Optional backend extras include CPU, CUDA, ROCm, xformers, ONNX variants, test/dev/dist groups, and backend-specific Torch wheel indexes.

## Safe Import Check

Use a lightweight import check before deeper inspection:

```bash
python - <<'PY'
import invokeai
import invokeai.version
print(invokeai.__app_name__, invokeai.version.__version__)
PY
```

This only proves the import root and version surface are available. It does not prove the web server, Torch/diffusers backends, model loading, or generation workflows are usable.

## Backend Expectations

InvokeAI’s runtime dependencies include Torch, diffusers, transformers, FastAPI, uvicorn, pydantic-settings, python-socketio, image/model utilities, and optional CUDA/ROCm/ONNX/xformers pieces. Choose the smallest backend that matches the task:

- Use CPU/metadata-only checks for docs, settings, workflow JSON, API route maps, and safe model metadata diagnostics.
- Use the official Torch CPU/CUDA/ROCm indexes when installing those extras; do not substitute a generic mirror for backend wheels unless it is known to host the exact required wheels.
- Do not run model loading or generation unless model weights, backend packages, and hardware are intentionally available.

## Entry Point Routing

- `invokeai-web` starts the web server and must parse CLI args before importing most app/runtime modules.
- `invoke-useradd`, `invoke-userdel`, `invoke-userlist`, and `invoke-usermod` operate on the configured InvokeAI root/user database; use a disposable root for tests.
- Use `sub-skills/operations-config/scripts/inspect_cli_help.py` to inspect known help text safely without starting the server or mutating users.

## Skill Generation Inspection Note

This skill was generated with a private metadata-only inspection environment that verified package metadata, lightweight imports, console entry points, and generated JSON catalogs. Full server startup and model/backend execution were intentionally not run because they require broad dependencies, model artifacts, optional hardware, and/or long-lived services.
