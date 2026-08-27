# Ray Cross-Cutting Troubleshooting

Use this reference before diving into a sub-skill when the failure might be caused by installation, optional extras, address selection, unsafe cluster commands, or workflow misrouting.

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ray'` | Ray is not installed in the active Python environment. | Install `ray` or switch to the environment where Ray is installed; rerun `python scripts/check_ray_environment.py --require core`. |
| `ImportError` mentions missing Data dependencies such as pandas or pyarrow | The base `ray` package is installed without Data extras. | Install `ray[data]` for generic Ray Data workflows. |
| Train or Tune import says to install `ray[train]` or `ray[tune]` | Narrow optional extras are missing. | Install the matching extra; add framework packages only for the selected trainer or search algorithm. |
| Serve import fails on web or gRPC dependencies | `ray[serve]` is missing. | Install `ray[serve]`; then use `sub-skills/serve-deployments/scripts/serve_config_lint.py` before deploying. |
| RLlib import fails on `gymnasium`, `torch`, or similar packages | `ray[rllib]` or RL backend packages are missing. | Install `ray[rllib]` and add `torch` or environment packages only when the workload needs them. |
| Dependency resolver conflicts after `ray[all]` | Too many unrelated optional dependencies were installed. | Prefer a fresh environment with the narrow workflow extra instead of broad `ray[all]`. |

## Pick The Right Address

Ray uses different address types for different surfaces:

- Python drivers and `ray.init(address=...)` use Ray bootstrap addresses, `auto`, or Ray Client-style addresses depending on the deployment.
- Jobs and State API commands usually use the dashboard/API HTTP address, commonly `http://127.0.0.1:8265`, via `RAY_API_SERVER_ADDRESS` or `--address`.
- Serve deploy/status/config commands target the Ray dashboard address for Serve’s submission client.
- Dashboard forwarding is a cluster access concern; use `sub-skills/cluster-ops/SKILL.md` before running forwarding commands.

When a command cannot connect, capture the exact command, the address value, whether a dashboard is running, and whether the user is local, VM, or Kubernetes-hosted.

## Avoid Unsafe Defaults

Do not silently run commands that start, stop, mutate, or submit work to a cluster:

- Ray lifecycle: `ray start`, `ray stop`, `ray up`, `ray down`, `ray exec`, `ray attach`, `ray submit`, `ray symmetric-run`.
- Jobs: `ray job submit`, `ray job stop`, `ray job delete`.
- Serve: `serve run`, `serve deploy`, `serve shutdown`, `serve start`.
- Debugging commands that interrupt or inspect live workers, such as stack dumps, should be confirmed on production clusters.

Prefer `--help`, bundled lint/check scripts, or read-only status/list commands first.

## Workflow Routing Failures

| User wording | Correct route |
| --- | --- |
| “Convert this function/class to run on Ray” | `sub-skills/core-runtime/SKILL.md` |
| “Why is `ray.get` hanging or memory exploding?” | `sub-skills/core-runtime/SKILL.md`, then cluster OOM notes if needed |
| “Submit this script to an existing Ray cluster” | `sub-skills/cluster-ops/SKILL.md` |
| “Use a runtime_env or working_dir for a job” | `sub-skills/cluster-ops/SKILL.md`; Serve-specific YAML goes to Serve |
| “Load/transform/write a dataset with Ray” | `sub-skills/data-pipelines/SKILL.md` |
| “Tune these hyperparameters” | `sub-skills/train-tune/SKILL.md` |
| “Use PPOConfig or custom Gymnasium envs” | `sub-skills/rllib-workloads/SKILL.md` |
| “Deploy this model as an HTTP service” | `sub-skills/serve-deployments/SKILL.md` |

## Version And Staleness Checks

- Read `references/repo-provenance.md` when comparing this skill to a checkout.
- If the checkout commit, Ray version, or selected evidence paths have drifted, refresh the skill before making precise API or CLI claims.
- If a live package version differs from the source baseline, prefer live inspection for signatures and use source/docs only for intent and broader workflow coverage.

## Hardware And Heavy Optional Workflows

GPU, Kubernetes, cloud, LLM, benchmark, release, C++ and Java workflows are not default coverage. Ask for platform constraints and use the closest sub-skill only for shared Ray concepts unless the user explicitly asks to extend the skill or run those workflows.
