---
name: cleanrl
description: "Use CleanRL's single-file reinforcement learning scripts,
  evaluation utilities, experiment operations, and repository maintenance
  workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CleanRL Repo Skill

Use this skill when the user asks about CleanRL, its single-file RL algorithms, training commands, model evaluation/sharing, experiment operations, or maintaining the CleanRL repository. CleanRL is intentionally script-oriented rather than a modular import library, so route tasks by workflow before recommending commands.

## Start Here

1. Read [references/install-and-extras.md](references/install-and-extras.md) before installing dependencies, choosing optional extras, or diagnosing import failures.
2. Run `python scripts/check_cleanrl_environment.py --check-help` in a prepared CleanRL checkout or installed package environment when you need a safe import/help diagnostic.
3. Check [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting Python, torch, Gym/Gymnasium, W&B, Hugging Face, AWS, and optional-backend failures.

## Route by Task

- **Training scripts**: use [`sub-skills/training-scripts/SKILL.md`](sub-skills/training-scripts/SKILL.md) to choose a CleanRL algorithm script, inspect tyro/argparse flags, build tiny smoke commands, or adapt single-file training runs.
- **Evaluation and sharing**: use [`sub-skills/evaluation-and-sharing/SKILL.md`](sub-skills/evaluation-and-sharing/SKILL.md) to inspect saved `runs/` artifacts, choose evaluation helpers, reason about model-zoo repositories, or guard Hugging Face upload/download actions.
- **Experiment operations**: use [`sub-skills/experiment-operations/SKILL.md`](sub-skills/experiment-operations/SKILL.md) for benchmark command matrices, W&B tracking, Optuna tuning, resume/reproduce utilities, plotting, Docker, Slurm, Terraform, and AWS Batch planning.
- **Repo maintenance**: use [`sub-skills/repo-maintenance/SKILL.md`](sub-skills/repo-maintenance/SKILL.md) when editing CleanRL code, docs, tests, package metadata, contribution workflows, or RLOps regression plans.

## CleanRL Operating Model

- CleanRL's public value is readable, duplicated, single-file algorithm implementations. Do not refactor user tasks into hidden shared abstractions unless the user is deliberately changing repository design.
- Most training entrypoints live under `cleanrl/` and are run as scripts, not imported as a stable library API.
- Common script flags include `--env-id`, `--total-timesteps`, `--seed`, `--cuda/--no-cuda`, `--track`, `--capture-video`, `--save-model`, and `--upload-model`, but inspect the target script before assuming every flag exists.
- Optional backends are workflow-specific: Atari, EnvPool, Procgen, MuJoCo, DM Control, PettingZoo, JAX, Optuna, cloud/AWS, docs, and memory-gym require separate extras or setup.
- Treat W&B tracking, Hugging Face upload/download, Docker build/push, Terraform, AWS Batch, Slurm submission, and long benchmark/training runs as side-effectful operations that need explicit user approval.

## Minimal Checks

```bash
python - <<'PY'
import importlib.metadata as metadata
print(metadata.version('cleanrl'))
import cleanrl_utils
print('cleanrl_utils import ok')
PY
python scripts/check_cleanrl_environment.py --check-help
```

If a check fails, avoid broad dependency installation first. Read [references/install-and-extras.md](references/install-and-extras.md), then install only the extra required by the selected workflow.

## Integrated Workflows

- For “train then upload/evaluate,” start in `training-scripts` to select and run with `--save-model`; then use `evaluation-and-sharing` to validate artifacts and handle Hugging Face steps.
- For “benchmark a changed algorithm,” start in `repo-maintenance` to classify the code change and tests; then use `experiment-operations` to generate dry-run command matrices or RLOps plans.
- For “cloud training failed,” use `experiment-operations` for credentials/resources and `training-scripts` for algorithm flags or backend extras.
- For “new CLI flag,” use `repo-maintenance` for docs/tests and `training-scripts` for script flag semantics and tiny smoke commands.

## Guardrails

- Do not tell future agents to read or run original CleanRL docs, examples, tests, or benchmark scripts as runtime dependencies. This skill bundles distilled references and safe helper scripts.
- Do not expose tokens, local environment paths, machine-specific install prefixes, or private setup details in user-facing answers.
- Do not run native tests, cloud jobs, W&B jobs, Hugging Face network actions, or long training by default; use the sub-skill safety rules and ask for approval when necessary.
