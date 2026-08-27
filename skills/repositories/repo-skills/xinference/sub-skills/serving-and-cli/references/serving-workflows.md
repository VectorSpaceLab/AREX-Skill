# Serving workflows

Choose the smallest command sequence that answers the operational question. Keep the model, backend, and deployment scope separate from Python client or auth policy work.

## 1. Single-machine startup

1. Start the local cluster.
2. Query compatible engines if the model is an LLM.
3. Launch the model.
4. List and terminate as needed.

```bash
xinference-local --host 127.0.0.1 --port 9997
xinference engine -e http://127.0.0.1:9997 -n <MODEL_NAME>
xinference launch -e http://127.0.0.1:9997 -n <MODEL_NAME> -t LLM -en <MODEL_ENGINE> -s <SIZE_IN_BILLIONS> -f <MODEL_FORMAT> -q <QUANTIZATION>
xinference list -e http://127.0.0.1:9997
xinference terminate -e http://127.0.0.1:9997 --model-uid <MODEL_UID>
```

Notes:

- The first launch of a built-in model may download weights or create a per-model virtual environment.
- Use `--enable-virtual-env` when you want the launch to isolate dependencies for that model.
- Use `--disable-virtual-env` only when you intentionally want to override the default isolation.
- Bind to `0.0.0.0` only when you intentionally want remote access.

## 2. Distributed cluster startup

1. Start one supervisor.
2. Start each worker against the supervisor endpoint.
3. Launch the model against the supervisor service endpoint.
4. Use `--n-worker` for worker count and `--n-gpu` for GPUs per worker.
5. Pin placement with `--worker-ip` and `--gpu-idx` when needed.

```bash
xinference-supervisor -H <SUPERVISOR_BIND_HOST> -p 9997 --supervisor-port <SUPERVISOR_PORT>
xinference-worker -e http://<SUPERVISOR_HOST>:9997 -H <WORKER_BIND_HOST> --worker-port <WORKER_PORT>
xinference launch -e http://<SUPERVISOR_HOST>:9997 -n <MODEL_NAME> -t LLM -en <MODEL_ENGINE> --n-worker 2 --n-gpu 1
```

Notes:

- Use full `IP:port` worker addresses when pinning placement.
- `replica_config` is a Python-client-only escape hatch for more precise per-replica placement.
- If the command expects an authenticated cluster, add `-ak <API_KEY>` or use a cached token for that endpoint.

## 3. Safe lifecycle loop

- Discover built-ins with `registrations`.
- Check `engine` or `vllm-models` before committing to a backend choice.
- Estimate memory with `cal-model-mem`.
- Launch with the smallest valid command.
- Verify with `list`.
- Clean up with `terminate`, `remove-cache`, or `stop-cluster` only after review.

## 4. Command-construction checklist

- Use `--endpoint` whenever the command should target a distributed cluster.
- Keep `--worker-ip` in full `IP:port` form.
- Keep `--gpu-idx` comma-separated and unique.
- Use `--enable-virtual-env` or `--disable-virtual-env`, not both.
- Pass engine-specific extras as trailing `--key value` pairs.
- Route Python client bodies to `client-and-api`; route backend selection to `models-and-backends`.
