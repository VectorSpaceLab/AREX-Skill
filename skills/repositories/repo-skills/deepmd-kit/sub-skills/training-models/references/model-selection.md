# Model Selection For DeePMD-kit Training

This reference helps choose a DeePMD-kit model family and backend before drafting `input.json` or a `dp train` command. It is intentionally distilled so the generated skill does not depend on source documentation being present.

## Selection Inputs

Collect only information that changes the decision:

| Input | Why it matters | Default when unknown |
| --- | --- | --- |
| Data format and labels | Determines whether energy/force/virial, tensor, DOS, property, spin, or Hessian losses are possible. | Route data uncertainty to `data-config`; do not invent labels. |
| Elements and `type_map` | Required by all models and critical for pretrained/fine-tune compatibility. | Ask for element order or derive from validated data. |
| System size and chemistry diversity | Controls descriptor complexity and whether large atomic models are worth the cost. | `se_e2_a` for a first baseline. |
| Target workflow | Baseline, production training, pretrained fine-tune, multi-task, long-range, spin, or property fitting lead to different schemas. | Baseline energy model unless user states otherwise. |
| Backend/deployment | Some models and deployment paths are backend-specific. | PyTorch for current large-model and multi-task workflows; TensorFlow for legacy compatibility. |
| Compute budget | DPA and distributed workflows are expensive; CPU runs should be bounded. | Draft commands and run only smoke steps if execution is requested. |

## Backend Matrix

| Backend flag | Good fit | Watch-outs |
| --- | --- | --- |
| `--tf` | Legacy TensorFlow training, many classical DeepPot-SE workflows, TensorFlow frozen `.pb` deployment. | Some newer models are PyTorch/JAX/Paddle focused; TensorFlow multi-task is deprecated. |
| `--pt` | DPA1/2/3/4 workflows, multi-task, pretrained fine-tuning, PyTorch deployment, current distributed DDP. | Requires PyTorch installation; checkpoints and frozen files use PyTorch conventions. |
| `--jax` | Supported descriptors where JAX is installed and desired for the workflow. | Not every model supports JAX; deployment/integration constraints may differ. |
| `--pd` | Paddle training and Paddle-specific deployment. | Confirm Paddle installation and use Paddle distributed launcher if needed. |
| `--pt-expt` / `pytorch-exportable` | Exportable PyTorch path when explicitly requested. | Do not use by default; confirm the user wants the exportable backend. |

Always include an explicit backend flag in generated commands. It avoids relying on the CLI default and makes handoffs reproducible.

## Descriptor And Model-Family Guide

| Family | Typical descriptor/model key | Use when | Avoid or pause when |
| --- | --- | --- | --- |
| DeepPot-SE angular baseline | `se_e2_a` | Need robust first model, compatibility, classical energy/force training, quick water-style smoke validation. | Chemistry/data are broad enough to justify a large atomic model or attention architecture. |
| DeepPot-SE radial baseline | `se_e2_r` | Want lighter radial-only descriptor and angular detail is less important. | Accuracy depends on angular or many-body local geometry beyond radial distances. |
| Three-body DeepPot-SE | `se_e3`, `se_e3_tebd` | Need angular/bond-angle sensitivity with SE-style architecture. | Backend does not support the chosen variant or type-embedding constraints are unclear. |
| DPA-1 | `se_atten`, `se_atten_v2` | Need attention/type-embedding model, pretrainable large-chemistry workflow, or DPA-1 style transfer. | Selected backend has unsupported attention/compression settings. |
| DPA-2 | `dpa2` | Need large atomic model, multi-task pretraining, shared descriptor with multiple heads, or DPA-2-style pretrained setup. | User only needs a small baseline or cannot support PyTorch/JAX/Paddle dependencies. |
| DPA-3 | `dpa3` | Need high-accuracy LAM, DPA3 pretrained fine-tuning, dynamic neighbor settings, or LiGS/message-passing architecture. | Compression is required or user cannot afford GPU/long training. |
| DPA-4 / SeZM | `dpa4` | Need PyTorch SO(3)-equivariant message-passing model in an installed version that supports it. | Non-PyTorch backend is required or the installed version lacks DPA4. |
| Hybrid descriptor | `hybrid` | Need to concatenate multiple descriptors/cutoffs in one model. | User cannot justify each component; simpler baseline not yet tested. |
| Linear/frozen composition | `linear_ener`, frozen model components | Need a linear combination of existing frozen models or pair-model components. | User expects ordinary training from raw data; route post-freeze operations if needed. |
| Pair-table short-range model | `pairtab` or pair component | Need short-range empirical pair potential interpolation/combination. | Pair table is absent or deployment details belong in integrations. |
| DPLR | DPLR energy plus deep Wannier/dipole model | Need long-range electrostatics with virtual/Wannier center machinery. | No dipole/Wannier prerequisite data or user only needs normal short-range DP. |
| Spin energy | spin section plus energy model | Magnetic systems with spin labels/inputs. | Spin data format or backend support is unclear. |
| DOS/property/tensor | `fitting_net.type` = `dos`, `property`, `dipole`, `polar`; matching loss types | Predict non-energy observables with matching labels. | Labels are missing; route label/data design to `data-config`. |
| Hessian energy | energy loss with Hessian prefactors/data | Need second derivatives in PyTorch. | Frozen Hessian output is expected; PyTorch JIT limitations can prevent Hessian deployment outputs. |

