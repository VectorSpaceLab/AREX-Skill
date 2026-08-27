---
name: comfy-ui
description: "Use ComfyUI as a modular AI content-creation engine: launch and
  automate the server, submit API workflows, validate graph JSON, author custom
  nodes, and configure model paths/backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# ComfyUI

Use this repo skill when a user asks for help with ComfyUI workflows, automation, server/API usage, custom nodes, model folder configuration, backend/memory flags, or prompt graph debugging.

ComfyUI is a node-graph AI creation engine for image, video, audio, 3D, and model-tooling workflows. Treat it as an application/runtime with a Python launch script, HTTP/websocket APIs, a node registry, JSON prompt graphs, model-folder conventions, optional hosted API nodes, and hardware-sensitive backend behavior.

## Start Here

1. Identify the task surface: server/API automation, prompt graph execution, node authoring, or model/backend setup.
2. If the user has a workflow JSON, decide whether it is API prompt JSON or UI workflow JSON before sending it to `/prompt`.
3. If the user has a model-loading error, separate graph-node input issues from model search path/backend issues.
4. If the user has a custom node problem, inspect mappings and node schemas before debugging prompt execution.
5. If the user is exposing a server, make network, CORS, TLS, credential, and API-node choices explicit.

## Routes

- `sub-skills/server-api/`: launch ComfyUI, choose server-facing CLI flags, queue API prompt JSON over HTTP, monitor websocket progress, fetch history/output files, use app/user/model/assets routes, and troubleshoot server/API failures.
- `sub-skills/workflow-execution/`: validate and debug API prompt JSON, distinguish UI workflow exports from executable prompts, reason about graph links, caching, async/lazy execution, blueprints/templates, and inference failure boundaries.
- `sub-skills/custom-nodes/`: implement, scaffold, inspect, and troubleshoot custom nodes using classic `INPUT_TYPES` classes, `NODE_CLASS_MAPPINGS`, hidden inputs, async validation, public `comfy_api` APIs, and API-provider nodes.
- `sub-skills/models-config/`: configure model folders and `extra_model_paths.yaml`, understand checkpoint/LoRA/VAE/controlnet categories, choose backend/VRAM flags, diagnose missing models, and reason about supported model families/quantization.

## Common Decisions

- **Launching locally:** start local-only unless remote access is required: `python main.py --listen 127.0.0.1 --port 8188`.
- **Submitting workflows:** use API-format prompt JSON for `/prompt`; normal UI workflow JSON contains canvas metadata and must be exported/converted first.
- **Getting outputs:** queue with `/prompt`, wait on `/ws` or poll `/history/{prompt_id}`, then download file outputs with `/view` using exact history metadata.
- **Using API nodes:** pass hosted Comfy API credentials through request `extra_data` or hidden node credentials; never hardcode API keys in workflow JSON or scripts.
- **Model placement:** put each model file in the category its loader node searches, or register shared paths through `extra_model_paths.yaml`.
- **Backend failures:** simplify to explicit CPU/CUDA/ROCm/MPS/DirectML flags, disable custom/API nodes while isolating startup failures, then re-enable pieces gradually.

## Bundled References

- `references/troubleshooting.md` covers cross-cutting install/import, launch, prompt, custom-node, model-path, backend, credential, and security failures.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill for future staleness checks.

## Bundled Scripts

Most reusable scripts are owned by sub-skills because they operate on a specific surface:

- `sub-skills/server-api/scripts/comfy_api_client.py`: validate, queue, wait for history, and download outputs through REST.
- `sub-skills/server-api/scripts/comfy_websocket_monitor.py`: queue and monitor websocket progress while ignoring binary preview frames by default.
- `sub-skills/workflow-execution/scripts/validate_prompt_graph.py`: structurally validate API prompt JSON without importing ComfyUI or loading models.
- `sub-skills/custom-nodes/scripts/scaffold_custom_node.py`: generate a safe starter custom node package.
- `sub-skills/custom-nodes/scripts/inspect_node_definitions.py`: statically inspect classic node mappings and common schema mistakes.
- `sub-skills/models-config/scripts/validate_extra_model_paths.py`: validate `extra_model_paths.yaml` shape and referenced directories.

## Safety Notes

- Do not expose ComfyUI on a public interface with permissive CORS and no external authentication boundary.
- Do not run untrusted custom nodes or hosted API-node workflows without reviewing network, credential, and filesystem effects.
- Do not assume a workflow that validates structurally can execute: model files, node registry contents, optional dependencies, credentials, and backend hardware still matter.
- Do not embed local paths, API keys, generated output paths, or private server URLs in reusable workflows or scripts.
