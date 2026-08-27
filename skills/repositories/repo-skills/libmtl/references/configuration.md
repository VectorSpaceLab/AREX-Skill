# Shared Configuration

This reference summarizes the shared `LibMTL_args` parser and the extra
arguments that the example scripts pass through `prepare_args`.

## Common flags

These flags appear across the benchmark scripts:

- `--mode {train,test}`
- `--seed`
- `--gpu_id`
- `--weighting`
- `--arch`
- `--rep_grad`
- `--multi_input`
- `--save_path`
- `--load_path`
- `--optim`
- `--lr`
- `--momentum`
- `--weight_decay`
- `--scheduler`
- `--step_size`
- `--gamma`

## Architecture-specific flags

The following flags are only meaningful for some architectures:

- `--img_size` and `--num_experts` are used by `CGC`, `PLE`, `MMoE`, and
  `DSelect_k`.
- `--num_nonzeros` and `--kgamma` are used by `DSelect_k`.

Architecture constraints verified from source:

- `PLE` rejects `multi_input=True`.
- `MTAN` expects a ResNet-based encoder.
- `CGC`, `PLE`, `MMoE`, and `DSelect_k` need an `img_size` tuple/list that
  matches the actual tensor shape they will flatten or gate over.

## Weighting-specific flags

The parser exposes a large family of weighting knobs. The most relevant ones
are:

- `--T` for `DWA`
- `--alpha` for `GradNorm`
- `--mgda_gn` for `MGDA`
- `--GradVac_beta` and `--GradVac_group_type` for `GradVac`
- `--leak` for `GradDrop`
- `--calpha` and `--rescale` for `CAGrad`
- `--update_weights_every`, `--optim_niter`, and `--max_norm` for
  `Nash_MTL`
- `--MoCo_beta`, `--MoCo_beta_sigma`, `--MoCo_gamma`, `--MoCo_gamma_sigma`,
  `--MoCo_rho` for `MoCo`
- `--DB_beta`, `--DB_beta_sigma` for `DB_MTL`
- `--STCH_mu`, `--STCH_warmup_epoch` for `STCH`
- `--robust_step_size` for `ExcessMTL`
- `--FairGrad_alpha` for `FairGrad`
- `--FAMO_w_lr`, `--FAMO_w_gamma` for `FAMO`
- `--MoDo_gamma`, `--MoDo_rho` for `MoDo`
- `--SDMGrad_lamda`, `--SDMGrad_niter` for `SDMGrad`
- `--UPGrad_norm_eps`, `--UPGrad_reg_eps` for `UPGrad`
- `--outer_lr`, `--inner_lr`, `--inner_step`, and `--FORUM_phi` for the
  bilevel family (`MOML`, `FORUM`, `AutoLambda`)

## Verified configuration caveats

These are useful to remember when writing skill guidance:

- `prepare_args` currently wires `optim=adam|sgd` only. `adagrad` and
  `rmsprop` are accepted by the parser help but are not fully handled.
- `prepare_args` currently wires `scheduler=step` only. `cos` and `exp` are
  advertised but not fully handled.
- If you build `Trainer` manually and do not call `prepare_args`, pass
  `weight_args={}` and `arch_args={}` even for simple HPS/EW runs.

## Example command pattern

```bash
python main.py --weighting EW --arch HPS --gpu_id 0 --scheduler step --mode train --save_path PATH
```

Use the benchmark sub-skills for dataset-specific defaults such as
`--dataset_path`, `--train_bs`, `--test_bs`, `--bs`, or `--target`.
