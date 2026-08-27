# Cross-Cutting Troubleshooting

## When To Read

Read this when SkyPilot cannot be imported, the `sky` CLI is missing, the API server is disconnected, a command requires credentials, output parsing is confusing, optional dependencies are missing, or the task spans multiple sub-skills.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sky: command not found` | SkyPilot is not installed in the active environment or the environment's `bin` directory is not on `PATH`. | Install SkyPilot with only needed extras, then run `python scripts/check_skypilot_env.py --check-cli`. |
| `ModuleNotFoundError: No module named 'sky'` | The Python interpreter used by the agent is not the interpreter where SkyPilot is installed. | Run `python -m pip show skypilot`; if missing, install the package in the interpreter being used. |
| Optional provider import errors | The base package is installed but the relevant cloud extra is missing. | Install the narrow extra needed for the user's target provider, such as `skypilot[aws]`, `skypilot[gcp]`, `skypilot[azure]`, or `skypilot[kubernetes]`. Avoid broad extras unless the user needs them. |
| YAML validators cannot import SkyPilot | The bundled skill helper is being run outside a SkyPilot environment. | Install SkyPilot first or run the helper with a Python interpreter that has SkyPilot installed. |

## API Server Connectivity

| Symptom | Meaning | Next step |
| --- | --- | --- |
| `sky api info` reports a server version and status | A SkyPilot API server is connected. | Continue with the user's task. |
| `No SkyPilot API server is connected` | No local or remote server is active for this client. | Ask whether to start one locally with `sky api start` or connect to an existing endpoint with `sky api login -e <url>`. |
| Remote endpoint unreachable or auth expired | Network, endpoint, or token issue. | Ask for the intended endpoint and run `sky api login --relogin -e <url>` if the user confirms. |
| New client / old server mismatch | API version compatibility issue. | Read `sub-skills/sdk-api-server/references/troubleshooting.md`; use the remote version, compatibility decorators, or upgrade/downgrade plan. |

## Credentials And Resources

- Use `sky check -o json` to inspect enabled/disabled clouds only when the user intends to launch or query provider resources.
- Do not ask the user to paste credentials into prompts. Point them to provider-native credential setup and rerun `sky check`.
- Resource unavailability is different from credential failure: capacity/quota failures usually happen after credentials are accepted; authentication failures happen during provider checks or provisioning setup.
- Let SkyPilot optimize cloud, region, and instance type by default. Pin `infra`, region, zone, Kubernetes context, Slurm partition, or instance type only when the user explicitly asks or the workload requires it.

## YAML, CLI, Jobs, And Serving Routing

- For parser or schema failures, use `sub-skills/task-yaml/scripts/validate_task_or_service_yaml.py` and then read `sub-skills/task-yaml/references/troubleshooting.md`.
- For interactive cluster lifecycle, logs, queues, workdir sync, or cleanup issues, read `sub-skills/cluster-operations/references/troubleshooting.md`.
- For managed job preemption, controller logs, job IDs, pools, or job groups, read `sub-skills/managed-jobs/references/troubleshooting.md`.
- For SkyServe readiness, wrong ports, replica states, updates, or service logs, read `sub-skills/serving/references/troubleshooting.md`.
- For cloud/Kubernetes/Slurm/SSH/storage/volume/provider failures, read `sub-skills/infrastructure-storage/references/troubleshooting.md`.

## Output And Automation

- Prefer `-o json` when available: `sky status -o json`, `sky queue -o json`, `sky jobs queue -o json`, `sky check -o json`, and `sky gpus list -o json` are easier to parse than tables.
- Use bounded log commands for automation: `--tail 200 --no-follow` when supported.
- Avoid scraping human-readable progress output for assertions; use status codes, JSON output, or SDK return values.

## Safe Native Verification

- Safe local checks: import SkyPilot, inspect SDK signatures, run `sky --help`, run bundled helper `--help`, and parser-only validation on tiny YAML fixtures.
- Conditional checks: focused unit tests can be safe when development dependencies are installed; choose the narrowest relevant test target.
- Unsafe by default: live `sky launch`, `sky jobs launch`, `sky serve up`, provider-specific `sky check` mutations, Kubernetes/Slurm/SSH operations, smoke tests, benchmarks, and LLM examples. Run only after explicit user approval and clear cost/resource expectations.

## Source Checkout Dependency Avoidance

This generated skill is self-contained for runtime guidance. If a future agent needs a reusable helper, use the bundled scripts under this skill tree. The source repository's docs, examples, tests, and scripts were used as evidence, but normal use of this skill should not depend on reopening or executing original source files.
