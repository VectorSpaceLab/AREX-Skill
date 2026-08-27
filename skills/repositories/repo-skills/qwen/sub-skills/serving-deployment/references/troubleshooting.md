# Serving Troubleshooting

## Local demos

- CLI starts downloading unexpectedly: the checkpoint argument is a remote model id. Use a verified local directory when network/storage is not approved.
- Web demo exposes publicly: `--share` or `--server-name 0.0.0.0` was used. Bind to loopback unless exposure is intended.
- CPU demo appears stuck: CPU generation can be extremely slow. Use a smaller model, GPU, or service backend.

## OpenAI-compatible API

- `Invalid request: Expecting at least one user message`: the message list lacks a `user` role.
- `Expecting role assistant before role function`: a `function` message must follow an assistant tool call.
- Function calling with `stream=True`: unsupported by the repository API server; use `stream=False`.
- No auth challenge when expected: verify `--api-auth username:password` and that clients send BasicAuth credentials.
- Server works locally but not remotely: check `--server-name`, firewall, Docker port mapping, and reverse proxy.

## Docker

- `Checkpoint config.json file not found`: wrong host path or incomplete checkpoint. Fix the source mount.
- Container cannot see GPU: verify `nvidia-smi` on host and `docker run --rm --gpus all ubuntu nvidia-smi` before Qwen-specific debugging.
- Image pull is slow or fails: this is a network/registry issue, not a Qwen script issue.
- Port already in use: change host port or stop the old container.

## vLLM/FastChat

- Worker fails on dtype: switch BF16/FP16 according to GPU and quantization.
- Multi-GPU worker fails for Int4: reduce tensor parallel size or use a supported quantized layout.
- Requests hang: confirm controller, worker, and API server are all running and connected.
- Responses have wrong chat format: use the Qwen ChatML template for standalone vLLM API.

## Vendor hardware

Ascend and DCU failures require vendor-specific logs and device tools. Do not try to fix them by installing CUDA packages. Confirm device files, driver mounts, image tag, vendor environment scripts, and converted model format first.
