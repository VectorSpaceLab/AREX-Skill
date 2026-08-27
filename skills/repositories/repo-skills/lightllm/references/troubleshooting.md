# Troubleshooting

This page collects failures that cut across serving, model selection,
deployment, and benchmark workflows.

## Install or import failures

### Symptom
`ImportError`, `ModuleNotFoundError`, or `python -m pip check` reports broken
requirements.

### Likely causes
- The target package is not installed in the inspection environment.
- A required runtime dependency is missing, especially `fastapi`, `uvloop`,
  `ujson`, `setproctitle`, `prometheus_client`, `rpyc`, `litellm`, `einops`,
  or `sortedcontainers`.
- The wrong Python environment is being used.
- The current directory or `PYTHONPATH` is masking the installed package.

### Recovery
- Re-run `python -m pip check` in the intended prefix.
- Confirm `import lightllm` succeeds from the target environment.
- Use `python -I` when possible so local paths do not hide installation issues.
- Rebuild the private inspection environment if dependency drift occurred.

## CUDA or backend failures

### Symptom
CUDA import warnings, `torch.cuda.is_available() == false`, missing custom
kernel messages, or backend validation failures.

### Likely causes
- The installed torch wheel does not match the host CUDA stack.
- The host driver or GPU is incompatible with the selected wheel.
- Optional kernel packages such as `sgl_kernel`, `vllm`, `deep_ep`, or
  `flashinfer` are not installed.
- A selected model/backend combination requires a backend the host does not
  provide.

### Recovery
- Re-run the CUDA smoke script and confirm device count and capability.
- Keep required backend claims separate from optional backend claims.
- Accept optional backend gaps only when the selected workflow does not depend
  on them.
- Revisit the model/runtime route if the selected backend is not available.

## Server startup failures

### Symptom
The process exits early, binds no port, or reports readiness while the model
is still loading.

### Likely causes
- Invalid CLI flags or a mismatched `StartArgs` combination.
- Port collisions.
- Missing model files or a bad `--model_dir`.
- `pd_master` / `prefill` / `decode` processes started in the wrong order.

### Recovery
- Check `python -m lightllm.server.api_server --help` and the CLI reference.
- Use the bundled topology reference before retrying a PD launch.
- Prefer readiness probes over health probes for launch validation.
- Keep logs for each process separate when debugging multi-process topologies.

## API misuse

### Symptom
4xx responses, streaming that never terminates, or malformed JSON payloads.

### Likely causes
- Wrong request envelope for `/generate` vs `/v1/completions` vs
  `/v1/chat/completions` vs `/v1/messages`.
- Multimodal content not encoded as structured message blocks.
- Tool-call or reasoning settings do not match the model/template.
- Client is not prepared for SSE-style streaming responses.

### Recovery
- Compare the request against `references/api-reference.md`.
- Use `scripts/request_smoke.py` to reproduce a small local call.
- Check whether the route expects a chat message list, a completion prompt, or
  a LightLLM-native input string.

## Proxy and localhost issues

### Symptom
Requests to a local LightLLM server fail only when proxy variables are set.

### Likely causes
- `http_proxy` or `https_proxy` still points local traffic through a proxy.
- `no_proxy` does not include localhost or the PD master host.

### Recovery
- Clear proxy variables for local service checks.
- Add `localhost`, `127.0.0.1`, and the PD master host to `no_proxy` when
  benchmarking or warmup traffic stays on the local machine.

## Optional dependency warnings

### Symptom
The server imports but logs warnings about optional backends.

### Likely causes
- `litellm` is missing for Anthropic message translation.
- `uvloop` or `ujson` is missing on the OpenAI path.
- `sgl_kernel`, `vllm`, `deep_ep`, or similar accelerators are unavailable.

### Recovery
- Treat these as optional unless the selected workflow depends on them.
- Do not claim the corresponding route is fully verified until the dependency
  is present and the route is smoke-tested.

## Staleness and evidence drift

### Symptom
The bundled skill no longer matches the repository version or package
metadata.

### Likely causes
- The repo was updated after the skill was generated.
- Public APIs, CLI flags, or model routing changed.

### Recovery
- Refresh the provenance note and routing metadata.
- Re-read the source files that changed and update the affected sub-skill
  reference rather than patching only the root router.
