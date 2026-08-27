---
name: server-api
description: "Launch ComfyUI safely and automate it through HTTP and websocket
  APIs, including queueing prompt JSON, monitoring progress, collecting outputs,
  configuring server flags, and handling user/model/asset route surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# ComfyUI Server and API

Use this sub-skill when an agent needs to start ComfyUI, configure server-facing CLI flags, call REST endpoints, queue an API workflow, monitor websocket progress, download output images, or troubleshoot server/API access.

Route graph construction, node input semantics, validation failures, and API-workflow JSON structure to `../workflow-execution/`. Route model folders, `extra_model_paths.yaml`, backend/VRAM choices, and checkpoint placement to `../models-config/`. Route custom node class authoring and node metadata implementation to `../custom-nodes/`.

## Fast Path

1. Start ComfyUI with explicit network/security choices:
   - Local-only default: `python main.py --listen 127.0.0.1 --port 8188`
   - LAN/API host: add a specific `--listen` address and review CORS/TLS before exposing it.
   - Multi-user storage: add `--multi-user` and use user-scoped endpoints carefully.
2. Export the graph from the UI with `File -> Export (API)`; do not POST the normal UI workflow JSON unless it has been converted to API prompt JSON.
3. Validate the JSON shape before sending it: root object maps node ids to objects with `class_type` and `inputs`.
4. Queue with `POST /prompt` using `{ "prompt": { ... }, "client_id": "..." }`. Let the server mint `prompt_id`, or provide a canonical lowercase hyphenated UUID.
5. Monitor progress with `GET /ws?clientId=<client_id>` and wait for a text message of type `executing` whose `data.prompt_id` matches and whose `data.node` is `null`.
6. Fetch outputs with `GET /history/{prompt_id}`, then download files through `GET /view?filename=...&subfolder=...&type=output`.

## Bundled Helpers

- `scripts/comfy_api_client.py` validates an exported API workflow, queues it through `/prompt`, optionally waits for `/history/{prompt_id}`, and downloads output media through `/view`.
- `scripts/comfy_websocket_monitor.py` queues an API workflow, monitors `/ws`, ignores binary preview frames by default, waits for the target `prompt_id`, and can download final output files.

Both scripts use only Python standard-library modules by default. Run `python <script> --help` for arguments. They never embed model paths or credentials; pass secrets through environment variables only when needed.

## Common Endpoint Flow

```text
POST /prompt
  body: {"prompt": <api-workflow>, "client_id": "<uuid-or-client-string>"}
  response: {"prompt_id": "<uuid>", "number": <queue-number>, "node_errors": {...}}

GET /history/<prompt_id>
  response: {"<prompt_id>": {"outputs": {"<node_id>": {"images": [...]}}}}

GET /view?filename=<name>&subfolder=<subfolder>&type=output
  response: file bytes
```

For API nodes that call Comfy’s hosted API, put the key in request `extra_data`, never in the workflow JSON or script source:

```json
{
  "prompt": {"...": "..."},
  "client_id": "automation-client",
  "extra_data": {"api_key_comfy_org": "${COMFY_API_KEY}"}
}
```

`api_key_comfy_org` is sensitive queue metadata; avoid logging it and do not store it in reusable examples.

## References

- `references/cli-reference.md` covers launch flags for listen/port, TLS, CORS, user directories, frontend, manager/API-node controls, assets, compression, logging, and backend caveats.
- `references/api-reference.md` summarizes core REST routes, payloads, job endpoints, app/user/model/assets surfaces, and `/api` prefix behavior.
- `references/api-workflows.md` explains queue/history/view automation, websocket message semantics, binary previews, and bundled script usage.
- `references/troubleshooting.md` maps common failures to checks and fixes.

## Safety Defaults

- Keep `--listen 127.0.0.1` unless a remote client genuinely needs access.
- Prefer TLS termination by a trusted local reverse proxy; if using ComfyUI TLS flags, provide both `--tls-keyfile` and `--tls-certfile`.
- Do not use `--enable-cors-header *` on a host reachable by untrusted browsers unless that is an intentional integration choice.
- Use `--disable-api-nodes` when external hosted-provider API nodes and frontend internet communication should be blocked.
- Use `--disable-all-custom-nodes` or `--whitelist-custom-nodes` while diagnosing untrusted or broken custom-node startup code.
- Treat `/internal/*` as frontend/internal only; do not build stable automations on it.
