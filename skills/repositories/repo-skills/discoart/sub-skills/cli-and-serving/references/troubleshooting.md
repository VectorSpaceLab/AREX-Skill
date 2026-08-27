# DiscoArt CLI and Serving Troubleshooting

Use this checklist for command-line, Jina service, endpoint, and Docker/Jupyter failures. For command shapes and flow YAML examples, see [CLI and serving reference](cli-and-serving.md).

## CLI help/config smoke fails

Symptoms:

- `python -m discoart --help` does not show `{create,config,serve}`.
- `python -m discoart config /tmp/default.yml` exits nonzero.
- Parser help prints unrelated import/runtime errors.

Checks:

1. Ensure the environment imports the intended DiscoArt package, not an unrelated checkout or stale install.
2. Run parser-only commands before expensive commands:
   ```bash
   python -m discoart --help
   python -m discoart create --help
   python -m discoart serve --help
   ```
3. If import-time remote model checks print timeout or remote-list warnings, treat them as network-sensitive warnings unless the command exits nonzero. Set `DISCOART_DISABLE_REMOTE_MODELS=1` for offline runs that should not check the remote model list.
4. If `config` fails, check `DISCOART_DEFAULT_PARAMETERS_YAML`; when set, it must point to a readable YAML file.

## `create` appears to hang before doing anything

Likely cause: `python -m discoart create` with no positional YAML file reads from stdin. In an interactive terminal it waits for input until EOF.

Fixes:

```bash
python -m discoart create my-run.yml
# or
cat my-run.yml | python -m discoart create
# or finish manual stdin with Ctrl-D on Unix-like terminals
```

Do not confuse `create` with `config`: `config` exports a YAML template, while `create` consumes YAML and starts generation.

## YAML is accepted by the wrong command

Common mismatches:

- Passing a Jina Flow YAML to `python -m discoart create`.
- Passing a DiscoArt generation-parameter YAML to `python -m discoart serve`.
- Supplying an empty stdin stream to `create`.
- Supplying a YAML list/string instead of a mapping/object to `create`.

Expected file types:

| Command | YAML shape |
|---|---|
| `python -m discoart create run.yml` | Mapping of DiscoArt generation keyword arguments. |
| `python -m discoart serve flow.yml` | Jina Flow config with `jtype: Flow`, `with:`, and `executors:`. |

If the YAML parses but generation parameters are invalid or prompts/schedules behave unexpectedly, route to the configuration-and-prompts sub-skill.

## `config` writes to the wrong place or prints to terminal

Behavior is parser-defined:

- `python -m discoart config my.yml` writes `my.yml`.
- `python -m discoart config` writes YAML to stdout.
- `python -m discoart config > my.yml` uses shell redirection.

If the exported content is not the expected default, inspect environment variables before import/command execution:

```bash
env | grep '^DISCOART_'
```

Most relevant for `config`:

- `DISCOART_DEFAULT_PARAMETERS_YAML`: overrides the default parameter YAML source.
- `DISCOART_CUT_SCHEDULES_YAML` and `DISCOART_MODELS_YAML`: affect schedule/model helper data used by DiscoArt, not the CLI parser itself.

## `serve` blocks the terminal

This is expected. `python -m discoart serve [FLOW_YAML_FILE]` loads the Jina Flow and calls its blocking runtime. The command does not return until interrupted or the process exits.

Operational options:

- Run it in a separate terminal for manual testing.
- Use `tmux`, `screen`, `systemd`, or a container supervisor for persistent service operation.
- Stop with the process manager or `Ctrl-C` for an interactive foreground service.
- Do not use automated verification that launches `serve` without a timeout and cleanup plan.

## Service starts but endpoint requests fail

Check protocol and route shape:

- HTTP gateway: send POST requests to `http://host:port/post` with JSON containing `execEndpoint`.
- gRPC gateway: use `jina.Client(host='grpc://host:port').post('/endpoint', ...)`.
- The monitoring port is not the request port. Default request port is `51001`; default monitoring port is `51002`.
- `0.0.0.0` is a bind address for servers. Clients on the same host usually use `127.0.0.1` or `localhost`.

HTTP example:

```bash
curl -sS -X POST http://127.0.0.1:51001/post \
  -H 'Content-Type: application/json' \
  -d '{"execEndpoint":"/result","parameters":{"name_docarray":"mydisco-123"}}'
```

If CORS/browser calls fail but curl works, verify the flow has `cors: true` for HTTP and that any reverse proxy forwards POST bodies correctly.

## `/result` returns empty, stale, or mismatched results

`/result` looks for the persisted result file associated with `parameters['name_docarray']`. Typical causes:

1. `/create` did not include `name_docarray`, or `/result` uses a different name.
2. Generation has not yet written the persisted `DocumentArray`; polling too early can return no result.
3. `DISCOART_OUTPUT_DIR` differs between the creator and poller process/container.
4. A replicated or distributed flow does not share the output volume across `DiscoArtExecutor` and `ResultPoller`.
5. A container writes results to an internal path that is not bind-mounted to the host.
6. The run failed before producing `da.protobuf.lz4`; inspect service logs for generation errors.

Safe polling pattern:

```bash
RUN_NAME=mydisco-123
BASE=http://127.0.0.1:51001
for i in 1 2 3 4 5; do
  curl -sS -X POST "$BASE/post" \
    -H 'Content-Type: application/json' \
    -d "{\"execEndpoint\":\"/result\",\"parameters\":{\"name_docarray\":\"$RUN_NAME\"}}"
  sleep 10
done
```

