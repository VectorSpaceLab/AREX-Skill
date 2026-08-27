# SMP Prior Training

Use this reference for TinyMDM prior training, prior sampling, and test-time motion generation inside a MimicKit checkout.

The bundled wrapper is [`../scripts/train_smp_prior.py`](../scripts/train_smp_prior.py).
It resolves the checkout root, validates imports and config paths with `--dry-run-config`, and then delegates to the source TinyMDM trainer.

## What the prior workflow does

The source trainer builds a `MotionPriorData` dataset from:

- the prior env config
- the prior motion source (`motion_file`)
- the character asset named by the env config
- the discriminator observation history length (`num_disc_obs_steps`)
- the control frequency (`control_freq`)

`MotionPriorData` samples motion windows from `MotionLib`, computes discriminator observations with `compute_disc_obs`, and returns a flattened history tensor.
`TinyMDMModel` then infers `input_dim` from the observed space and derives `input_channel = input_dim / num_disc_obs_steps`.

### Model behavior to remember

- Scheduler: DDPM for training and default sampling, DDIM for the SDS reward path.
- EMA: enabled in the bundled configs, with `model_ema_decay`, `model_ema_steps`, and `model_ema_update_after`.
- Test mode: loads `model.pt`, uses EMA sampling when EMA exists, unnormalizes outputs, converts them back into `Motion` pickles, and writes sample plots.
- Loss path: `ESM_SDS_loss` denoises at the selected diffusion steps and measures epsilon error against the current noise.

## Bundled prior configs

| Config | Use | Motion source | Env source | Main notes |
| --- | --- | --- | --- | --- |
| `tools/diffusion_model/config/tinymdm_multi_clip.yaml` | Multi-clip prior for task policies | `data/datasets/dataset_humanoid_locomotion.yaml` | `data/envs/smp_location_humanoid_env.yaml` | `batch_size: 512`, `lr: 2e-4`, `num_iterations: 200000`, EMA enabled |
| `tools/diffusion_model/config/tinymdm_single_clip.yaml` | Single-clip prior for the spinkick setup | `data/motions/humanoid/humanoid_spinkick.pkl` | `data/envs/smp_humanoid_env.yaml` | `batch_size: 512`, `lr: 1e-4`, `num_iterations: 50000`, EMA enabled |

Both configs use:

- `model_name: tiny_mdm`
- `arch_name: DiT`
- `T: 50`
- `loss_type: l1`
- `estimate_mode: epsilon`
- `noise_schedule_mode: squaredcos_cap_v2`
- `num_layers: 2`
- `num_attention_heads: 4`
- `normalizer_std_clip: 0.2`
- `control_freq: 30`

## Config schema checklist

These fields must be present or intentionally overridden:

| Field | Meaning | Notes |
| --- | --- | --- |
| `env_config` | Prior env YAML | Must exist inside the MimicKit checkout |
| `motion_file` | Motion clip or dataset manifest | Can point to a `.pkl` motion file or a `data/datasets/*.yaml` manifest |
| `control_freq` | Prior control frequency | Must stay aligned with the engine/control frequency used by the policy env |
| `T` | Diffusion steps | Larger values cost more time |
| `loss_type` | Training loss | Bundled configs use `l1` |
| `estimate_mode` | Diffusion prediction target | Bundled configs use `epsilon` |
| `noise_schedule_mode` | Scheduler schedule | Bundled configs use `squaredcos_cap_v2` |
| `model_ema*` | EMA settings | Bundled configs keep EMA on |
| `batch_size` | Prior train batch size | Reduce first if memory is tight |
| `num_samples_stat` | Normalizer statistics sample count | Large values slow start-up |
| `output_iter` | Sample/checkpoint interval | Generates sample motions during training |
| `grad_clip_norm` | Gradient clipping | Bundled configs use `1.0` |

`MotionPriorData` supports character assets with `.xml`, `.urdf`, and `.usd` extensions.

## Supported workflow

### Dry run only

Validate imports and config paths without starting training or sampling:

```bash
python scripts/train_smp_prior.py \
  --repo-root <mimickit-checkout> \
  --mode train \
  --cfg_path tools/diffusion_model/config/tinymdm_multi_clip.yaml \
  --out_dir output/smp_prior \
  --device cuda \
  --dry-run-config
```

### Train a prior

```bash
python scripts/train_smp_prior.py \
  --repo-root <mimickit-checkout> \
  --mode train \
  --cfg_path <prior-config> \
  --out_dir <output-dir> \
  --device cuda
```

### Sample or test a prior

```bash
python scripts/train_smp_prior.py \
  --repo-root <mimickit-checkout> \
  --mode test \
  --cfg_path <prior-config> \
  --model_file <prior-checkpoint.pt> \
  --out_dir <output-dir> \
  --device cuda
```

## Outputs to expect

Training writes these files under `out_dir`:

- `env_config.yaml`
- `diffusion_config.yaml`
- `model.pt`
- `log.txt`
- `samples/motion_*.pkl`
- `samples/anim_*`

Test mode writes sampled motions and plots under `out_dir/samples/`.

## Validation checklist

Before asking for a real prior run, confirm:

- the checkout root is correct
- the config file exists
- the env config exists
- the motion source exists or is queued for download
- the chosen control frequency matches the policy-side engine plan
- the target machine has the required CUDA-torch runtime
- the simulator backend is available if you intend to launch downstream policy training after the prior is built

## Current checkout limits

This repository snapshot only verified:

- `python tools/diffusion_model/train_tinymdm.py --help`
- CUDA torch import and allocation
- source import/compile smoke
- tiny converter fixtures

Actual prior training was not run here because the downloaded motion/model assets are not present.
