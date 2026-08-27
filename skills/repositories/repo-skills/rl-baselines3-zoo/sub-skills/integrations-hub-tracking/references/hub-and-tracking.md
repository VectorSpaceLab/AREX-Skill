# Hub and tracking workflows

This reference covers RL Zoo's Hugging Face Hub helpers and Weights & Biases tracking flags. Commands shown here are installed-package commands. The Hub commands perform network operations if executed; use the bundled checker first when the task is planning, debugging, or CI-safe validation.

## Network and credential stance

- `python -m rl_zoo3.load_from_hub` downloads files from a Hugging Face Hub repository.
- `python -m rl_zoo3.push_to_hub` evaluates the selected local model, optionally records replay video, creates/updates a local staging repository, and uploads files to the Hub.
- `--track` in training initializes W&B and can send metrics, TensorBoard data, monitor videos, config, tags, and code metadata to W&B.
- The bundled `hub_model_layout_checker.py` never imports Hugging Face or W&B libraries, never reads tokens, never opens network connections, never loads model weights, and never trains.
- Do not put tokens in command lines, Markdown, shell history, or logs. Let the user's environment or service login provide credentials when live transfers are explicitly approved.

## Naming model files and repositories

RL Zoo uses the Hugging Face SB3 naming helpers internally:

| Concept | Default value | Where it appears |
| --- | --- | --- |
| `EnvironmentName` | User `--env`, such as `CartPole-v1` | Validates/normalizes the environment name for Hub helpers. |
| `ModelName(algo, env)` | `{algo}-{env}` | Default model name and default repo name. |
| model filename | `{algo}-{env}.zip` | File expected in a Hub repo and written during upload packaging. |
| `ModelRepoId(organization, repo_name)` | `{organization}/{repo_name}` | Final Hub repository id. |
| `--repo-name` / `-name` | omitted by default | Overrides the repo name only; the model filename still follows `{algo}-{env}.zip`. |

Examples:

```bash
# Default repository id sb3/ppo-CartPole-v1 and model filename ppo-CartPole-v1.zip
python -m rl_zoo3.load_from_hub --algo ppo --env CartPole-v1 -f logs -orga sb3

# Custom repository name under the same organization
python -m rl_zoo3.load_from_hub --algo ppo --env CartPole-v1 -f logs -orga my-org -name cartpole-demo
```

Supported algorithm aliases in this checkout are `a2c`, `ars`, `crossq`, `ddpg`, `dqn`, `ppo`, `ppo_lstm`, `qrdqn`, `sac`, `td3`, `tqc`, and `trpo`.

## Planning a safe download from Hub

Command shape:

```bash
python -m rl_zoo3.load_from_hub \
  --algo ppo --env CartPole-v1 \
  -f logs -orga sb3 \
  --exp-id 0
```

Important semantics:

- The command downloads the Hub model zip, `config.yml`, `args.yml`, `env_kwargs.yml`, `train_eval_metrics.zip`, and optionally `vec_normalize.pkl`.
- Downloaded files are converted into the RL Zoo local layout: `<folder>/<algo>/<env>_<id>/<env>.zip`, `<folder>/<algo>/<env>_<id>/<env>/config.yml`, `<folder>/<algo>/<env>_<id>/<env>/args.yml`, `<folder>/<algo>/<env>_<id>/<env>/env_kwargs.yml`, optional `<folder>/<algo>/<env>_<id>/<env>/vecnormalize.pkl`, and extracted metrics in the run folder.
- For `load_from_hub`, `--exp-id 0` means “create the next numeric run id” under `<folder>/<algo>/`, not “reuse latest”. If no numeric run exists, the target is usually `<folder>/<algo>/<env>_1/`.
- A positive `--exp-id` writes to that exact numbered run folder. `--exp-id -1` writes to `<folder>/<algo>/` without an environment-id run folder.
- If the destination folder already exists, the command fails unless `--force` is passed. `--force` deletes the destination before saving the downloaded files.
- Public repositories may download without a token. Private/gated repositories still require appropriate user credentials.

No-network target collision check:

```bash
python ../scripts/hub_model_layout_checker.py \
  --mode load-target --folder logs --algo ppo --env CartPole-v1 \
  --organization sb3 --exp-id 0
```

Use `--json` when another verification script needs machine-readable findings.

## Planning an upload to Hub

Command shape:

