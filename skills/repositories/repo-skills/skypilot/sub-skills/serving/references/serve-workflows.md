# SkyServe Workflows

This reference distills SkyServe service authoring and operations into self-contained patterns for future agents. SkyServe deploys an HTTP-serving task across replicas, monitors readiness, routes traffic through a load balancer, and can recover or autoscale replicas.

## Minimal Service YAML

A service YAML is a normal SkyPilot task with an added `service:` section:

```yaml
service:
  readiness_probe: /
  replicas: 1

resources:
  ports: 8080
  cpus: 2+

run: python3 -m http.server 8080
```

Key rules:

- The replica must start an HTTP process in `run` that listens on `0.0.0.0` or an equivalent all-interface bind address.
- `resources.ports` exposes the port on each replica VM or pod.
- `service.readiness_probe` defines the path used to decide when a replica can receive traffic.
- Fixed replica count can use `service.replicas`; autoscaling uses `service.replica_policy` instead.
- If several replica ports are exposed, set `service.ports` to the single port that the load balancer should route to.

## Service Fields

Common `service:` fields:

```yaml
service:
  readiness_probe:
    path: /health
    initial_delay_seconds: 120
    timeout_seconds: 15
    endpoint_probe_interval_seconds: 10
    consecutive_failure_threshold_timeout: 300
    headers:
      Authorization: Bearer $AUTH_TOKEN
  ports: 8080
  replicas: 2
  load_balancing_policy: least_load
```

Supported readiness forms:

- String shorthand: `readiness_probe: /health`.
- Object form: `path`, `initial_delay_seconds`, `timeout_seconds`, `endpoint_probe_interval_seconds`, `consecutive_failure_threshold_timeout`, optional JSON/object `post_data`, and string-valued `headers`.
- The path must start with `/`. Use longer initial delay for model downloads, container pulls, CUDA kernel compilation, or first load of large weights.

Supported replica policies:

```yaml
service:
  readiness_probe: /health
  replica_policy:
    min_replicas: 1
    max_replicas: 4
    target_qps_per_replica: 2
    upscale_delay_seconds: 300
    downscale_delay_seconds: 1200
```

Policy notes:

- `max_replicas` must be at least `min_replicas`.
- `target_qps_per_replica` is required when `min_replicas` and `max_replicas` differ for normal services.
- `min_replicas: 0` enables scale-to-zero behavior; first traffic triggers scale-up and may incur cold-start latency.
- `target_qps_per_replica` may be a number or an accelerator-keyed map when using `instance_aware_least_load`.
- Spot fallback belongs in `replica_policy` with `dynamic_ondemand_fallback`, `base_ondemand_fallback_replicas`, or `spot_placer`, and replica resources should use `use_spot: true`.

Load balancing policies include:

- `least_load`: default policy; routes to the ready replica with the least in-flight load.
- `round_robin`: cycles through ready replicas.
- `instance_aware_least_load`: requires accelerator-keyed `target_qps_per_replica`, e.g. `A100:1: 4`, to normalize load by GPU type.

## CLI Lifecycle

Use explicit names for services you will operate repeatedly:

```bash
sky serve up --service-name my-service service.yaml
sky serve status my-service
sky serve status my-service -v
sky serve status --endpoint my-service
```

Update an existing service:

```bash
sky serve update my-service new-service.yaml --mode rolling
sky serve update my-service new-service.yaml --mode blue_green
```

Update mode choice:

- `rolling` is the default. New replicas come up while old replicas are terminated one at a time. Traffic may be mixed across old and new versions.
- `blue_green` waits for enough new replicas to be ready before switching traffic and terminating old replicas. Use it for model/API changes where mixed traffic is unacceptable.
- If only the service section changes and no file mounts are involved, SkyServe can reuse old replicas; run/setup/resource changes generally require new replicas.
- Rollback is another update: keep the last known-good YAML and run `sky serve update my-service previous.yaml --mode blue_green` or `--mode rolling` depending on traffic-switchover needs.

Log commands:

```bash
sky serve logs my-service 1 --tail 200 --no-follow
sky serve logs --controller my-service --tail 200 --no-follow
sky serve logs --load-balancer my-service --tail 200 --no-follow
sky serve logs my-service --sync-down
sky serve logs my-service 1 3 --controller --sync-down
```

Log selection:

- Replica logs show provisioning, setup, server startup, readiness failures, application exceptions, model download failures, and GPU/runtime errors.
- Controller logs show service registration, autoscaler decisions, replica manager behavior, controller boot problems, and max-services errors.
- Load balancer logs show request routing and downstream replica failures.
- Tailing allows exactly one target at a time; use `--sync-down` to collect multiple targets.

Teardown commands:

```bash
sky serve down my-service
sky serve down my-service --replica-id 2
sky serve down my-service --purge
sky serve down --all
```

Teardown cautions:

- `sky serve down` deletes service replicas and associated resources.
- Use `--replica-id` only for one named service.
- Use `--purge` for failed services or replicas only after considering possible leaked resources.
- Avoid `--all` unless the user explicitly wants every service removed.

