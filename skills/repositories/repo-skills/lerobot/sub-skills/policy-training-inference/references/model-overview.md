# Policy catalog and selection

This catalog is for LeRobot 0.6.2. Registration is evidence of a supported choice,
not proof that a particular checkpoint, tokenizer, GPU size, or environment is
available. The live registry can be inspected with the environment probe.

## Registered policy choices

The built-in `PreTrainedConfig` registry contains:

`act`, `diffusion`, `eo1`, `evo1`, `groot`, `molmoact2`, `fastwam`,
`gaussian_actor`, `lingbot_va`, `multi_task_dit`, `pi0`, `pi0_fast`, `pi05`,
`smolvla`, `tdmpc`, `vla_jepa`, `vqbet`, `wall_x`, and `xvla`.

`get_policy_class(name)` resolves the registered config module from
`configuration_*` to its sibling `modeling_*` module and then expects the
corresponding `<Name>Policy` class. This is lazy: a policy can appear in the
registry while class import still fails because its optional dependencies are
absent. Third-party policy plugins can register the same contract after plugin
discovery; never hard-code a plugin as built-in.

## Conditional extras

Use the smallest scoped install that matches the selected policy. In an existing
source checkout, the equivalent `uv sync --extra <extra>` is preferred; in an
installed package environment, use `uv pip install 'lerobot[<extra>]'` or the
project's package-manager equivalent.

| Policy family | Extra(s) evidenced by packaging | Main conditional dependencies |
|---|---|---|
| `act` | base; usually `training` for CLI training | core PyTorch/vision |
| `diffusion` | `diffusion` | `diffusers` |
| `pi0`, `pi0_fast`, `pi05` | `pi` | `transformers`, `scipy`; Pi0 Fast also loads tokenizer/processor assets |
| `smolvla` | `smolvla` | `transformers`, `num2words`, `accelerate` |
| `groot` | `groot` | `transformers`, `peft`, `diffusers`, dataset/video stack, `dm-tree`, `timm`, optional `decord` |
| `wall_x` | `wallx` | `transformers`, `peft`, `scipy`, `torchdiffeq`, `qwen-vl-utils` |
| `molmoact2` | `molmoact2` | `transformers`, `peft`, `scipy` |
| `multi_task_dit` | `multi_task_dit` | `transformers`, `diffusers` |
| `fastwam` | `fastwam` | `transformers`, `diffusers` |
| `lingbot_va` | `lingbot_va` | `transformers`, `diffusers`, `accelerate` |
| `vla_jepa` | `vla_jepa` | `transformers`, `diffusers`, `qwen-vl-utils` |
| `eo1` | `eo1` | `transformers`, `qwen-vl-utils` |
| `evo1` | `evo1` | `transformers` and the model's vision/runtime needs |
| `xvla` | `xvla` | `transformers` |
| `vqbet` | base; `training` for CLI | core; policy has an MPS incompatibility |
| `tdmpc` | base; `training` for CLI | core; simulator/RL integration is a separate route |
| `gaussian_actor` | base plus its RL workflow dependencies | core policy class; do not infer RL readiness from ordinary IL training |

`training` composes dataset, video, W&B, and accelerate dependencies. `evaluation`
adds the evaluation video dependency, but policy and simulated-environment extras
are still separate. `peft` composes `transformers` and `peft`; policy-specific
extras may already include those packages.

## Practical choice

- Start with `act` for a compact single-task imitation baseline and low-risk
  processor validation.
- Use `diffusion` when a diffusion action distribution is required and the
  `diffusers` extra is installed.
- Use `smolvla` for a smaller language-conditioned VLA; account for tokenizer
  assets and its image/text processor.
- Use `pi0`, `pi05`, or `pi0_fast` only after confirming checkpoint model IDs,
  tokenizer/action-tokenizer assets, `transformers`/`scipy`, and GPU memory.
- Treat `groot`, `wall_x`, `molmoact2`, `vla_jepa`, `eo1`, `evo1`, `xvla`,
  `fastwam`, and `lingbot_va` as specialist VLA/world/action-tokenization
  paths. Read the checkpoint's own config and processor files before changing
  defaults.
- `vqbet` cannot be constructed on MPS by the factory; use CPU or CUDA.
- `tdmpc` and `gaussian_actor` may be valid registered policy choices but their
  RL/environment workflow is outside this sub-skill's dataset/IL route.

## What not to infer

The source documents provide indicative memory snapshots, not guarantees.
Memory depends on batch size, optimizer state, image resolution, checkpoint,
AMP, gradient accumulation, and backend. A policy registry entry does not prove
that its pretrained weights are public, cached, compatible with the chosen
feature schema, or safe to execute on a robot.
