# Cross-Cutting Troubleshooting

## Install and Import

- If `import invokeai` fails, confirm Python is in the supported range `>=3.11,<3.13`, the `InvokeAI` distribution is installed, and runtime dependencies match the chosen backend.
- If `pip check` reports missing Torch/diffusers/FastAPI/backend packages after a metadata-only install, do not treat that as a runtime-ready environment; install the documented runtime/backend dependency set before server/model checks.
- If compiled packages fail on Python 3.13 or unsupported platforms, recreate the environment with Python 3.11 or 3.12 and backend wheels that match the hardware.

## Server and API

- If `invokeai-web` fails during startup, route to `sub-skills/operations-config/` and check root/config selection, dependency availability, port conflicts, SSL/CORS/log settings, and the startup order around Torch CUDA allocator configuration.
- If OpenAPI or route import fails, first run the bundled route-family fallback helper; full schema generation imports the app and needs the complete runtime dependency set.

## Workflows and Nodes

- If workflow JSON validates structurally but fails at runtime, route to `sub-skills/workflow-nodes/` for invocation type, field, edge, iterator/collector, and execution-state validation.
- If the failure involves queue enqueue, batch substitution, workflow library records, public/private access, or queue item redaction, route to `sub-skills/workflows-queues/`.

## Models and Backends

- If a model is listed but cannot load, route to `sub-skills/model-management/` and inspect record path, base/type/format, missing-file listing, optional backend packages, cache limits, and safe file metadata before loading weights.
- If LoRA, GGUF, quantized, or external provider models fail, verify taxonomy/format/provider settings before attempting conversion, deletion, downloads, or paid external calls.

## Safety Stops

Stop and ask before actions that download large models, start long-running services, use credentials/API keys, mutate user/workflow/model databases, delete model files, run release scripts, or stress GPU/VRAM.
