# GPU workers and queues

CUDA/GPU support is optional for this generated skill. The verified required
backend is CPU. Treat GPU queues as an operations surface to configure and
monitor, not as a required model-stack capability.

## Queue names

The platform recognizes these queue classes:

| Queue | Intended work |
|---|---|
| `default` | general compare/create/search jobs and catch-all background jobs |
| `cpu-heavy` | long CPU tuning/search jobs that should not starve default jobs |
| `gpu` | jobs that request CUDA-visible workers |
| `inference` | lightweight latency-sensitive prediction work |

Explicit queue selection comes from `plan_params.queue` or
`setup_params.queue`. Without an explicit queue, runs with `use_gpu=True` route
to `gpu`; otherwise they route to `default`. Allowed queue names outside this
set fall back to `default`.

For search-style runs, any `use_gpu` on the base setup, plan params, or variants
pushes the whole search to the `gpu` queue. Mixed CPU/GPU variant search is not
supported in this cut; pin a queue explicitly when separating work.

## In-process versus Redis workers

Single-process local mode:

```bash
export PYCARET_RUNS_BACKEND=inprocess
pycaret-server serve --port 8020
```

The API process executes jobs itself. Redis workers and queue separation are not
required.

Distributed worker mode:

```bash
export PYCARET_RUNS_BACKEND=redis
export PYCARET_REDIS_URL='redis://redis:6379/0'
pycaret-server serve --host 0.0.0.0 --port 8020
pycaret-server worker --queues default,cpu-heavy --worker-id cpu-1
```

Every worker needs the same DB, Redis, storage, and Fernet settings as the API.
Queue order matters: a worker with `--queues gpu,default` tries `gpu` before
`default` when both queues have jobs.

## GPU detection

The worker uses a process-local GPU inventory probe:

1. `CUDA_VISIBLE_DEVICES` environment override.
   - unset: continue to library/system probes.
   - empty string: explicitly no GPUs.
   - `0,1`: two CUDA devices, reported as `cuda:0` and `cuda:1`.
2. `pynvml`, when importable.
3. `nvidia-smi -L`, when available.
4. otherwise no GPU.

The result is cached per process. Restart the worker after changing GPU-related
environment variables, drivers, or container device visibility.

## GPU worker startup

A GPU worker should listen only where it has GPU visibility:

```bash
export PYCARET_RUNS_BACKEND=redis
export PYCARET_REDIS_URL='redis://redis:6379/0'
export CUDA_VISIBLE_DEVICES=0
pycaret-server worker --queues gpu --worker-id gpu-1
```

Containerized GPU workers also need runtime/device wiring from the orchestrator,
for example Docker `--gpus all` or a Kubernetes GPU resource limit. The
production-shaped Compose file in this snapshot starts only a `default` worker;
add GPU workers explicitly if GPU jobs are expected.

## GPU routing guard

A worker refuses to run a job whose queue is `gpu` or whose requested resources
include `gpu >= 1` unless `detect_gpus().available` is true. If a CPU-only
worker picks up such a job, it releases the job back to `queued` and re-enqueues
it instead of failing it permanently.

Troubleshooting signal:

- Jobs stay queued on `gpu` with no progress.
- Worker logs mention no GPU available with a probe source such as `env`,
  `pynvml`, `nvidia-smi`, or `none`.
- `/api/v1/admin/system` reports no GPU for the API process. Note that this is
  the API process inventory, not a per-worker inventory.

Fix:

1. Start a worker that listens on `gpu`.
2. Ensure that worker has CUDA devices visible.
3. Confirm `CUDA_VISIBLE_DEVICES` is not an empty string.
4. If containerized, confirm GPU runtime/resource limits expose devices inside
   the worker container.
5. Re-run a GPU-queued job or requeue stuck jobs after fixing visibility.

## Admin checks

Authenticated endpoints:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/admin/queues
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/admin/workers
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/admin/system
```

`/admin/queues` returns per-queue counts for `queued`, `running`, `succeeded`,
`failed`, `cancelled`, and recent one-hour throughput.

`/admin/workers` derives active workers from currently locked running jobs. It
is not a full heartbeat registry; idle workers may not appear.

`/admin/system` reports process-local Redis health, GPU inventory, runs backend,
and configured worker queue names.

## Helm/Kubernetes GPU target status

The values file describes a target where GPU workers use `worker.queues=gpu` and
a GPU resource limit such as `nvidia.com/gpu=1`. In this verified snapshot, the
Helm path is not proven production-complete; validate templates and cluster
scheduling before relying on it.

Minimum Kubernetes checks for a future GPU worker pool:

```bash
kubectl -n pycaret get pods -o wide
kubectl -n pycaret describe pod <gpu-worker-pod>
kubectl -n pycaret exec <gpu-worker-pod> -- nvidia-smi -L
kubectl -n pycaret exec <gpu-worker-pod> -- pycaret-server doctor
```

Then submit a run with `setup_params.use_gpu=true` or `setup_params.queue=gpu`
and watch `/api/v1/admin/queues`.
