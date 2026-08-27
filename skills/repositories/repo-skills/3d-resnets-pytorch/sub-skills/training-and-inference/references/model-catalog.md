# Model catalog and fine-tuning map

`main.py -h` only shows a shortened model-depth hint. Use this catalog for the full supported matrix.

## Supported families

| Family flag | Supported depths | Final head module | Family-specific knobs | Good `ft_begin_module` values |
| --- | --- | --- | --- | --- |
| `resnet` | 10, 18, 34, 50, 101, 152, 200 | `fc` | `--resnet_shortcut`, `--conv1_t_size`, `--conv1_t_stride`, `--no_max_pool`, `--resnet_widen_factor` | `fc`, `layer4`, `layer3` |
| `resnet2p1d` | 10, 18, 34, 50, 101, 152, 200 | `fc` | same as `resnet` | `fc`, `layer4`, `layer3` |
| `preresnet` | 10, 18, 34, 50, 101, 152, 200 | `fc` | `--resnet_shortcut`, `--conv1_t_size`, `--conv1_t_stride`, `--no_max_pool` | `fc`, `layer4`, `layer3` |
| `wideresnet` | 50, 101, 152, 200 | `fc` | `--wide_resnet_k`, plus the shared ResNet knobs | `fc`, `layer4` |
| `resnext` | 50, 101, 152, 200 | `fc` | `--resnext_cardinality`, plus the shared ResNet knobs | `fc`, `layer4` |
| `densenet` | 121, 169, 201, 264 | `classifier` | `--conv1_t_size`, `--conv1_t_stride`, `--no_max_pool` | `classifier`, `denseblock4`, `denseblock3` |

## Source versus target class counts

When you fine-tune from a pretrained checkpoint, keep the source label count separate from the downstream label count.

| Published checkpoint family | `--n_pretrain_classes` |
| --- | --- |
| Kinetics-700 (`K`) | 700 |
| Kinetics-700 + Moments in Time (`KM`) | 1039 |
| Kinetics-700 + Moments in Time + STAIR-Actions (`KMS`) | 1139 |
| Kinetics-700 + STAIR-Actions (`KS`) | 800 |
| Moments in Time (`M`) | 339 |
| Moments in Time + STAIR-Actions (`MS`) | 439 |
| STAIR-Actions (`S`) | 100 |

The repository README also uses Kinetics-700 pretrained releases, even though the historical CLI help text still mentions older Kinetics-400/600 recipes.

Downstream examples from this repository:

| Dataset | `--n_classes` |
| --- | --- |
| ActivityNet | 200 |
| Kinetics (older recipes) | 400 or 600 |
| Kinetics-700 pretrained fine-tuning | usually the target task count, not 700 |
| UCF101 | 101 |
| HMDB51 | 51 |

## Fine-tuning module selection

`get_fine_tuning_parameters()` matches the first top-level module name it sees after removing `module.` and `features.` prefixes. That means:

- `--ft_begin_module fc` starts training at the classifier head for ResNet-style models.
- `--ft_begin_module classifier` starts training at the DenseNet head.
- `--ft_begin_module layer4` keeps the last residual stage and the head trainable.
- An unknown module name can leave the optimizer with no trainable parameters.

## Common checkpoints and shape implications

- `resume_path` requires the exact same `arch` string, so changing either `--model` or `--model_depth` invalidates the checkpoint as a resume target.
- `pretrain_path` is for weight transfer, not exact resume. The source checkpoint's classifier is loaded first, then the final head is replaced for the target class count.
- If a checkpoint was saved from `nn.DataParallel`, the key names will usually start with `module.` and may need `scripts/strip_dataparallel.py` before use in bare-state-dict tools.

## Input-channel note

The model families all expect RGB input by default. If you switch to `--input_type flow`, the runtime trims the mean/std vectors to two channels and the loader requires HDF5 input files.
