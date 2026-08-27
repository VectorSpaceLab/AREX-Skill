# Offline RL overview

AI-Optimizer's offline RL collection is a research-code suite built around d3rlpy-style training flows plus standalone scripts. Offline RL, also called batch RL, trains a policy from a fixed dataset of transitions instead of collecting fresh interaction during the offline phase. The main risk is distribution shift: the learned policy may choose actions that were rare or absent in the behavior dataset, causing overestimated values and unstable deployment.

## Taxonomy used by the collection

| Family | Meaning | Algorithms in scope | Typical task shape |
| --- | --- | --- | --- |
| IL | Imitation learning / behavior cloning baseline | BC-style APIs are present in the d3rlpy-derived package | Fit policy directly to dataset actions; useful baseline before value-based offline RL. |
| PC | Policy Constraint methods | BCQ, BEAR | Constrain learned actions near the behavior policy or dataset support. Use when out-of-distribution action avoidance is the main concern. |
| VR | Value-function Regularization methods | CQL, ISPI-style pessimistic value correction | Penalize optimistic Q-values or reweight actor updates. Use when conservative value estimation matters. |
| MB | Model-Based offline methods | MOPO, COMBO | Fit a learned dynamics model, then train policy with model rollouts and penalties/regularization. Heavy simulator and dynamics-model prerequisites apply. |
| U | Uncertainty-based methods | UWAC, REDQ-related uncertainty/ensemble variants | Use ensembles or uncertainty estimates to weight or regularize learning. |
| Off2On | Offline-to-online algorithms | AWAC, E2O, PEX | Start from offline data/checkpoints and continue with controlled online interaction. |

## Algorithm map

| Algorithm | Family | Dataset/env input style | Main notes |
| --- | --- | --- | --- |
| BCQ | PC | `--dataset` | Continuous-control BCQ using a VAE-like behavior model and perturbation model. d3rlpy class exposes `n_action_samples`, `action_flexibility`, and `lam`. |
| BEAR | PC | `--dataset` | MMD-based policy support constraint with VAE behavior model. Exposes MMD kernel/sigma, warmup, alpha threshold, action samples. |
| CQL | VR | `--dataset` | Conservative Q-learning with `conservative_weight`, `alpha_threshold`, and action sampling controls. |
| AWAC | Off2On | `--dataset` | Advantage weighted actor critic; offline training recipe uses larger batch size and `lam`. |
| REDQ | U / online ensemble | `--env` | The available script creates Gym envs and trains online with a replay buffer; do not treat it as a pure D4RL dataset script despite README-style examples elsewhere. |
| UWAC | U | `--dataset` in documented recipe | The algorithm class is present, but the documented train entry may be absent in some checkouts. Verify the target checkout contains a runnable UWAC trainer or adapt from the class API. |
| ISPI | VR / pessimistic actor update | `--env` | Standalone PyTorch/D4RL script using D4RL q-learning dataset conversion, optional normalization/reward transforms, and no explicit `--gpu` flag. |
| MOPO | MB | `--dataset` | Trains probabilistic ensemble dynamics first, then policy with model rollouts. Heavy D4RL/MuJoCo and long training prerequisites. |
| COMBO | MB | `--dataset`, plus `--n_critics` in the COMBO-specific entry | Similar dynamics pretraining, then conservative offline model-based policy optimization. The COMBO-specific recipe uses the COMBO entry, not the MOPO-style generic file. |
| E2O | Off2On | offline `--dataset`, online `--env` | Offline stage trains an ensemble CQL variant; online stage loads the offline params/model from expected d3rlpy log outputs. |
| PEX | Off2On | `--env_name`, `--log_dir` | Separate Policy Expansion implementation with offline IQL checkpoint and online modes `scratch`, `buffer`, `direct`, `pex`. |

## Choosing a workflow

1. If the task only needs a command recipe, use the bundled builders instead of hand-writing flags.
2. If the task uses D4RL names such as `hopper-medium-v2`, `halfcheetah-medium-expert-v2`, or AntMaze tasks, validate that the environment and dataset dependencies are available before any run.
3. If the task supplies custom arrays, validate the `.npz` with `validate_mdp_dataset_npz.py` and then follow the `MDPDataset` contract in `dataset-and-d3rlpy-api.md`.
4. If the task is offline-to-online, separate the offline checkpoint-producing stage from the online stage and record which checkpoint path the online stage consumes.
5. If the task asks for performance claims, benchmark reproduction, MuJoCo/D4RL download, or CUDA training, treat that as a heavyweight execution task requiring explicit budget and environment readiness.
