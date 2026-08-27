# DiscoArt CLI and Serving Reference

This reference covers command-line and service workflows for DiscoArt. It is self-contained: use it to plan commands, flow YAML, HTTP/gRPC requests, and Docker/Jupyter execution without reopening the source checkout.

## Scope and safety

- `python -m discoart config` is safe: it exports a YAML template and does not generate art.
- `python -m discoart create` starts Disco Diffusion generation from YAML. It can download or load models, allocate GPU/CPU memory, write outputs, and run for minutes or longer.
- `python -m discoart serve` launches a persistent Jina Flow and blocks the process. Starting the service opens a port and may later run GPU workloads when `/create` is called.
- The bundled `scripts/service_config_helper.py` only prints Jina Flow YAML; it does not import Jina, launch a server, download models, or write files unless shell redirection is used.
- Prompt/config parameter meaning belongs to the configuration-and-prompts sub-skill. Generation output, `create(**kwargs)`, model/cache details, and `DocumentArray` post-processing belong to the artwork-generation sub-skill.

## CLI command surface

The parser exposes a required subcommand:

```text
python -m discoart [-h] [-v] {create,config,serve} ...
```

Commands:

```bash
python -m discoart --help
python -m discoart --version
python -m discoart config [EXPORT_YAML_FILE]
python -m discoart create [YAML_CONFIG_FILE]
python -m discoart serve [FLOW_YAML_FILE]
```

Important positional behavior:

- `config [EXPORT_YAML_FILE]`: writes the default parameter YAML to the given file. If no output path is given, it writes YAML to stdout.
- `create [YAML_CONFIG_FILE]`: reads YAML parameters from the given file. If no file path is given, it reads from stdin.
- `serve [FLOW_YAML_FILE]`: loads a Jina Flow config. If no flow file is supplied, it uses DiscoArt's packaged default flow.
- `create --help`, `config --help`, and `serve --help` are parser-only checks and should exit without launching generation or a service.
- The CLI modules set `DISCOART_DISABLE_IPYTHON=1` for command-line use.

## Exporting a YAML config

Create a starter YAML file:

```bash
python -m discoart config my-run.yml
```

Print the default YAML to stdout:

```bash
python -m discoart config
```

Redirect stdout into a file:

```bash
python -m discoart config > my-run.yml
```

Use a custom default YAML as the export source:

```bash
DISCOART_DEFAULT_PARAMETERS_YAML=/abs/path/team-default.yml \
  python -m discoart config my-run.yml
```

The exported file is a parameter file for `create`, not a Jina Flow file for `serve`. Edit prompt text, schedules, dimensions, model choices, and other generation parameters with the configuration-and-prompts sub-skill.

## Running generation from YAML

Run a YAML file:

```bash
python -m discoart create my-run.yml
```

Pipe YAML through stdin:

```bash
cat my-run.yml | python -m discoart create
```

Use environment variables to keep output and cache locations stable:

```bash
export DISCOART_OUTPUT_DIR="$PWD/discoart-output"
export DISCOART_CACHE_DIR="$HOME/.cache/discoart"
export WANDB_MODE=disabled
python -m discoart create my-run.yml
```

`create` loads the YAML into keyword arguments and passes them to DiscoArt's Python `create()` function. A YAML document must therefore be a mapping/object, not a list, plain string, or empty stream.

## Serving through Jina Flow

Start with the default flow:

```bash
python -m discoart serve
```

Start with a custom flow file:

```bash
python -m discoart serve myflow.yml
```

The service command imports Jina, loads the flow config, enters the Flow context, and blocks the terminal. Use a separate terminal, `tmux`, `systemd`, Docker, or a process supervisor only when the user explicitly wants a persistent service.

A distilled equivalent of the packaged default flow is:

