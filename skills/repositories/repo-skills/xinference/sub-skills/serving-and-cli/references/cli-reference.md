# CLI reference

This page captures the public CLI surface used by this sub-skill. It stays close to the installed help and the current command parser.

## Console entry points

- `xinference` - top-level command group; bare `xinference` startup is deprecated, so prefer `xinference-local`.
- `xinference-local` - start a local cluster.
- `xinference-supervisor` - start a distributed supervisor and service endpoint.
- `xinference-worker` - start a worker and join a supervisor-managed cluster.

## Top-level options

The `xinference` group exposes:

- `-v`, `--version`
- `--log-level`
- `-H`, `--host`
- `-p`, `--port`

## Service startup commands

### Local cluster

```bash
xinference-local --host <LOCAL_BIND_HOST> --port <SERVICE_PORT> --log-level INFO
```

- Spawns the local supervisor and worker automatically.
- `--metrics-exporter-host` controls the exporter bind host; `--metrics-exporter-port` sets its port.
- Use `0.0.0.0` only when you intentionally want remote access.

### Supervisor

```bash
xinference-supervisor -H <SUPERVISOR_BIND_HOST> -p <SERVICE_PORT> --supervisor-port <SUPERVISOR_PORT>
```

- `-p` is the API/Web UI service port.
- `--supervisor-port` is the internal supervisor port used by workers.
- Use `0.0.0.0` when exposing the service outside the host or container.

### Worker

```bash
xinference-worker -e http://<SUPERVISOR_HOST>:<SERVICE_PORT> -H <WORKER_BIND_HOST> --worker-port <WORKER_PORT> --metrics-exporter-host <METRICS_HOST> --metrics-exporter-port <METRICS_PORT>
```

- `-e`, `--endpoint` points to the supervisor service endpoint.
- The worker joins the cluster through the supervisor, not through the internal worker port.

## Model launch

```bash
xinference launch -e <ENDPOINT> -n <MODEL_NAME> -t LLM -en <MODEL_ENGINE> -u <MODEL_UID> -s <SIZE_IN_BILLIONS> -f <MODEL_FORMAT> -q <QUANTIZATION> -r <REPLICA> --n-worker <N_WORKER> --n-gpu <N_GPU> --worker-ip <WORKER_IP:PORT> --gpu-idx <GPU_IDX,COMMA_SEPARATED> --trust-remote-code true -ak <API_KEY> -mp <MODEL_PATH> --enable-thinking --enable-virtual-env --virtual-env-package <PACKAGE_SPEC> --env KEY VALUE
```

- `-n`, `--model-name` is required.
- `-t`, `--model-type` defaults to `LLM`.
- `-en`, `--model-engine` is required for LLM launches.
- `-r`, `--replica` sets the number of replicas.
- `--n-worker` sets the number of workers used by a distributed launch.
- `--n-gpu` accepts `auto`, `none`, or an integer string.
- `--worker-ip` must be the full registered worker address.
- `--gpu-idx` is a comma-separated list of GPU indexes.
- `--enable-virtual-env` and `--disable-virtual-env` are mutually exclusive.
- `--virtual-env-package` and `--env` may repeat.
- Extra backend-specific kwargs must appear after the known flags as `--key value` pairs.
- `--model_path` remains a legacy compatibility alias for `--model-path`.
- Optional launch extras also include `--trust-remote-code`, `--enable-thinking`, `-lm/--lora-modules`, `-qc/--quantization-config`, `-ld/--image-lora-load-kwargs`, and `-fd/--image-lora-fuse-kwargs`.

## Model state and lifecycle

### List and terminate

```bash
xinference list -e <ENDPOINT> -ak <API_KEY>
xinference terminate -e <ENDPOINT> --model-uid <MODEL_UID> -ak <API_KEY>
```

### Registrations and custom models

```bash
xinference registrations -e <ENDPOINT> --model-type LLM -ak <API_KEY>
xinference register -e <ENDPOINT> --model-type LLM --file <MODEL_CONFIG_FILE> --worker-ip <WORKER_IP:PORT> --persist -ak <API_KEY>
xinference unregister -e <ENDPOINT> --model-type LLM --model-name <MODEL_NAME> -ak <API_KEY>
```

- `register` uses `--file` for the model config and `--persist` to keep the registration across restarts.
- Supported registration types include `LLM`, `embedding`, `rerank`, `image`, `audio`, and `flexible`.

### Cache inspection and cleanup

```bash
xinference cached -e <ENDPOINT> --model_name <MODEL_NAME> --worker-ip <WORKER_IP:PORT> -ak <API_KEY>
xinference remove-cache -e <ENDPOINT> --model_version <MODEL_VERSION> --worker-ip <WORKER_IP:PORT> -ak <API_KEY>
```

- `cached` uses the underscore form `--model_name` in the parser.
- `remove-cache` uses the underscore form `--model_version`.
- `--check` is the confirmation/bypass flag for interactive deletion flows.

### Planning and compatibility

```bash
xinference engine -e <ENDPOINT> -n <MODEL_NAME> --model-engine <MODEL_ENGINE> --model-format <MODEL_FORMAT> --model-size-in-billions <SIZE_IN_BILLIONS> --quantization <QUANTIZATION> -ak <API_KEY>
xinference cal-model-mem -n <MODEL_NAME> --size-in-billions <SIZE_IN_BILLIONS> --model-format <MODEL_FORMAT> --quantization <QUANTIZATION> --context-length <CONTEXT_LENGTH>
xinference vllm-models -e <ENDPOINT> -ak <API_KEY>
```

- `engine` prints supported engine/format/size/quantization combinations.
- `cal-model-mem` requires `--context-length`.
- `vllm-models` lists model families compatible with vLLM.

### Cluster access and shutdown

```bash
xinference login -e <ENDPOINT> --username <USERNAME> --password <PASSWORD>
xinference stop-cluster -e <ENDPOINT> -ak <API_KEY>
```

- `stop-cluster` is destructive and should be reviewed carefully.
- Use `login` only when the cluster expects authenticated access.

## Command-construction reminders

- `launch` needs `--model-engine` for LLMs.
- `--worker-ip` must be the full registered `IP:port`.
- `--gpu-idx` is comma-separated integers.
- `--n-gpu none` disables GPU binding; `auto` lets Xinference choose.
- `replica` counts model copies, while `n-worker` counts worker machines and `n-gpu` counts GPUs per worker in distributed mode.
- Use `--enable-virtual-env` or `--disable-virtual-env`, not both.
- Pass engine-specific extras as trailing `--key value` pairs.
- `chat` and `generate` exist for interactive prompting against a running model, but they are intentionally not covered here.
