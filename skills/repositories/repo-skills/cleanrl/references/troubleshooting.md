# Cross-Cutting Troubleshooting

## Python or Package Version

Symptoms:
- Install resolver refuses CleanRL on Python 3.11+.
- CLI scripts fail before parsing arguments.

Likely causes and recovery:
- CleanRL metadata declares `>=3.8,<3.11`; use Python 3.10 for the most compatible setup.
- If working from a checkout, run an editable install in an isolated environment and verify with `python scripts/check_cleanrl_environment.py --check-help`.

## Torch or CUDA

Symptoms:
- `ImportError` from `torch` shared libraries.
- `torch.cuda.is_available()` is false even on a GPU host.
- Training starts on CPU despite `--cuda` defaulting true.

Recovery:
- Verify `import torch` before running CleanRL scripts.
- For smoke tests, use `--no-cuda` unless the user specifically needs GPU execution.
- Match CUDA wheels to the driver and hardware. Do not fix a CUDA issue by installing all optional CleanRL extras.

## Gym, Gymnasium, and NumPy

Symptoms:
- Gym emits a warning about being unmaintained or NumPy 2 support.
- Environment id works in Gymnasium but not Gym, or vice versa.

Recovery:
- Treat the warning as upstream context, not necessarily a failed import.
- Check the target script and docs page; CleanRL is mid-migration and scripts may use Gym or Gymnasium differently.
- If an environment id fails, confirm whether the selected script expects classic Gym ids, Gymnasium ids, Atari no-frameskip ids, EnvPool ids, DM Control ids, or PettingZoo ids.

## Optional Backends Missing

Symptoms:
- `ModuleNotFoundError` for `ale_py`, `envpool`, `jax`, `flax`, `mujoco`, `dm_control`, `procgen`, `pettingzoo`, `supersuit`, or `isaacgym`.

Recovery:
- Route to `sub-skills/training-scripts/references/troubleshooting.md` for workflow-specific extras.
- Install only the extra family needed by the selected script.
- Use help checks or AST inspection when backend imports block execution.

## W&B, Hugging Face, and Credentials

Symptoms:
- `--track` prompts for W&B login or fails with API errors.
- `--upload-model` or model-zoo operations fail with repository/token errors.
- User asks to print or reuse tokens.

Recovery:
- Use `sub-skills/experiment-operations/scripts/check_wandb_env.py` to report readiness without printing values.
- Keep W&B tracking (`--track`) separate from Hugging Face model sharing (`--upload-model`).
- Ask before running credential-backed network actions.

## Cloud, Docker, Slurm, and AWS

Symptoms:
- Terraform/AWS Batch commands need credentials or mutate infrastructure.
- Docker build/push is slow or requires registry access.
- Slurm command launches a long job.

Recovery:
- Route to `sub-skills/experiment-operations/SKILL.md`.
- Generate command previews and inspect resource settings before execution.
- Require explicit user approval for external-resource actions.

## Repository Maintenance

Symptoms:
- A small code change affects docs, tests, requirements, or benchmark results.
- Tyro help warnings appear after changing defaults.
- Optional backend tests fail in an environment without extras.

Recovery:
- Route to `sub-skills/repo-maintenance/SKILL.md`.
- Use `sub-skills/repo-maintenance/scripts/select_native_checks.py` to choose focused checks.
- For performance-impacting algorithm changes, smoke tests are not enough; plan RLOps benchmark/regression review.