```yaml
jtype: Flow
with:
  protocol: http
  monitoring: true
  cors: true
  port: 51001
  port_monitoring: 51002
  env:
    JINA_LOG_LEVEL: debug
    DISCOART_DISABLE_IPYTHON: 1
    DISCOART_DISABLE_RESULT_SUMMARY: 1
    WANDB_MODE: disabled
executors:
  - name: discoart
    uses: DiscoArtExecutor
    env:
      CUDA_VISIBLE_DEVICES: RR0:2
    replicas: 1
    floating: false
  - name: poller
    uses: ResultPoller
```

Generate a minimal custom flow from this sub-skill directory:

```bash
python scripts/service_config_helper.py \
  --protocol http \
  --port 51001 \
  --replicas 1 \
  --cuda-visible-devices 0 \
  > myflow.yml
python -m discoart serve myflow.yml
```

Enable an immediately-returning `/create` endpoint only when request rate is controlled:

```bash
python scripts/service_config_helper.py \
  --floating \
  --replicas 1 \
  --cuda-visible-devices 0 \
  > myflow-floating.yml
python -m discoart serve myflow-floating.yml
```

Scaling pattern for multiple GPUs:

```yaml
executors:
  - name: discoart
    uses: DiscoArtExecutor
    env:
      CUDA_VISIBLE_DEVICES: RR0:3
    replicas: 3
    floating: false
  - name: poller
    uses: ResultPoller
```

`replicas: 3` starts three DiscoArt executor replicas. `CUDA_VISIBLE_DEVICES: RR0:3` requests round-robin use of the first three GPU slots. Keep `floating: false` unless the client or backend-for-frontend controls concurrency; otherwise several `/create` calls may run in parallel and exhaust GPU memory.

## Service endpoints and behavior

The service exposes these executor endpoints:

| Endpoint | Owner | Behavior |
|---|---|---|
| `/create` | `DiscoArtExecutor` | Calls `create(init_document=docs, skip_event=..., stop_event=..., **parameters)`. Parameters are the same keyword arguments accepted by the Python generation API. |
| `/result` | `ResultPoller` | Reads the persisted `da.protobuf.lz4` for `parameters['name_docarray']` and returns a `DocumentArray` when it exists. |
| `/skip` | `DiscoArtExecutor` | Sets the executor's skip event so the current run moves to the next batch when supported by the generation loop. |
| `/stop` | `DiscoArtExecutor` | Sets the executor's stop event to cancel remaining batches for the current executor. |

Use a stable `name_docarray` in `/create` whenever `/result` polling is required. The same `name_docarray` must be used in `/result`, and the poller must see the same output directory as the creator.

`/skip` and `/stop` are executor-level controls, not named-run controls. In a floating or replicated service, use them carefully because they target the active executor state rather than a specific `name_docarray`.

## HTTP request shapes

For HTTP protocol, Jina's gateway accepts POST requests at `/post` with `execEndpoint` selecting the DiscoArt endpoint.

Set a base URL:

```bash
BASE=http://127.0.0.1:51001
RUN_NAME=mydisco-123
```

Start a named run:

```bash
curl -sS -X POST "$BASE/post" \
  -H 'Content-Type: application/json' \
  -d '{"execEndpoint":"/create","parameters":{"name_docarray":"mydisco-123","text_prompts":["A beautiful painting of a singular lighthouse","yellow color scheme"]}}'
```

Poll the named run:

```bash
curl -sS -X POST "$BASE/post" \
  -H 'Content-Type: application/json' \
  -d '{"execEndpoint":"/result","parameters":{"name_docarray":"mydisco-123"}}'
```

Skip the current batch on the active executor:

```bash
curl -sS -X POST "$BASE/post" \
  -H 'Content-Type: application/json' \
  -d '{"execEndpoint":"/skip"}'
```

Stop remaining batches on the active executor:

```bash
curl -sS -X POST "$BASE/post" \
  -H 'Content-Type: application/json' \
  -d '{"execEndpoint":"/stop"}'
```

