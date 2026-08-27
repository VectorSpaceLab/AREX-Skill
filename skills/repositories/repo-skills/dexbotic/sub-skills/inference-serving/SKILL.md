---
name: inference-serving
description: "Serve and consume Dexbotic VLA/VLM policies through the legacy or
  v1 HTTP APIs and the BasePolicy contract."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic inference serving

Use this route for policy wrappers, HTTP server/client contracts, action chunks, reset semantics, capability discovery, and optional DM0 realtime serving. Read [HTTP and policy contract](references/http-and-policy.md) before wiring a client and [troubleshooting](references/troubleshooting.md) when requests fail. Route benchmark setup and hardware bridges to [evaluation-deployment](../evaluation-deployment/SKILL.md).

## Operating sequence

1. Start from a checkpoint whose model family, processor/tokenizer, action dimension, camera order, normalization stats, and control mode are known.
2. Query `GET /health`, then `GET /v1/capabilities`; do not guess whether state is required or whether actions are absolute/relative.
3. Build one observation with 1-based image slots, a prompt, and state only when required/used. For the Python client, convert RGB arrays correctly and choose `use_delta` from the declared action mode.
4. Send a bounded request with `sampling.num_steps`, `cfg_scale`, and optional `seed`; verify the action chunk shape and units before passing actions to a robot or simulator.
5. Call `/v1/reset` at episode boundaries for stateful policies such as MemVLA. Treat a reset failure as a session boundary problem, not a model-quality result.
6. Use the legacy `/process_frame` route only when the consumer requires multipart compatibility.

No server, checkpoint download, physical control loop, or Triton weight conversion is run by the bundled smoke helper unless explicitly requested with a reachable local URL.
