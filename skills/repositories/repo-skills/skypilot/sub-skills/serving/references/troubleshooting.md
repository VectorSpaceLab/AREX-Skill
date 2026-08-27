# SkyServe Troubleshooting

Use this reference when a SkyServe YAML validates poorly, a service is stuck, requests fail, replicas restart, autoscaling surprises the user, or LLM serving takes too long to become ready.

## Triage Order

1. Check service and replica state:

   ```bash
   sky serve status <service-name> -v
   ```

2. Inspect the endpoint only after a service exists:

   ```bash
   sky serve status --endpoint <service-name>
   ```

3. Inspect logs by target:

   ```bash
   sky serve logs <service-name> <replica-id> --tail 200 --no-follow
   sky serve logs --controller <service-name> --tail 200 --no-follow
   sky serve logs --load-balancer <service-name> --tail 200 --no-follow
   ```

4. Validate YAML locally without launching:

   ```bash
   python scripts/validate_service_yaml.py service.yaml --summary
   ```

5. Route provider, credential, GPU, Kubernetes, Slurm, SSH, storage, and volume failures to `../../infrastructure-storage/SKILL.md`; route task syntax outside the `service:` section to `../../task-yaml/SKILL.md`.

## Status Interpretation

Service states:

- `CONTROLLER_INIT`: controller is still starting; wait briefly, then inspect controller logs if it stays here.
- `REPLICA_INIT`: controller is up but no ready replicas yet; inspect replica provisioning/startup logs.
- `READY`: at least one replica passed readiness and the endpoint should accept traffic.
- `NO_REPLICAS`: commonly from `min_replicas: 0`; traffic should trigger scale-up, but cold start is expected.
- `CONTROLLER_FAILED`: controller or load balancer did not start or died; inspect controller logs and API/server infrastructure.
- `FAILED`: no ready replica and at least one replica failed due to provisioning, readiness timeout, runtime code, or user setup/run errors.
- `FAILED_CLEANUP`: teardown failed and cloud resources may remain; verify in the cloud/provider UI or with provider-specific checks.
- `SHUTTING_DOWN`: teardown is in progress.

Replica states:

- `PENDING`: launch is queued due to concurrency limits.
- `PROVISIONING`: resources are being created; route resource capacity/credentials to infrastructure troubleshooting if it fails.
- `STARTING`: VM/pod exists and setup/run is executing; inspect replica logs for package install, model download, and server bind failures.
- `READY`: readiness probe passed.
- `NOT_READY`: readiness probe is currently failing but the replica has not exceeded failure thresholds.
- `FAILED_INITIAL_DELAY`: readiness did not pass before `initial_delay_seconds`; increase delay only after confirming the server is still legitimately starting.
- `FAILED_PROBING`: readiness repeatedly failed after startup; verify path, port, headers, and server health.
- `FAILED_PROVISION`: cloud/Kubernetes provisioning failed; route to infrastructure troubleshooting.
- `PREEMPTED`: spot replica was interrupted and SkyServe is recovering it.

## Readiness Probe Failures

Symptoms:

- `STARTING`, `NOT_READY`, `FAILED_INITIAL_DELAY`, or `FAILED_PROBING` replicas.
- Endpoint returns 502/503 or load balancer has no ready replica.
- Replica logs show server started, but readiness still fails.

Common fixes:

- Ensure `readiness_probe` starts with `/`, e.g. `/health` or `/v1/models`.
- Match readiness path to framework: vLLM OpenAI-compatible servers commonly use `/v1/models`; TGI and SGLang examples use `/health`; simple HTTP servers often use `/` or `/health`.
- If the readiness endpoint requires authentication, put `headers` under `service.readiness_probe` and provide tokens via `secrets` or CLI `--secret`.
- For large models, set `initial_delay_seconds` high enough for dependency installation, container pull, model download, tokenizer loading, CUDA initialization, and tensor-parallel warmup.
- Avoid generation-heavy readiness requests; use cheap health/model-list endpoints when available.
- If `post_data` is a string, it must be valid JSON.

## Wrong Ports

Symptoms:

- Replica logs show server listening on one port while YAML exposes another.
- `validate_service_yaml.py` reports missing or ambiguous service ingress port.
- Service passes provisioning but never becomes ready.

Fixes:

- Align the server command, `resources.ports`, and optional `service.ports`.
- Use `--host 0.0.0.0` for Python/FastAPI/vLLM/SGLang servers; binding only to `127.0.0.1` can make the service unreachable from the load balancer.
- If `resources.ports` is a list or range, set `service.ports` to the single ingress port.
- For TGI Docker, expose a host port and map it to container port 80, e.g. `-p 8080:80` plus `resources.ports: 8080`.
- If different resource alternatives declare different ports, normalize them or set a consistent `service.ports` present in every resource option.

## Replica Not Ready Or Restarting

Symptoms:

- Repeated transition between `STARTING`, `NOT_READY`, and failed states.
- Replica log shows process exits, OOM, CUDA errors, package failures, or missing model credentials.

Fixes:

- Inspect replica logs first: `sky serve logs <service> <replica-id> --tail 200 --no-follow`.
- Confirm model tokens are passed as secrets and not left as `null` at runtime.
- Increase `disk_size` for large models and Docker layers.
- Match accelerators to the model and serving framework; tensor parallel size should not exceed `$SKYPILOT_NUM_GPUS_PER_NODE`.
- Prefer a tested smaller model or CPU/lightweight HTTP service when debugging SkyServe mechanics.
- If the process starts multiple internal servers, make sure the final foreground process is the public API server and does not exit early.

## Autoscaling Surprises

Symptoms:

- More or fewer replicas than expected.
- `NO_REPLICAS` despite a valid service.
- Scale-up is slow after traffic starts.

Fixes:

- For fixed count, use `replicas: <n>` instead of `replica_policy`.
- For autoscaling, set `replica_policy.min_replicas`, `max_replicas`, and `target_qps_per_replica`.
- `min_replicas: 0` intentionally starts with no replicas; document cold-start latency.
- Use `upscale_delay_seconds` and `downscale_delay_seconds` to dampen scale decisions.
- For heterogeneous GPUs with `instance_aware_least_load`, use a dict-valued `target_qps_per_replica` and set `load_balancing_policy: instance_aware_least_load`.
- Spot/on-demand fallback requires spot resources; do not mix spot and on-demand resources directly unless using the SkyServe fallback policy fields.

## Update And Rollback Issues

Symptoms:

- Update keeps serving old behavior.
- Update terminates old replicas before the new ones are ready.
- Mixed model versions appear during rollout.

Fixes:

- Use `sky serve update <service> <yaml> --mode blue_green` when mixed traffic is unacceptable.
- Use `rolling` for lower-disruption incremental updates where old and new versions can both serve traffic safely.
- Preserve the previous known-good YAML before every update; rollback is `sky serve update <service> previous.yaml --mode blue_green` or `--mode rolling`.
- If only `service:` fields changed, SkyServe may reuse old replicas; if code, resources, workdir, file mounts, setup, or run changed, expect new replicas.
- Watch `sky serve status <service> -v` until active versions and ready replicas match the desired rollout state.

## Logs Command Pitfalls

Symptoms:

- CLI rejects a logs command.
- Logs are missing the target information.

Fixes:

- Tailing supports one target at a time: one replica ID, `--controller`, or `--load-balancer`.
- Use `--sync-down` to gather multiple targets or all logs.
- Use `--tail` with tailing/printing logs, not as a substitute for collecting all historical logs.
- Replica logs require a replica ID; get it from `sky serve status <service> -v`.

## Cleanup And Failed Teardown

Symptoms:

- `FAILED_CLEANUP` service or replica.
- Service down command fails or resources appear leaked.

Fixes:

- Retry a scoped teardown first: `sky serve down <service>`.
- For a failed replica, use `sky serve down <service> --replica-id <id> --purge` only after considering resource-leak risk.
- For a failed service, use `sky serve down <service> --purge` only when normal down cannot clean it.
- Avoid tearing down the SkyServe controller directly while services still exist; use service-level down commands first.
- If provider resources remain, route to `../../infrastructure-storage/SKILL.md` for the specific cloud/Kubernetes cleanup path.

## Controller And Max Services

Symptoms:

- Controller fails to register services.
- Error mentions max number of services reached.
- Controller logs fill disk or controller is under-resourced.

Fixes:

- Inspect controller logs: `sky serve logs --controller <service> --tail 200 --no-follow`.
- Controller resources are configured outside individual service YAML, in SkyPilot config under `serve.controller.resources`; existing controllers must be torn down before new controller settings take effect.
- On Kubernetes, high-availability controller mode may be relevant, but route Kubernetes setup and API server deployment details to infrastructure/API-server sub-skills.
- If many services run concurrently, increase controller memory and disk with a planned controller restart window.

## LLM Serving Failure Modes

Common vLLM issues:

- Readiness should usually be `/v1/models`.
- `--host 0.0.0.0` and the same `--port` as `resources.ports` are required.
- `--tensor-parallel-size` should match available GPUs; `$SKYPILOT_NUM_GPUS_PER_NODE` is useful.
- Hugging Face tokens should be secrets; missing tokens cause download/auth errors.
- Large models need enough disk and may need longer readiness initial delay.

Common SGLang issues:

- Readiness is often `/health`.
- Use the installed framework extras needed by the chosen model and backend.
- Verify model path, token, and port alignment.

Common TGI issues:

- Readiness is usually `/health`.
- Docker must expose the host port: `-p <host-port>:80`.
- GPU, shared memory, model cache, and disk requirements can dominate startup.

General LLM cautions:

- Do not promise quick startup for large models; model downloads and first load can take many minutes.
- For debug loops, use a tiny model or simple HTTP service before launching expensive GPUs.
- Avoid embedding API keys, HF tokens, or bearer tokens in YAML examples intended for shared contexts.

## Beta Caveat

SkyServe is documented as beta. It is well-suited for internal serving, R&D, batch inference, cost/capacity experiments, and multi-cloud scarce-GPU serving. For external production serving, explicitly call out rough edges, need for monitoring, rollout discipline, cleanup plans, auth/TLS design, and infrastructure validation.