For HTTP polling loops, wait between polls and tolerate empty/no-result responses until the result file is written. Do not send rapid `/create` bursts to a floating service unless another layer rate-limits them.

## Jina Client request shapes

Use a Jina Client for gRPC, websocket, or HTTP clients that should call executor endpoints directly.

```python
from jina import Client

run_name = 'mydisco-123'
c = Client(host='grpc://127.0.0.1:51001')

# Start generation. For HTTP Client usage, use an http:// host instead.
da = c.post(
    '/create',
    parameters={
        'name_docarray': run_name,
        'text_prompts': [
            'A beautiful painting of a singular lighthouse',
            'yellow color scheme',
        ],
    },
)

# Poll intermediate or completed results.
da = c.post('/result', parameters={'name_docarray': run_name})

# Executor-level controls. Use cautiously in replicated/floating deployments.
c.post('/skip')
c.post('/stop')
```

Send an existing `Document` or `DocumentArray` as initialization data by passing it as the request data to `/create`; follow-up `parameters` override values from the initial document where DiscoArt supports that behavior.

## Docker and Jupyter runtime notes

Use a prebuilt image when possible:

```bash
docker pull jinaai/discoart:latest
```

Start the default Jupyter notebook entrypoint with GPU and cache mounts:

```bash
docker run \
  -p 51000:8888 \
  -v "$PWD":/home/jovyan/ \
  -v "$HOME/.cache":/root/.cache \
  --gpus all \
  jinaai/discoart:latest
```

Then open `http://127.0.0.1:51000` in a browser. The image's default command starts Jupyter on container port `8888`.

Run the image as a DiscoArt service instead of Jupyter:

```bash
docker run \
  --entrypoint python \
  -p 51001:51001 \
  -v "$PWD":/home/jovyan/ \
  -v "$HOME/.cache":/root/.cache \
  --gpus all \
  -e DISCOART_OUTPUT_DIR=/home/jovyan/discoart-output \
  -e DISCOART_CACHE_DIR=/root/.cache/discoart \
  -e WANDB_MODE=disabled \
  jinaai/discoart:latest \
  -m discoart serve
```

If using a custom flow file, mount it into the container and pass its container path:

```bash
docker run \
  --entrypoint python \
  -p 51001:51001 \
  -v "$PWD":/home/jovyan/ \
  -v "$HOME/.cache":/root/.cache \
  --gpus all \
  jinaai/discoart:latest \
  -m discoart serve /home/jovyan/myflow.yml
```

Runtime planning checklist:

- GPU access: pass `--gpus all` and ensure the host has an NVIDIA container runtime. On Windows, use a WSL setup with CUDA-capable Docker GPU support.
- Cache persistence: mount `$HOME/.cache` or a dedicated cache volume to avoid repeated model downloads.
- Output persistence: mount a working directory and set `DISCOART_OUTPUT_DIR` inside the container if results must survive container removal.
- Port mapping: map host `51001` to container `51001` for service mode, and host `51000` or another host port to container `8888` for Jupyter mode.
- Version pinning: replace `latest` with a concrete image tag when reproducibility matters.
- WandB/no-notebook behavior: set `WANDB_MODE=disabled`, `DISCOART_DISABLE_IPYTHON=1`, and `DISCOART_DISABLE_RESULT_SUMMARY=1` for headless services.

## Hosting and protocol notes

- HTTP is convenient for curl and browser-facing gateways. Use `protocol: http` and send JSON to `/post`.
- gRPC is preferred behind a backend-for-frontend or internal service boundary because it has lower overhead and richer transport features. Use `protocol: grpc` and `jina.Client(host='grpc://host:port')`.
- Websocket support is Jina-protocol dependent; keep endpoint names the same and adjust the client host/protocol accordingly.
- Hosting from transient notebook runtimes can work for demos but is not recommended for reliable service: GPU availability, sleep/idle timeouts, reverse tunnels, and exposed credentials must be managed outside DiscoArt.
