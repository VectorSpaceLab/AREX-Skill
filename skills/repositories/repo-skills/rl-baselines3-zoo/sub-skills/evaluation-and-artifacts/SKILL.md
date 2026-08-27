---
name: evaluation-and-artifacts
description: "Evaluate and inspect local RL Baselines3 Zoo model artifacts
  without rendering or live Hub side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation and Artifacts

Use this sub-skill when a future Researcher needs to load, evaluate, or inspect an existing RL Baselines3 Zoo model folder from an installed `rl_zoo3` package.

## Route here for

- Building no-render local evaluation commands with `python -m rl_zoo3.enjoy` or `rl_zoo3 enjoy`.
- Choosing the final model, `best_model.zip`, a specific `rl_model_<steps>_steps.zip`, or the latest checkpoint.
- Explaining `--exp-id` behavior, including `--exp-id 0` as “latest numeric run”.
- Inspecting saved artifacts such as `args.yml`, `config.yml`, `env_kwargs.yml`, reward logs, checkpoint files, and `vecnormalize.pkl`.
- Planning a local benchmark smoke command with `--test-mode --no-hub`.

## Route elsewhere

- To create or resume training artifacts, use the `training-cli` sub-skill.
- For live Hugging Face Hub download/upload, model cards, W&B, or video creation, use the `integrations-hub-tracking` sub-skill.
- For plotting or interpreting learning/evaluation curves, use the `plotting-benchmarking` sub-skill.

## Default operating stance

1. Prefer installed-package commands. Use `python -m rl_zoo3.enjoy` when the `rl_zoo3` console wrapper or optional plotting dependencies are questionable; otherwise `rl_zoo3 enjoy` is equivalent for the enjoy entry point.
2. Add `--no-render` for headless, CI, notebook server, or SSH sessions unless the user explicitly wants a live window.
3. Inspect the local artifact tree before assuming a model exists. The bundled inspector does not import `rl_zoo3`, does not load model weights, and performs no training.
4. Avoid relying on a local `rl-trained-agents` checkout or submodule. If a command would trigger Hub fallback, either route to the Hub integration sub-skill or add the local/offline guard described in the troubleshooting reference.

## Bundled references and helper

- Start with [evaluation workflows](references/evaluation-workflows.md) for command templates and selector semantics.
- Use [artifact layout](references/artifact-layout.md) before debugging missing files.
- Use [troubleshooting](references/troubleshooting.md) for common errors and fixes.
- Use `scripts/model_artifact_inspector.py --help` to inspect a model/log folder without loading weights.

## Minimal workflow

```bash
python scripts/model_artifact_inspector.py \
  --folder logs --algo ppo --env CartPole-v1 --exp-id 0

python -m rl_zoo3.enjoy \
  --algo ppo --env CartPole-v1 -f logs --exp-id 0 \
  --no-render -n 1000
```

If inspection reports a missing selected model, do not “fix” it by training here; hand off artifact creation to the `training-cli` sub-skill.