```bash
python -m rl_zoo3.push_to_hub \
  --algo ppo --env CartPole-v1 \
  -f logs --exp-id 0 \
  -orga my-org -name ppo-CartPole-v1 \
  -m "Initial commit" \
  --no-render
```

Important semantics:

- The command first resolves and loads a local model from the RL Zoo log layout. Use `--load-best`, `--load-checkpoint <steps>`, or `--load-last-checkpoint` to upload a non-default selector.
- It recreates an evaluation environment using saved hyperparameters/config and evaluates the model for the model card.
- Without `--no-render`, upload packaging also attempts replay video generation. Use `--no-render` for headless or display-constrained sessions.
- Upload packaging writes a Hub model file named `{algo}-{env}.zip`, saved `args.yml`, `config.yml`, generated `env_kwargs.yml`, optional `vec_normalize.pkl`, a zipped metrics bundle, and a generated `README.md` model card with metadata.
- `--organization` / `-orga` is required by the CLI; `--repo-name` / `-name` defaults to `{algo}-{env}`.
- There is no upload CLI `--force` flag. The packaging routine creates or reuses the remote repository and uploads the local staging folder. Confirm overwrite policy with the user before live upload.
- The upload CLI passes `token=None`; service credentials come from the user's Hugging Face configuration/environment, not from this skill.

Local upload preflight:

```bash
python ../scripts/hub_model_layout_checker.py \
  --mode push --folder logs --algo ppo --env CartPole-v1 --exp-id 0 \
  --organization my-org --repo-name ppo-CartPole-v1 --expect-vecnormalize auto
```

Selector examples:

```bash
# Check that best_model.zip exists before planning --load-best upload
python ../scripts/hub_model_layout_checker.py \
  --mode push --folder logs --algo ppo --env CartPole-v1 --exp-id 1 --load-best

# Check that a checkpoint exists before planning --load-checkpoint 10000 upload
python ../scripts/hub_model_layout_checker.py \
  --mode push --folder logs --algo ppo --env CartPole-v1 --exp-id 1 --load-checkpoint 10000
```

## Checking a staged/local Hub repository

If the user already has a local Hub repository clone or staging directory, validate its expected file set without network:

```bash
python ../scripts/hub_model_layout_checker.py \
  --mode staged-hub --folder logs --algo ppo --env CartPole-v1 \
  --staged-hub-dir hub/ppo-CartPole-v1
```

A Hub repository intended for `load_from_hub` should contain:

```text
{algo}-{env}.zip
config.yml
args.yml
env_kwargs.yml
train_eval_metrics.zip
vec_normalize.pkl      # optional unless the model was normalized
README.md              # model card, expected after upload packaging
```

The file name `vec_normalize.pkl` is used in the Hub repo. After download, RL Zoo saves it into the local run's environment subfolder as `vecnormalize.pkl`.

## Direct model-card/API planning

RL Zoo exposes model-card and package helpers for advanced integrations:

- `generate_model_card(algo_name, algo_class_name, organization, env_id, mean_reward, std_reward, hyperparams, env_kwargs)` returns model-card text plus metadata.
- `package_to_hub(...)` performs the complete evaluate, optional replay-video, model-card, local staging, and upload pipeline.

Use the CLI for normal tasks. Do not call `package_to_hub` from a bundled helper or automation unless the user explicitly approved live network upload, evaluation side effects, and credential use.

## W&B training tracking

W&B is controlled by training flags, not by a separate RL Zoo integration command:

```bash
python -m rl_zoo3.train \
  --algo ppo --env CartPole-v1 --n-timesteps 10000 \
  --log-folder logs --device cpu \
  --track --wandb-project-name sb3 \
  --wandb-entity my-team --wandb-group cartpole-smoke \
  --wandb-tags optimized pr-123
```

Behavior when `--track` is present:

- Training imports `wandb`; if it is not installed, startup fails with an import error.
- RL Zoo creates a run name shaped like `{env}__{algo}__{seed}__{timestamp}`.
- User-provided `--wandb-tags` are combined with an SB3 version tag.
- W&B is initialized with `sync_tensorboard=True`, `monitor_gym=True`, and `save_code=True`.
- RL Zoo sets `tensorboard_log` to `runs/<run-name>` for the tracked run.
- If the task must be offline/no-network, omit `--track` or use an explicitly approved W&B offline configuration supplied by the user.

For training duration, checkpointing, and the rest of the `train` command surface, route to `../../training-cli/SKILL.md`.
