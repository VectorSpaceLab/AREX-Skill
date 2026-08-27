# HTTP and policy contract

## Routes

- `GET /health` → lightweight `{"status":"ok"}` readiness response.
- `GET /v1/models` → model listing from the active experiment.
- `GET /v1/capabilities` → image slots, state contract, action spec, VLA/VLM support, max batch size, and sampling defaults.
- `POST /v1/infer` → JSON observation plus sampling, response key `actions` and optional metadata.
- `POST /v1/reset` → episode boundary; important for stateful policies.
- `POST /v1/chat/completions` → OpenAI-style VLM generation; VLA-only policies return not implemented.
- `POST /process_frame` → legacy multipart request with response key `response`.

## v1 request

```json
{
  "observation": {
    "prompt": "pick up the cube",
    "images": {"1": "<base64 PNG>", "2": "<base64 PNG>"},
    "state": [0.0, 0.0, 0.0]
  },
  "sampling": {"num_steps": 10, "cfg_scale": 1.5, "seed": 42}
}
```

Image keys are numeric strings starting at `1`; the server maps them to internal `image/0`, `image/1`, etc. The server filters sampling keys to `num_steps`, `cfg_scale`, and `seed`. A required state key is checked at the HTTP boundary; concrete state dimensionality is a policy/model concern.

## BasePolicy

A policy is injected with model, tokenizer, norm stats, optional input/output pipelines, and `camera_order`. Implement `select_action(observation, sampling_config)` and return a list of `ActionOutput`; each `ActionOutput.actions` is a NumPy array `[chunk_size, action_dim]` with no batch dimension. The observation uses `image/{slot}`, `prompt`, and optional `state` for direct policy calls.

The class-level declarations drive capabilities:

- `action_mode`: `absolute`, `relative`, or `unknown`;
- `state_used`, `state_required`, `state_dim`;
- `max_batch_size`;
- `supports_vlm()` and `generate()`;
- override `reset()` for episode memory.

`SamplingConfig` defaults to `num_steps=10`, `cfg_scale=1.5`, and no seed. `GenSamplingConfig` controls text generation separately.

## Client semantics

`DexClient(base_url, use_delta=True, api_style="legacy", sampling=None)` queues action chunks. `act(observation, prompt)` requests a new chunk when its queue is empty. With `use_delta=True`, returned actions are accumulated against `last_act`; the orientation indices `[3:6]` wrap across ±pi, and the gripper tail is reset before accumulation. Set `use_delta=False` when the server/environment already supplies absolute actions or capability metadata says so.

The client uses OpenCV RGB arrays, encodes PNG bytes, and sends v1 image slots as base64. A server process is external to the client and must be reachable at the configured URL.

## DM0 realtime

The optional realtime policy keeps the v1 contract and absolute action semantics but uses a Triton-backed CUDA graph. Its fixed-step graph requires each request's `sampling.num_steps` to equal the advertised capability. Treat Triton, checkpoint conversion, and performance numbers as optional/unverified unless the matching CUDA/runtime/checkpoint is available.
