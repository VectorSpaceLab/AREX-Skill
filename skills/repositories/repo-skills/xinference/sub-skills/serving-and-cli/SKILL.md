---
name: serving-and-cli
description: "Launch and operate Xinference services and model lifecycles
  through public CLI surfaces with safe command templates, placement notes, and
  troubleshooting handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving and CLI

Use this sub-skill when you need to start a local service, stand up a supervisor/worker cluster, or build safe command lines for model launch and lifecycle management.

## Covers

- Local cluster startup with `xinference-local`.
- Distributed startup with `xinference-supervisor` and `xinference-worker`.
- Top-level `xinference` service commands for:
  - `launch`
  - `list`
  - `terminate`
  - `register`
  - `unregister`
  - `registrations`
  - `cached`
  - `remove-cache`
  - `engine`
  - `cal-model-mem`
  - `vllm-models`
  - `stop-cluster`
  - `login`
- Placement and launch flags such as:
  - `--endpoint` / `-e`
  - `--model-name`, `--model-uid`, `--model-type`
  - `--n-worker`, `--n-gpu`, `--replica`
  - `--worker-ip`, `--gpu-idx`
  - `--enable-virtual-env`, `--disable-virtual-env`
  - `--virtual-env-package`, `--env`
  - `--api-key` placeholders

## Does not cover

- Python client calls or HTTP/OpenAI request bodies -> `client-and-api`
- Backend or model-family selection, optional engine installs, or model schema design -> `models-and-backends`
- Auth database, metrics policy, environment policy, or deployment hardening -> `operations-and-security`

## Working pattern

1. Read `references/cli-reference.md` for exact command shapes.
2. Use `scripts/render_xinference_commands.py` to generate copy-paste-safe templates.
3. Read `references/serving-workflows.md` for local, distributed, launch, and shutdown flows.
4. Read `references/distributed-deployment.md` for host/port and worker placement rules.
5. Read `references/troubleshooting.md` when a command fails, blocks, or returns a validation error.

## Safety rules

- Treat bundled command text as templates, not runnable automation.
- Real launches may download models and per-model dependencies.
- `launch` requires `--model-engine` for LLMs.
- Distributed placement must use full registered worker `IP:port` values.
- `--gpu-idx` is a comma-separated list of integers.
- Pass engine-specific extras as `--key value` pairs after the standard `launch` flags.
- Use `--enable-virtual-env` or `--disable-virtual-env`, never both.

## Bundled references

- [CLI reference](references/cli-reference.md)
- [Serving workflows](references/serving-workflows.md)
- [Distributed deployment](references/distributed-deployment.md)
- [Troubleshooting](references/troubleshooting.md)
- [Command renderer](scripts/render_xinference_commands.py)
