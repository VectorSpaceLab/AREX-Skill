---
name: cli-and-serving
description: "Operate DiscoArt command-line, YAML execution, Jina serving,
  endpoint polling/control, and Docker/Jupyter runtime planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI and Serving

Use this sub-skill when the task asks to use `python -m discoart`, export or run a YAML file from the command line, launch or tune DiscoArt as a Jina service, call `/create`/`/result`/`/skip`/`/stop`, or plan Docker/Jupyter GPU execution.

## Route first

- CLI command syntax, stdin/file behavior, service flow YAML, endpoint calls, Jina Client/curl shapes, Docker/Jupyter notes: read [CLI and serving reference](references/cli-and-serving.md).
- YAML/stdin mistakes, blocked servers, polling mismatches, Jina issues, GPU/OOM, floating requests, and port/protocol confusion: read [Troubleshooting](references/troubleshooting.md).
- Python `create(**kwargs)` parameter meanings, outputs, `DocumentArray` post-processing, generation runtime, and model/cache behavior belong to `../artwork-generation/SKILL.md`.
- Prompt schema, YAML parameter semantics, schedules, default config editing, and config validation belong to `../configuration-and-prompts/SKILL.md`.
- Maintainer release automation, CI scripts, shell release helpers, and packaging publication are out of scope.

## Quick workflow

1. Decide whether the request is a local CLI run, a persistent service run, or a Docker/Jupyter runtime plan. Do not start image generation or a long-lived server unless the user explicitly asks and the GPU/cache/time budget is clear.
2. For local CLI config export, use `python -m discoart config [EXPORT_YAML_FILE]`. With no output path, the default YAML is printed to stdout.
3. For local CLI generation, use `python -m discoart create [YAML_CONFIG_FILE]`. With no file path, `create` reads YAML from stdin; avoid leaving it waiting on an interactive terminal by accident.
4. For serving, generate or edit a Jina Flow YAML, then run `python -m discoart serve [FLOW_YAML_FILE]`. The command loads the flow and blocks the terminal until interrupted.
5. For HTTP clients, post JSON to the Jina gateway `/post` route with `execEndpoint`. Use a stable `name_docarray` in `/create` if the workflow needs `/result` polling.
6. For gRPC or non-HTTP gateways, use `jina.Client(...).post(endpoint, parameters=...)`; the service endpoints remain `/create`, `/result`, `/skip`, and `/stop`.
7. For Docker, preserve bind mounts for working output and model cache, pass GPU access explicitly, and carry required environment variables such as `DISCOART_OUTPUT_DIR`, `DISCOART_CACHE_DIR`, `DISCOART_DEFAULT_PARAMETERS_YAML`, and `WANDB_MODE` into the container.
8. Verify safely with parser/config/help smoke tests and the bundled helper's `--help`; do not run full generation, Docker, or persistent service checks by default.

## Fast validation anchors

- Root parser usage is `python -m discoart [-h] [-v] {create,config,serve} ...`.
- `config` accepts optional `EXPORT_YAML_FILE` and defaults to stdout.
- `create` accepts optional `YAML_CONFIG_FILE` and defaults to stdin.
- `serve` accepts optional `FLOW_YAML_FILE` and defaults to DiscoArt's packaged Jina flow.
- Service executor endpoints are `/create`, `/skip`, and `/stop`; result polling endpoint is `/result`.
- The default flow uses HTTP port `51001`, monitoring port `51002`, `DiscoArtExecutor`, `ResultPoller`, `replicas: 1`, and `floating: false`.
- The bundled helper at `scripts/service_config_helper.py` prints flow YAML only; it never launches a server, downloads models, opens ports, or writes files by default.
