---
name: web-demo
description: "Builds and troubleshoots HunyuanVideo Gradio web-demo launch
  commands, UI option mapping, server binding, and output behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo Web Demo

Use this sub-skill when the user asks for the HunyuanVideo Gradio interface, web demo, browser UI, local server, `SERVER_NAME`, `SERVER_PORT`, or UI-specific behavior. Route checkpoint and CUDA readiness to `../checkpoint-and-setup/SKILL.md`, single-GPU CLI/API sampling to `../inference/SKILL.md`, and FP8/xDiT optimization to `../parallel-and-optimization/SKILL.md`.

## Read first

- `references/gradio-workflow.md` for launch commands, UI defaults, and option mapping.
- `references/troubleshooting.md` for model path, port, binding, checkpoint, and output-location issues.
- `scripts/build_gradio_command.py` to create a safe launch command without starting a server.
- `scripts/run_gradio_server.py` is the bundled service runner; execute it only when checkpoints, CUDA, and service exposure are approved.

## Safe launch planning

Prefer localhost binding unless the user explicitly asks for LAN/public exposure:

```bash
python sub-skills/web-demo/scripts/build_gradio_command.py \
  --model-base ckpts \
  --server-name 127.0.0.1 \
  --server-port 7860 \
  --flow-reverse
```

The helper prints a command using the bundled `run_gradio_server.py` runner. It does not bind a port or load model weights.

## Execution boundaries

Starting Gradio is a real service and generation still requires the full HunyuanVideo CUDA/checkpoint stack. Do not run it as a verification smoke test unless the user approves a service launch and GPU/model use.
