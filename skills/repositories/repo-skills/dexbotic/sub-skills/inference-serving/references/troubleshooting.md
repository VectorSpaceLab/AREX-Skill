# Inference troubleshooting

| Symptom | Cause | Remedy |
|---|---|---|
| Health works but infer fails | Model initialization, processor, or checkpoint mismatch | Read server startup logs and validate model family, processor, norm stats, and camera count before changing HTTP payloads. |
| `400` for images | Image keys are not 1-based numeric strings or base64 is malformed | Send `images: {"1": "..."}` with valid encoded image bytes. |
| State error | Capabilities says `state.required=true`, but request omits it | Query capabilities and provide the expected state; verify dimensionality in the policy. |
| Wrong action semantics | `use_delta` disagrees with `action_spec.action_mode` or environment control mode | Decide absolute/relative behavior once and disable client accumulation when it is already applied. |
| Fewer actions than expected | Model returned a chunk with a family-specific horizon | Inspect the returned array shape and configure the controller's action queue for that horizon. |
| Memory persists across episodes | Client reset only cleared its queue, or server reset was not called | Use v1 `reset()` at every episode boundary and verify the server's reset response. |
| Legacy route differs from v1 | Legacy response is `response`, v1 response is `actions`; sampling fields differ | Keep protocol-specific parsing and use v1 for capability-driven integrations. |
| VLM endpoint returns 501 | Policy does not support VLM generation | Use a policy with `supports_vlm()` or route the task to a dedicated VLM workflow. |
| Camera order mismatch | `camera_order` and numeric image slots disagree | Maintain a slot/name table and verify it against `/v1/capabilities`. |
| Realtime request rejected | `sampling.num_steps` differs from fixed CUDA graph steps | Use the advertised value; do not vary steps per request on the realtime backend. |
| Server cannot bind/connect | Port, host, container networking, or firewall issue | Check `/health` from the same network namespace; do not expose a physical robot until the local loop is proven. |
| CUDA OOM or slow first request | Checkpoint/precision/GPU mismatch or graph warm-up | Run a single bounded request on a dedicated GPU, then measure steady state separately from startup. |
