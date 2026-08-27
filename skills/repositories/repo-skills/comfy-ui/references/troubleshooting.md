# ComfyUI Troubleshooting

Use this root guide for failures that cross multiple ComfyUI surfaces. For deeper fixes, route to the owning sub-skill.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError` for torch, frontend/template packages, API-node packages, acceleration libraries, or media libraries.
- Startup aborts before the HTTP server prints an address.
- A package install succeeds but runtime imports still fail.

Checks:

1. Confirm Python satisfies ComfyUI's supported range from package metadata.
2. Install the runtime requirements appropriate to the selected backend; do not assume CPU and CUDA wheels are interchangeable.
3. Run `python main.py --help` or inspect `comfy/cli_args.py`-backed flags when launch syntax is unclear.
4. Temporarily launch with `--disable-all-custom-nodes --disable-api-nodes` to isolate third-party custom/API node imports.
5. If the traceback mentions model paths or backend memory, route to `../sub-skills/models-config/`.

## Server Starts but Automation Fails

Route to `../sub-skills/server-api/` when failures involve HTTP routes, websocket progress, history/output downloads, CORS, TLS, multi-user storage, or API-node request credentials.

Fast checks:

- Default server is `127.0.0.1:8188`; remote clients cannot reach that loopback address from another host.
- `--listen` without an argument exposes all IPv4/IPv6 interfaces; pair it with network controls.
- Browser CORS failures differ from Python script connection errors.
- TLS-enabled servers require `https://` and `wss://` clients.
- History/output downloads require the exact `filename`, `subfolder`, and `type` values returned by `/history/{prompt_id}`.

## Prompt JSON Is Rejected

Route to `../sub-skills/workflow-execution/` when errors mention `prompt`, `class_type`, `inputs`, invalid links, missing node ids, node validation, cache behavior, async/lazy execution, or blueprint/template conversion.

Fast checks:

- `/prompt` expects API prompt JSON, not the full UI workflow JSON with canvas metadata.
- Each executable node must be an object with `class_type` and `inputs`.
- Links use `["node_id", output_index]`; output indexes are integers.
- Structural validation cannot prove node class availability, model names, optional dependencies, or runtime hardware.

## Custom Node Is Missing or Crashes

Route to `../sub-skills/custom-nodes/` when the task involves node package layout, `NODE_CLASS_MAPPINGS`, `INPUT_TYPES`, `RETURN_TYPES`, hidden inputs, public `comfy_api` node APIs, API-provider nodes, or return tuple mismatches.

Fast checks:

- The module imports without side effects that require unavailable models, internet, credentials, or GPUs.
- `NODE_CLASS_MAPPINGS` maps stable string names to classes.
- The method named by `FUNCTION` exists and returns one item per declared output.
- Hidden credentials and prompt metadata must stay hidden; do not expose them as widgets or log them.

## Model Cannot Be Found or Loaded

Route to `../sub-skills/models-config/` when a loader dropdown is missing a file, `extra_model_paths.yaml` is wrong, backend flags are confusing, VRAM is exhausted, quantized models fail, or model-family compatibility is unclear.

Fast checks:

- Put files in the category the loader searches: `checkpoints`, `loras`, `vae`, `controlnet`, `text_encoders`, `diffusion_models`, and so on.
- Validate `extra_model_paths.yaml` indentation, `base_path`, category names, and directory existence.
- Restart or refresh after changing model directories.
- Separate missing-file errors from unsupported model-family, optional dependency, or backend/precision errors.

## Hosted API Nodes Fail

Hosted API nodes are node definitions that call external providers, not the same thing as ComfyUI's local HTTP API.

Checks:

- Confirm API nodes were not disabled with `--disable-api-nodes`.
- Provide API keys through hidden node inputs or `/prompt` request `extra_data`, not hardcoded workflow JSON.
- Avoid logging tokens, provider request headers, full private URLs, or raw credential-bearing payloads.
- If the deployment must stay offline, disable API nodes and choose local-only workflows.

## Backend, CUDA, and VRAM Problems

Checks:

- Match torch wheels and optional acceleration packages to the intended backend: CUDA, ROCm, MPS, DirectML, oneAPI, or CPU.
- Use `--cpu` only when CPU execution is intended and slow performance is acceptable.
- Choose one primary VRAM strategy: `--highvram`, `--lowvram`, `--novram`, or `--gpu-only` are mutually exclusive.
- Use `--reserve-vram`, `--vram-headroom`, dynamic VRAM flags, async offload flags, and cache flags deliberately.
- Disable custom/API nodes while isolating backend import failures; re-enable once base launch works.

## Safe Debugging Order

1. Validate install/import and launch with minimal flags.
2. Disable custom/API nodes to isolate base server behavior.
3. Validate prompt JSON structurally before queueing it.
4. Confirm required model files and backend resources.
5. Re-enable custom nodes, API nodes, frontend integrations, CORS/TLS, and remote access one at a time.
