---
name: cluster-ops
description: "Operate Ray clusters, jobs, dashboard access, runtime
  environments, state APIs, logs, and observability workflows safely from the
  Ray CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray Cluster Operations

Use this sub-skill when the task is about administering or inspecting Ray clusters and submitted Ray applications: `ray start`, `ray stop`, `ray status`, `ray job submit`, `ray job logs`, `ray job status`, `RAY_API_SERVER_ADDRESS`, dashboard forwarding, runtime environments, `ray list/get/summary/logs`, cluster YAML, VM/KubeRay connection concepts, or OOM debugging.

## Route First

- For Ray Core application code, task/actor APIs, `ray.init()`, object refs, scheduling options, or placement groups in Python, route to `../core-runtime/SKILL.md`.
- For Ray Serve deploy/run/status/config details, Serve application YAML, HTTP ingress, or `ray serve`, route to `../serve-deployments/SKILL.md`.
- For Ray Data, Train, Tune, or RLlib workload internals, route to the matching sibling sub-skill after using this sub-skill only for cluster/job visibility.
- For cloud account, Kubernetes credential, network policy, or VM provisioning, keep guidance high-level and ask the user for their platform-specific constraints before issuing mutating commands.

## Operating Rules

1. Prefer read-only inspection first: `ray --help`, `ray status --help`, `ray job --help`, `ray list --help`, `ray summary --help`, and this sub-skill's `scripts/ray_cli_doctor.py`.
2. Distinguish local bootstrap addresses from dashboard HTTP addresses. Jobs and State API commands usually need the dashboard/API server address such as `http://127.0.0.1:8265`; Ray Core drivers may use a Ray bootstrap address or Ray Client URI.
3. Treat `ray start`, `ray stop`, `ray up`, `ray down`, `ray exec`, `ray submit`, `ray attach`, `ray dashboard`, and `ray symmetric-run` as mutating or long-running unless the user explicitly authorizes them.
4. Use `ray summary` before broad `ray list` calls on busy clusters; state snapshots can be stale, partial, or truncated.
5. For jobs, capture the submission ID, dashboard address, runtime environment, working directory, and exact entrypoint before debugging status or logs.

## References

- `references/cli-reference.md` maps the Ray CLI, read-only versus mutating commands, state/log patterns, and dashboard/status workflows.
- `references/job-and-runtime-env.md` covers Jobs CLI/API use, `RAY_API_SERVER_ADDRESS`, `--working-dir`, runtime environment packaging, and remote/KubeRay dashboard access concepts.
- `references/troubleshooting.md` covers connection failures, missing extras, dashboard/state API issues, runtime-env upload/import failures, OOM/system exits, and unsafe command handling.
- `scripts/ray_cli_doctor.py` checks local Ray CLI availability and selected command help without starting, stopping, or connecting to a cluster.

## Quick Triage

```bash
python scripts/ray_cli_doctor.py
python scripts/ray_cli_doctor.py --command job
python scripts/ray_cli_doctor.py --command list
```

If a user asks you to run a mutating cluster command, first restate what it changes, confirm the target address or cluster config, and prefer a dry-run/help command when available.