## Fitting Target Checklist

| Target | Required label/data signal | Training consequences |
| --- | --- | --- |
| Energy/force/virial | `energy`, `force`, optional `virial` labels. | Use `loss.type: ener`; set virial prefactors to zero if virials are absent. |
| Hessian | Full Hessian matrices per frame. | PyTorch-oriented; add Hessian loss columns and expect larger memory/time. |
| Spin energy | Spin settings and magnetic force/related labels as required. | Backend differences change virtual-type and `sel` behavior. |
| DOS | DOS or atomic DOS arrays with consistent output dimension. | `fitting_net.type: dos`; match `numb_dos` to data. |
| Property | Named global property arrays matching `property_name`. | `fitting_net.type: property`; `task_dim` must match label shape. |
| Tensor | Dipole or polarizability labels, global or atomic as configured. | `fitting_net.type: dipole` or `polar`; `loss.type: tensor`. |
| DPLR | Wannier-center/dipole model and long-range setup. | Usually multi-stage; do not collapse into a single ordinary energy input. |

If the requested target has missing labels, do not paper over it by changing loss weights. Route detailed validation to `data-config` and return with the missing label names.

## Neighbor Selection Strategy

All descriptor families need neighbor limits. Choose one of these routes:

1. **Use explicit `sel` from validated prior run** when the user has production data and prior statistics.
2. **Run or plan `neighbor-stat`** when data are available and the run can inspect maximum neighbors.
3. **Use `sel: auto` / `auto:factor`** where the backend/model supports automatic selection and the training command will not use `--skip-neighbor-stat`.
4. **Use a conservative smoke value only for toy validation** and clearly mark it non-production.

Too-small `sel` can break energy conservation and accuracy. Too-large `sel` wastes memory and slows training. `--skip-neighbor-stat` disables sel checking, automatic sel, and model compression preparation; use it only when the user understands that trade-off or for bounded smoke testing.

## Recommended Defaults

- **Quick baseline:** `se_e2_a`, explicit backend flag, tiny `numb_steps`, `disp_freq` and `save_freq` adjusted to produce `lcurve.out` and a checkpoint quickly.
- **Production starting point:** first prove data and command on a small bounded run, then scale `numb_steps`, batch size, and distributed launch.
- **DPA3 fine-tune:** PyTorch backend, confirm pretrained model name/file, cached availability, type-map subset/compatibility, optional branch/head, and lower learning rate.
- **Multi-task:** PyTorch backend, `shared_dict` + `model_dict`, per-task `loss_dict`, per-task `training.data_dict`, and explicit branch names that will later be used by `show`/`freeze`.
- **CPU-only environment:** draft commands and run only smoke checks; do not imply production training is practical on CPU.

## Selection Output Template

When handing off a model-selection decision, include:

- Chosen backend flag and why.
- Chosen descriptor/model family and why.
- Fitting target and required labels.
- Neighbor-stat / `sel` plan.
- Expected checkpoint and freeze artifact format.
- Any route-outs needed before training can be launched.