## Python SDK Equivalents

SkyServe APIs return SkyPilot request IDs and generally require `sky.get()` or `sky.stream_and_get()` from the main SDK to wait for results.

```python
import sky
from sky import serve

service_task = sky.Task.from_yaml('service.yaml')
request_id = serve.up(service_task, service_name='my-service')
service_name, endpoint = sky.get(request_id)

status_request = serve.status('my-service')
records = sky.get(status_request)

update_task = sky.Task.from_yaml('new-service.yaml')
update_request = serve.update(
    update_task,
    service_name='my-service',
    mode=serve.UpdateMode.BLUE_GREEN,
)
sky.get(update_request)

serve.tail_logs('my-service', target='replica', replica_id=1, follow=False, tail=200)
sky.get(serve.down('my-service'))
```

SDK routing notes:

- Route API server login, request ID mechanics, remote server compatibility, and async SDK details to `../../sdk-api-server/SKILL.md`.
- Use CLI examples when the user asks for operational runbooks; use SDK examples when integrating service lifecycle into Python automation.

## vLLM Service Pattern

Use `/v1/models` as readiness for OpenAI-compatible vLLM. Ensure the process uses the same port declared in `resources.ports`.

```yaml
service:
  readiness_probe: /v1/models
  replicas: 2

secrets:
  HF_TOKEN: null

envs:
  MODEL_NAME: mistralai/Mixtral-8x7B-Instruct-v0.1

resources:
  ports: 8080
  accelerators: {L4:8, A10g:8, A100:4, A100-80GB:2}
  disk_size: 1024

setup: |
  conda activate vllm || (conda create -n vllm python=3.10 -y && conda activate vllm)
  pip install vllm

run: |
  conda activate vllm
  python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --tensor-parallel-size $SKYPILOT_NUM_GPUS_PER_NODE \
    --host 0.0.0.0 --port 8080
```

For authenticated vLLM endpoints, add readiness headers and pass the API key as a secret:

```yaml
service:
  readiness_probe:
    path: /v1/models
    headers:
      Authorization: Bearer $AUTH_TOKEN
  replicas: 1

secrets:
  HF_TOKEN: null
  AUTH_TOKEN: null
```

## SGLang Service Pattern

Use `/health` readiness and align `--port` with `resources.ports`.

```yaml
service:
  readiness_probe: /health
  replicas: 2

secrets:
  HF_TOKEN: null

envs:
  MODEL_NAME: meta-llama/Llama-2-7b-chat-hf

resources:
  ports: 8000
  accelerators: {L4:1, A10G:1, A100:1}

setup: |
  conda activate sglang || (conda create -n sglang python=3.10 -y && conda activate sglang)
  pip install "sglang[all]" transformers

run: |
  conda activate sglang
  python -m sglang.launch_server \
    --model-path $MODEL_NAME --host 0.0.0.0 --port 8000
```

## TGI Service Pattern

TGI usually exposes health on `/health` and listens internally on container port 80. Map host port to container port and expose the host port.

```yaml
envs:
  MODEL_ID: lmsys/vicuna-13b-v1.5

service:
  readiness_probe: /health
  replicas: 2

resources:
  ports: 8080
  accelerators: A100:1

run: |
  docker run --gpus all --shm-size 1g -p 8080:80 \
    -v ~/data:/data ghcr.io/huggingface/text-generation-inference \
    --model-id $MODEL_ID
```

## Rollout Plan For A vLLM Service

For a hard case such as creating a SkyServe vLLM service with readiness, ports, replicas, and rollback:

1. Pick a stable service name such as `mixtral-vllm`.
2. Write `service.readiness_probe: /v1/models`, `service.replicas: 2`, `resources.ports: 8080`, model envs, secrets for tokens, and `run` with `--host 0.0.0.0 --port 8080`.
3. Validate locally with `python scripts/validate_service_yaml.py service.yaml --summary`.
4. First deploy with `sky serve up --service-name mixtral-vllm service.yaml`.
5. Monitor with `watch -n10 sky serve status mixtral-vllm` and then `sky serve status --endpoint mixtral-vllm`.
6. For a model/server update, save the prior YAML, run `sky serve update mixtral-vllm new-service.yaml --mode blue_green`, and watch verbose status until the new version is ready.
7. Roll back by updating with the prior YAML; use `blue_green` for API/model compatibility breaks or `rolling` for minor service-section changes.
8. If startup stalls, inspect replica logs first, then controller logs, before changing readiness delays or resource requirements.

## Native Verification Candidates

Safe local checks for this sub-skill are parser/help oriented:

- `sky serve --help` and subcommand help are local and do not launch cloud resources.
- `python scripts/validate_service_yaml.py <yaml> --summary` is parser-only.
- Unit tests around service spec, service state, autoscaler, runner, and replica manager are useful evidence but may need the repository test environment.
- Real `sky serve up`, update, and serving smoke tests are cloud/GPU/Kubernetes-bound and should run only with explicit user authorization and suitable credentials.
