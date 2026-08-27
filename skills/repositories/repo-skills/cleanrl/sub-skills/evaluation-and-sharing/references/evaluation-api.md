# Evaluation API

This reference helps agents choose between `cleanrl_utils.enjoy` and direct `cleanrl_utils.evals` calls, then match the model artifact to the correct environment, model class, serialization format, and optional dependencies.

## Choosing An Entry Point

| Scenario | Recommended path | Network behavior |
| --- | --- | --- |
| User wants to load from CleanRL's Hugging Face model zoo. | `python -m cleanrl_utils.enjoy ...` after approval. | Downloads from Hugging Face. |
| User already has a local `.cleanrl_model`. | Import the matching `cleanrl_utils.evals.<name>_eval.evaluate` function and pass `model_path`. | Local-only if env creation is local. |
| User only wants to inspect a run folder. | Use `sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py`. | Local-only. |
| User wants to share a model. | Explain `--save-model --upload-model --hf-entity`, then ask before upload/auth. | Writes to Hugging Face. |

## `cleanrl_utils.enjoy` CLI

`cleanrl_utils.enjoy` accepts:

| Argument | Purpose |
| --- | --- |
| `--exp-name` | Key used to select `cleanrl_utils.evals.MODELS[exp_name]`; default `dqn_atari`. |
| `--seed` | Seed embedded in the derived repository name; default `1`. |
| `--hf-entity` | Owner/org used when deriving the repository; default `cleanrl`. |
| `--hf-repository` | Full repository override such as `<owner>/<repo>`. |
| `--env-id` | Environment id passed into the evaluation function. |
| `--eval-episodes` | Number of evaluation episodes. |

If `--hf-repository` is omitted, `enjoy` derives:

```text
<hf_entity>/<env_id>-<exp_name>-seed<seed>
```

It then downloads:

```text
<exp_name>.cleanrl_model
```

The installed help check for `python -m cleanrl_utils.enjoy --help` passes. The observed parser does not define a `--capture-video` argument but passes `args.capture_video` into `evaluate`; if execution reaches that path and fails with an attribute error, use a direct eval-function call with `capture_video=False` or verify whether the current CleanRL version has patched the parser.

## `cleanrl_utils.evals.MODELS` Router

These `exp_name` values are routed by `cleanrl_utils.evals.MODELS` for `enjoy`:

| `exp_name` | Training module | Eval module | `Model` passed to eval | Artifact format |
| --- | --- | --- | --- | --- |
| `dqn` | `cleanrl.dqn` | `dqn_eval` | `QNetwork` | PyTorch state dict. |
| `dqn_atari` | `cleanrl.dqn_atari` | `dqn_eval` | `QNetwork` | PyTorch state dict. |
| `dqn_jax` | `cleanrl.dqn_jax` | `dqn_jax_eval` | `QNetwork` | Flax serialized params bytes. |
| `dqn_atari_jax` | `cleanrl.dqn_atari_jax` | `dqn_jax_eval` | `QNetwork` | Flax serialized params bytes. |
| `c51` | `cleanrl.c51` | `c51_eval` | `QNetwork` | PyTorch dict with `args` and `model_weights`. |
| `c51_atari` | `cleanrl.c51_atari` | `c51_eval` | `QNetwork` | PyTorch dict with `args` and `model_weights`. |
| `c51_jax` | `cleanrl.c51_jax` | `c51_jax_eval` | `QNetwork` | Flax serialized dict with `args` and `model_weights`. |
| `c51_atari_jax` | `cleanrl.c51_atari_jax` | `c51_jax_eval` | `QNetwork` | Flax serialized dict with `args` and `model_weights`. |
| `ppo_atari_envpool_xla_jax_scan` | `cleanrl.ppo_atari_envpool_xla_jax_scan` | `ppo_envpool_jax_eval` | `(Network, Actor, Critic)` | Flax serialized `(args, params)` tuple. |

If `exp_name` is not in this table, `enjoy` will not route it. Use the standalone eval modules below when they fit the algorithm and artifact format.

## Standalone Eval Modules

These modules expose `evaluate(...)` but are not all present in `MODELS`:

| Eval module | Typical model tuple | Notable dependencies and format |
| --- | --- | --- |
| `dqn_eval` | `QNetwork` | PyTorch discrete-action state dict. |
| `dqn_jax_eval` | `QNetwork` | JAX/Flax discrete-action params bytes. |
| `c51_eval` | `QNetwork` | PyTorch dict with C51 atom metadata. |
| `c51_jax_eval` | `QNetwork` | JAX/Flax dict with C51 atom metadata. |
| `ddpg_eval` | `(Actor, QNetwork)` | PyTorch continuous-control tuple `(actor, qf)`. |
| `ddpg_jax_eval` | `(Actor, QNetwork)` | JAX/Flax continuous-control tuple. |
| `td3_eval` | `(Actor, QNetwork)` | PyTorch continuous-control tuple `(actor, qf1, qf2)`. |
| `td3_jax_eval` | `(Actor, QNetwork)` | JAX/Flax continuous-control tuple. |
| `ppo_eval` | `Agent` | PyTorch actor-critic state dict. |
| `ppo_envpool_jax_eval` | `(Network, Actor, Critic)` | EnvPool/JAX/Flax plus video dependencies when capture is enabled. |

The common call shape is:

```python
evaluate(
    model_path,
    make_env,
    env_id,
    eval_episodes=10,
    run_name="eval",
    Model=Model,
    capture_video=False,
)
```

Torch eval modules often accept `device=torch.device("cpu")`. DQN/C51 evals accept `epsilon`; DDPG/TD3 evals accept `exploration_noise`; PPO evals may accept algorithm-specific settings such as `gamma`.

## Matching Rules

- Match `exp_name` to the training script that created the artifact; model filenames are expected to be `<exp_name>.cleanrl_model`.
- Match `env_id` to the trained environment; observation/action-space mismatches surface as shape errors when constructing or loading the model.
- Match serialization format: PyTorch `.pt`-style state dicts are not interchangeable with Flax serialized bytes.
- Match optional dependencies before evaluation: Atari environments need Atari dependencies/ROM handling, JAX variants need JAX/Flax, continuous-control MuJoCo environments need MuJoCo-compatible packages, and EnvPool variants need EnvPool plus video dependencies if capture is enabled.
- Prefer `capture_video=False` during debugging so video backends do not obscure model/env mismatch errors.
