# Model and dataset overview

Read this when choosing a model, resolution, dataset key, or latent/class
configuration. Facts are distilled from the repository's model architecture
and utility dictionaries and were checked through live imports.

## Model modules

- `BigGAN.Generator` and `BigGAN.Discriminator` implement the main residual
  BigGAN architecture. Generator resolutions are 32, 64, 128, 256, and 512;
  the default attention string is `64`.
- `BigGANdeep.Generator` and `BigGANdeep.Discriminator` use the deep residual
  block pattern and accept `G_depth`/`D_depth`. The launch recipe uses
  `--model BigGANdeep`, depth 2, and larger channel widths.
- Both expose `G_D(G, D)` for the training loop. The generator is conditional:
  labels are integer class ids passed through `G.shared`, and hierarchical
  latent mode splits `z` into slots.
- Important constructor families are `G_ch`, `D_ch`, `dim_z`, `resolution`,
  `G_attn`/`D_attn`, `n_classes`, `G_shared`, `shared_dim`, `hier`,
  `G_param`/`D_param`, `norm_style`, `G_fp16`/`D_fp16`, and initialization
  choices. Constructors accept extra config keys through `**kwargs`.

## Dataset keys

| Key family | Loader | Image size | Classes | Root under `data_root` |
|---|---|---:|---:|---|
| `I32`, `I64`, `I128`, `I256` | ImageFolder | 32/64/128/256 | 1000 | `ImageNet` |
| `I32_hdf5`, `I64_hdf5`, `I128_hdf5`, `I256_hdf5` | `ILSVRC_HDF5` | 32/64/128/256 | 1000 | `ILSVRC32.hdf5` etc. |
| `C10` | CIFAR10 subclass | 32 | 10 | `cifar` |
| `C100` | CIFAR100 subclass | 32 | 100 | `cifar` |

The class-sheet widths are 50 for 32/64 ImageNet, 20 for 128/256 ImageNet,
10 for C10, and 100 for C100. Keep labels in the integer range expected by the
selected class count.

## Outputs and metrics

Training creates a configuration-derived experiment name unless
`--experiment_name` is supplied. Checkpoints contain generator/discriminator
weights, optimizer states, `state_dict`, and optionally `G_ema`; suffixes such
as `copy0` and `best0` are separate files. Sampling can write JPEG sheets,
random samples, interpolation sheets, and `samples.npz`. Inception moments are
loaded from `<dataset-without-_hdf5>_inception_moments.npz`.
