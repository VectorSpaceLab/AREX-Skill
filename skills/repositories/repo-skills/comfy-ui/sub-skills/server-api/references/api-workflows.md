# API Workflow Automation

ComfyUI’s automation path uses API-format prompt JSON, not the full UI workflow JSON. Export from the UI with `File -> Export (API)` before calling `/prompt`. For graph semantics, validation details, and node input references, use `../../workflow-execution/`.

## API Prompt JSON Shape

A minimal valid shape is an object whose keys are node ids:

```json
{
  "4": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {"ckpt_name": "model.safetensors"}
  },
  "9": {
    "class_type": "SaveImage",
    "inputs": {"images": ["8", 0], "filename_prefix": "ComfyUI"}
  }
}
```

Client-side validation should catch at least:

- Top-level JSON must be an object, not a list.
- Each node id must map to an object.
- Every node must include string `class_type`.
- Every node should include object `inputs`; empty inputs are allowed by shape but may fail server validation.
- Node references in inputs use `["node_id", output_index]`.
- UI workflow exports often contain fields such as `nodes`, `links`, or `last_node_id`; those are not directly accepted as `/prompt` payloads.

## Queue, Wait, Download Pattern

1. Generate a client id. UUIDs are a safe default.
2. `POST /prompt` with `{ "prompt": workflow, "client_id": client_id }`.
3. Save `prompt_id` from the response.
4. Poll `GET /history/{prompt_id}` or listen to `/ws?clientId=<client_id>` until complete.
5. Walk `history[prompt_id].outputs`. Common image outputs are under `outputs[node_id].images`.
6. Download each file through `/view` using the exact `filename`, `subfolder`, and `type` from history.

Example file item:

```json
{"filename": "ComfyUI_00001_.png", "subfolder": "", "type": "output"}
```

Download URL:

```text
/view?filename=ComfyUI_00001_.png&subfolder=&type=output
```

## Websocket Semantics

Connect to:

```text
/ws?clientId=<same-client-id-used-for-post-prompt>
```

On connect, the server sends a text `status` message with queue status and assigned sid. During execution, clients receive JSON text messages such as:

```json
{"type": "executing", "data": {"node": "3", "prompt_id": "..."}}
```

The target prompt is done when a text message satisfies:

```text
message.type == "executing"
message.data.prompt_id == target_prompt_id
message.data.node == null
```

Important details:

- Filter by `prompt_id`; other prompts can emit messages on shared or reused clients.
- Reconnects with the same `clientId` replace the previous socket.
- If the socket reconnects while the same client is executing, the server may resend the current node.
- The first client text message may negotiate feature flags by sending `{"type": "feature_flags", "data": {...}}`; the server can answer with `feature_flags`.
- Binary websocket frames are preview/image bytes, not JSON. Ignore them unless the workflow intentionally uses websocket image output.

## Binary Preview Frames

Sampler previews and `SaveImageWebsocket` can send binary frames on `/ws`.

Patterns from the bundled examples:

- Latent preview frames include an 8-byte header followed by image bytes. Clients that only need completion can ignore every non-text frame.
- If using `SaveImageWebsocket`, track the current executing node from text messages. When the current node is the `SaveImageWebsocket` node, store binary payloads after the 8-byte header.
- For normal `SaveImage`, prefer `/history/{prompt_id}` plus `/view`; this is easier to retry and does not require decoding websocket image frames.

## API Nodes and Credentials

Hosted API nodes use sensitive request metadata. Put credentials in `extra_data`, not in the workflow graph:

```json
{
  "prompt": {"...": "..."},
  "client_id": "automation-client",
  "extra_data": {"api_key_comfy_org": "<secret-from-env>"}
}
```

ComfyUI removes sensitive extra-data keys from public queue tuples. Client code should still avoid printing request bodies containing secrets.

Use `--disable-api-nodes` to prevent hosted API nodes and frontend internet communication in offline or locked-down deployments.

## Bundled Script: HTTP Client

`../scripts/comfy_api_client.py` validates and queues API workflow JSON.

Show help:

```bash
python sub-skills/server-api/scripts/comfy_api_client.py --help
```

Queue and wait for history:

```bash
python sub-skills/server-api/scripts/comfy_api_client.py workflow-api.json --wait --timeout 300
```

Download output files:

```bash
python sub-skills/server-api/scripts/comfy_api_client.py workflow-api.json --wait --download-dir outputs
```

Pass an API-node key from an environment variable:

```bash
COMFY_API_KEY=... python sub-skills/server-api/scripts/comfy_api_client.py workflow-api.json --api-key-env COMFY_API_KEY
```

## Bundled Script: Websocket Monitor

`../scripts/comfy_websocket_monitor.py` validates and queues API workflow JSON, then waits on `/ws` for the target prompt to complete.

```bash
python sub-skills/server-api/scripts/comfy_websocket_monitor.py workflow-api.json --download-dir outputs
```

Use `--save-binary-previews DIR` only when you intentionally want raw binary websocket payloads for inspection. The monitor ignores binary frames for completion logic.

## Retry and Timeout Guidance

- Server not ready: retry `GET /system_stats` or `GET /prompt` before queueing.
- Queue accepted but no history yet: wait; history is populated after execution finishes or fails.
- Websocket times out but prompt may still run: fall back to `GET /history/{prompt_id}` and `GET /queue`.
- `/history/{prompt_id}` returns `{}`: wrong prompt id, not complete yet, history cleared, or server restarted.
- `/view` fails after history exists: use the exact filename/subfolder/type from history, and do not invent local paths.