For robust automation, add a timeout, backoff, and service-log collection rather than polling forever.

## `/skip` or `/stop` affects the wrong work

`/skip` and `/stop` set events on the active DiscoArt executor. They are not addressed by `name_docarray`.

Risk cases:

- `floating: true` allows multiple `/create` calls to run concurrently.
- `replicas` greater than one means multiple executor instances may exist.
- A shared service receives requests from more than one user or job.

Mitigations:

- Keep `floating: false` for single-user/manual services.
- Put the service behind a backend that serializes or rate-limits create requests.
- Avoid offering `/skip` and `/stop` directly to untrusted clients.
- Prefer one service instance per controlled workload when cancellation semantics must be predictable.

## Floating `/create` causes GPU OOM or runaway jobs

When the DiscoArt executor has `floating: true`, `/create` returns immediately and the client must rely on `/result`. It also means client request velocity controls concurrency.

Symptoms:

- Several generation jobs start at once.
- CUDA out-of-memory errors.
- Polling results from several run names never stabilizes.
- Skip/stop controls do not map cleanly to a named request.

Fixes:

- Set `floating: false`.
- Reduce `replicas` to `1`.
- Use a queue or backend-for-frontend to rate-limit `/create`.
- Lower generation memory settings in the generation config, routed through the artwork-generation/configuration sub-skills.
- Restart the service after OOM if CUDA memory is not released cleanly.

## Jina import, class, or version problems

Symptoms:

- `ModuleNotFoundError: No module named 'jina'` when serving.
- Flow loading cannot resolve `DiscoArtExecutor` or `ResultPoller`.
- Flow config rejects `floating`.
- Client protocol calls fail due to version mismatch.

Checks:

1. Parser help should work without launching a flow:
   ```bash
   python -m discoart serve --help
   ```
2. Serving requires an environment where Jina and DiscoArt's executor classes are importable.
3. Use a Jina version that supports the flow syntax and executor `floating` field used by the service config. `floating` is a Jina 3.7-era feature.
4. Keep server and client Jina versions compatible when using `jina.Client`.
5. If custom flow YAML uses bare class names, run from an installed DiscoArt environment so `DiscoArtExecutor` and `ResultPoller` can be resolved.

## GPU and memory failures

DiscoArt generation is practical on CUDA GPUs but can be memory-heavy.

Checks:

```bash
python - <<'PY'
import torch
print('cuda_available=', torch.cuda.is_available())
print('device_count=', torch.cuda.device_count())
if torch.cuda.is_available():
    print('device0=', torch.cuda.get_device_name(0))
PY
```

Mitigations:

- Set `CUDA_VISIBLE_DEVICES` or flow `env.CUDA_VISIBLE_DEVICES` deliberately.
- Lower `replicas`; start with `1`.
- Keep `floating: false` unless external rate limiting exists.
- Use persistent `DISCOART_CACHE_DIR` so model downloads are not repeated.
- If generation config is too large for VRAM, route to artwork-generation/configuration sub-skills for width/height, steps, CLIP model, and batch adjustments.
- After CUDA OOM, restart the process/container if memory remains fragmented.

## Docker service or Jupyter fails

Common causes and fixes:

- Docker daemon unavailable: start Docker and verify `docker run hello-world` separately.
- GPU not visible: install/configure NVIDIA container runtime and run with `--gpus all`.
- Windows GPU runtime: use WSL with CUDA-capable Docker GPU support.
- Cache is not persistent: bind-mount `$HOME/.cache` or a named cache volume to `/root/.cache`.
- Output disappears after container exit: bind-mount a working directory and set `DISCOART_OUTPUT_DIR` to a path inside that mount.
- Port conflict: choose a different host port, e.g. `-p 51011:51001` for service or `-p 51010:8888` for Jupyter.
- Jupyter works but service does not: the image's default command starts Jupyter; service mode needs `--entrypoint python ... -m discoart serve`.
- Service works in container but not on host: use `127.0.0.1:<host-port>` from the host and ensure the port was published with `-p`.

## Network-sensitive model/cache behavior

CLI and service imports can trigger model-list/version/cache checks, and actual generation can download models. For offline or reproducible runs:

```bash
export DISCOART_CACHE_DIR="$HOME/.cache/discoart"
export DISCOART_DISABLE_REMOTE_MODELS=1
export DISCOART_DISABLE_CHECK_MODEL_SHA=1  # only when local model provenance is trusted
export WANDB_MODE=disabled
```

Use `DISCOART_DISABLE_CHECK_MODEL_SHA=1` only when you intentionally bypass model SHA checks; otherwise keep integrity checks enabled.

## Safe final verification for this sub-skill

Recommended non-generating checks:

```bash
python -m discoart --help
python -m discoart create --help
python -m discoart serve --help
python -m discoart config /tmp/discoart-default.yml
# From the cli-and-serving sub-skill directory:
python scripts/service_config_helper.py --help
python scripts/service_config_helper.py --floating --replicas 2 --cuda-visible-devices RR0:2 > /tmp/discoart-flow.yml
```

Do not include unbounded `python -m discoart serve`, Docker build/run, or real `/create` generation in default verification unless the test plan has explicit timeout, GPU, cache, port, and cleanup controls.
