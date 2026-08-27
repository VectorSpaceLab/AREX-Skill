---
name: serving
description: "Configure and operate SkyPilot SkyServe services, replicas,
  readiness probes, updates, logs, and LLM serving recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SkyServe Serving

Use this sub-skill when the user wants to deploy, update, inspect, debug, or tear down a SkyPilot SkyServe service. It owns service YAML structure, readiness probes, exposed service ports, replica and autoscaling policy, load balancing policy, rolling and blue-green updates, service status/log/down commands, and LLM-serving adaptations for vLLM, SGLang, TGI, FastChat, Ray Serve, or generic HTTP servers.

Do not use this sub-skill for generic task YAML details, cloud credentials, Kubernetes/Slurm/SSH setup, storage/file-mount troubleshooting, interactive cluster operations, managed jobs, or API server mechanics. Route those to sibling sub-skills.

## Read First

- For SkyServe service YAML patterns, CLI workflows, SDK equivalents, rollout plans, and LLM recipes, read [references/serve-workflows.md](references/serve-workflows.md).
- For readiness failures, wrong ports, stuck replicas, autoscaler behavior, update issues, log selection, cleanup, beta caveats, and LLM startup failures, read [references/troubleshooting.md](references/troubleshooting.md).
- For parser-only YAML checks, run [scripts/validate_service_yaml.py](scripts/validate_service_yaml.py); it does not launch services, start controllers, contact clouds, or open network sockets.
- For task fields such as `resources`, `setup`, `run`, `envs`, `secrets`, `workdir`, `file_mounts`, and `volumes`, use [../task-yaml/SKILL.md](../task-yaml/SKILL.md).
- For provider credentials, GPU availability, Kubernetes, Slurm, SSH, object storage, and volume failures, use [../infrastructure-storage/SKILL.md](../infrastructure-storage/SKILL.md).
- For Python SDK request handling, remote API server login, and API server lifecycle, use [../sdk-api-server/SKILL.md](../sdk-api-server/SKILL.md).

## Operating Principles

- Treat a SkyServe YAML as a normal SkyPilot task plus a top-level `service:` section; first ensure the replica process starts an HTTP endpoint on `0.0.0.0` and that the declared `resources.ports` exposes the same ingress port.
- Prefer `sky serve up --service-name <name> service.yaml` for first deployment, `sky serve update <name> service.yaml --mode rolling` for compatible changes, and `--mode blue_green` when traffic should switch only after enough new replicas become ready.
- Use `sky serve status <name> -v` and `sky serve logs` before changing YAML when replicas are stuck; status states distinguish controller initialization, provisioning, startup, readiness, preemption, cleanup, and no-replica autoscale-to-zero states.
- Keep service names explicit for repeatable operations, especially update/down/log commands; generated names are convenient for demos but poor for automation.
- Add an explicit cleanup command in every plan: `sky serve down <name>` for one service, `sky serve down <name> --replica-id <id>` for a single bad replica, or `sky serve down <name> --purge` only for failed services where resource leaks have been considered.
- Remember SkyServe is beta; it is useful for internal serving, R&D, batch inference, and scarce-GPU availability experiments, but do not present it as a mature external production serving layer without caveats.

## Fast Router

- New HTTP service YAML: validate with `python scripts/validate_service_yaml.py service.yaml --summary`, then plan `sky serve up --service-name <name> service.yaml`.
- vLLM/SGLang/TGI service: choose the framework readiness endpoint (`/v1/models` for OpenAI-compatible vLLM, `/health` for SGLang/TGI), align `resources.ports` with the server `--port`, add model download/GPU notes, and pass tokens through `secrets` or CLI `--secret` rather than inline plaintext.
- Multiple replica or autoscaling request: use `service.replicas` for fixed count, or `service.replica_policy` with `min_replicas`, `max_replicas`, and `target_qps_per_replica` for autoscaling.
- Multiple exposed replica ports: set `resources.ports` to the list and set `service.ports` to the single ingress port for the load balancer.
- Update/rollback request: preserve the last known-good YAML, use `sky serve update <name> <new.yaml> --mode rolling` or `--mode blue_green`, and roll back by updating the service with the previous YAML.
- Stuck service or failed request: inspect `sky serve status <name> -v`, `sky serve logs <name> <replica-id> --tail 200 --no-follow`, `sky serve logs --controller <name> --tail 200 --no-follow`, and `sky serve logs --load-balancer <name> --tail 200 --no-follow`.

## Safety Checklist

Before suggesting a command that mutates cloud resources, confirm:

- The user has accepted that `sky serve up`, `update`, and `down` can create, replace, or delete cloud/Kubernetes resources.
- The service YAML includes a `service:` section and a replica HTTP endpoint reachable on the exposed port.
- The readiness probe path starts with `/`, uses the correct HTTP method expectation, and allows enough `initial_delay_seconds` for model download and warmup.
- `service.ports` is set when multiple `resources.ports` are exposed, and it matches the application ingress port.
- Secrets such as Hugging Face tokens, API keys, and auth tokens are provided through `secrets`/`--secret`, not hard-coded into shared YAML.
- GPU and model choices are realistic for the requested framework, model size, tensor parallelism, disk size, and download time.

## Safe Validation

From this sub-skill directory, run:

```bash
python scripts/validate_service_yaml.py path/to/service.yaml --summary
```

The helper loads the YAML, validates the top-level `service:` block with SkyServe's parser, validates the surrounding `Task` when possible, checks common service/replica port pitfalls, and prints a concise summary. It is not a launch dry run and does not require cloud credentials.
