---
name: evaluation-and-sharing
description: "Evaluate CleanRL saved models, inspect local artifacts, and safely
  reason about Hugging Face sharing without network or credential side effects
  by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation And Sharing

Use this sub-skill when a task is about evaluating a trained CleanRL model, finding the right evaluation entry point, inspecting a saved run artifact, or explaining how CleanRL's Hugging Face model zoo upload/download path works.

## Route Here For

- Local artifact checks for `runs/<run_name>/<exp_name>.cleanrl_model`, TensorBoard event hints, and related `videos/<run_name>` or `videos/<run_name>-eval` folders.
- CleanRL model-zoo loading through `cleanrl_utils.enjoy` and its `--exp-name`, `--env-id`, `--seed`, `--hf-entity`, `--hf-repository`, and `--eval-episodes` arguments.
- Mapping an experiment name to the correct `cleanrl_utils.evals` function, model class tuple, serialization format, and optional dependencies.
- Explaining `--save-model`, `--upload-model`, `--hf-entity`, `push_to_hub`, and model card/upload behavior without performing network or credential actions by default.
- Diagnosing missing models, wrong Hugging Face repository names, env/script/eval mismatches, video capture failures, and optional Atari/JAX/MuJoCo/EnvPool dependency gaps.

## Do Not Use For

- Choosing or configuring training algorithms; route to `training-scripts`.
- W&B benchmark reproduction, sweeps, or experiment orchestration; route to `experiment-operations`.
- Pull requests, documentation contribution, or repository maintenance work; route to `repo-maintenance`.

## Safe Default Workflow

1. Read `references/model-zoo-and-artifacts.md` for artifact layout, save/upload flags, and network side effects.
2. Read `references/evaluation-api.md` to choose `cleanrl_utils.enjoy` versus a local `cleanrl_utils.evals` function.
3. Run `python sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py --run-dir <run-dir> --exp-name <exp-name>` or `python sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py --runs-dir runs --exp-name <exp-name> --env-id <env-id> --seed <seed>` before attempting evaluation.
4. Keep all Hugging Face downloads, uploads, repository creation, logins, and token use behind explicit user approval.
5. Use `references/troubleshooting.md` when an artifact, repository name, optional dependency, video backend, or eval function does not match the model.

## Guardrails

- Do not run `cleanrl_utils.enjoy` unless the user accepts Hugging Face network download behavior.
- Do not run `--upload-model`, `push_to_hub`, or `huggingface-cli login` unless the user explicitly requests credential-backed sharing.
- Prefer local inspection and direct eval-function calls for already downloaded or locally trained `.cleanrl_model` files.
- Treat `--track` as W&B tracking and `--upload-model` as Hugging Face sharing; they are separate network integrations.
