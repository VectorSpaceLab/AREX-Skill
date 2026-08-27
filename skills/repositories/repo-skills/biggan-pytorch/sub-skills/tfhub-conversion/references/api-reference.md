# TFHub converter API reference

This file mirrors the interfaces in `TFHub/converter.py` and the conversion-only
models in `TFHub/biggan_v1.py`. Signatures and behavior are source-derived and
were not runtime verified. The code is coupled to legacy TensorFlow 1.x,
`tensorflow_hub.Module`, the `parse` package, and the repository's root
`BigGAN.py`.

## Module constants

`converter.py` defines:

```python
DEVICE = 'cuda'
HDF5_TMPL = 'biggan-{}.h5'
PTH_TMPL = 'biggan-{}.pth'
MODULE_PATH_TMPL = 'https://tfhub.dev/deepmind/biggan-{}/2'
Z_DIMS = {128: 120, 256: 140, 512: 128}
RESOLUTIONS = [128, 256, 512]
```

The fixed CUDA device affects only the sample path directly, but it means a
successful import or conversion should not be mistaken for CPU support.

## Public conversion functions

### `dump_tfhub_to_hdf5(module_path, hdf5_path, redownload=False)`

Exports TensorFlow Hub global variables to an HDF5 intermediate.

- If `hdf5_path` exists and `redownload=False`, prints a cache message and
  returns `h5py.File(hdf5_path, 'r')` without constructing the Hub module.
- Otherwise, calls `tf.reset_default_graph()`, constructs
  `hub.Module(module_path)`, initializes globals with
  `tf.global_variables_initializer()`, creates a `tf.Session`, evaluates every
  `tf.global_variables()` entry, and writes a dataset under its TensorFlow
  variable name.
- Closes the write handle, then reopens the HDF5 file read-only and returns
  that handle.

The function requires a valid TF1 graph-mode API and a network or already
available TensorFlow Hub cache when it takes the download path. A partial HDF5
can pass the existence check and fail later during key lookup.

### `convert_biggan(resolution, weight_dir, redownload=False, no_ema=False, verbose=False)`

Converts one supported resolution and returns a constructed root
`BigGAN.Generator`.

- `resolution`: must be `128`, `256`, or `512`.
- `weight_dir`: output directory for `biggan-R.h5` and `biggan-R.pth`.
- `redownload`: forwarded to `dump_tfhub_to_hdf5`; overwrites the HDF5 export
  path when true.
- `no_ema`: passed as `load_ema=not no_ema`; by default the converter looks
  under each TF variable prefix for `/ema_b999900` for `w`, `b`, `gamma`, and
  `beta`. With `no_ema=True`, it uses the non-EMA names.
- `verbose`: prints layer-loading messages from `TFHub2Pytorch`.

The function selects `biggan_v1.Generator128/256/512`, loads the v1 state
mapping, calls `convert_from_v1`, builds `BigGAN.Generator(**get_config(R))`,
loads with `strict=False`, and saves the converted state dictionary using
`torch.save(state_dict, weight_dir / f'biggan-{R}.pth')`. It does not save the
model object, optimizer, or a full training checkpoint.

### `generate_sample(G, z_dim, batch_size, filename, parallel=False)`

Generates a sample JPEG from a converted root generator.

- `G`: the returned root `BigGAN.Generator`.
- `z_dim`: accepted by the signature but the implementation creates `z` with
  `G.dim_z`; callers should pass the resolution's `Z_DIMS` value for clarity.
- `batch_size`: number of random samples and class ids.
- `filename`: output image path; the caller must ensure its parent directory
  exists.
- `parallel`: when true, calls `nn.parallel.data_parallel(G, (z,
  G.shared(y)))`; otherwise calls `G(z, G.shared(y))`.

The implementation calls `G.eval()`, moves `G` to `cuda`, uses
`torch.no_grad()`, draws `z = torch.randn(batch_size, G.dim_z).to('cuda')`,
draws random class ids from 0 through 999, and calls `save_image(images,
filename, scale_each=True, normalize=True)`. It uses ordinary normal latent
vectors; truncation is not implemented here.

## Internal state mapper

### `TFHub2Pytorch(state_dict, tf_weights, resolution=256, load_ema=True, verbose=False)`

`TFHub2Pytorch` is the name/layout bridge between HDF5 TensorFlow variables and
the deprecated v1 PyTorch generator state dict.

Important class constants:

```python
TF_ROOT = 'module'
NUM_GBLOCK = {128: 5, 256: 6, 512: 7}
w = 'w'; b = 'b'; u = 'u0'; v = 'u1'
gamma = 'gamma'; beta = 'beta'
```

When `load_ema=True`, the mapper appends `/ema_b999900` to the `w`, `b`,
`gamma`, and `beta` variable suffixes. `load()` calls `load_generator()` and
returns the modified state dict.

`load_generator()` covers:

- every resolution-dependent `GBlock` convolution and two HyperBN layers;
- self-attention `theta`, `phi`, `g`, and `o_conv`, plus attention `gamma`;
- the shared class `linear` layer;
- spectral-normalized `G_Z/G_linear`;
- the output `conv_2d` colorize layer; and
- `ScaledCrossReplicaBN` gain, bias, running mean, running variance, and
  accumulation counter.

The mapper's tensor-layout rules are significant:

- convolution `w` is permuted with `.permute(3, 2, 0, 1)`;
- linear `w` is transposed with `.permute(1, 0)`;
- spectral-normalization vectors are squeezed where required;
- BN accumulated statistics and counters are copied into the target state;
- `u0`/`u1`/`weight_bar` are kept under the target spectral-normalization
  naming expected by `biggan_v1.py`.

`load_tf_tensor(prefix, var, device='0')` looks up
`os.path.join(prefix, var) + ':0'` by default in the HDF5 mapping and returns a
`torch.from_numpy` tensor. Missing or differently named HDF5 datasets are
usually a source-version, EMA-selection, or incomplete-cache problem.

## v1-to-root remapping

### `convert_from_v1(hub_dict, resolution=128)`

Maps the deprecated v1 state dictionary to root `BigGAN.py` names. It uses the
third-party `parse` package for names such as
`GBlock.{:d}.{}.module.{}` and `GBlock.{:d}.{}.bn.{}`. It then applies
resolution-dependent attention and latent maps.

The map includes:

- shared and class-conditional linear layers;
- `GBlock` conv0/conv1/conv_sc names;
- HyperBN gain/bias and stored mean/variance;
- self-attention tensors;
- output-layer BN and colorize tensors.

It intentionally drops v1 `num_batches_tracked` entries during the remap. It
also reconstructs the first linear layer's `(4, 4, 96 * 16, -1)` layout,
transposes the shared embedding, concatenates the v1 class/latent condition
parts for BN weights, and unsqueezes `weight_u` tensors where root shapes
require it. Do not apply this mapper to an arbitrary checkpoint: it assumes
the TFHub BigGAN v1 variable naming and one of the three supported resolutions.

## Conversion configuration

### `get_config(resolution)`

Returns the root generator configuration used for loading the converted
weights. The important values are:

| Setting | Value or mapping |
|---|---|
| `G_param`, `D_param` | `SN` |
| `G_ch`, `D_ch` | `96` |
| `D_wide`, `G_shared`, `hier` | `True`, `True`, `True` |
| `shared_dim`, `n_classes` | `128`, `1000` |
| `dim_z` | 120 / 140 / 128 for 128 / 256 / 512 |
| `G_attn` | `64` / `128` / `64` for 128 / 256 / 512 |
| `cross_replica`, `mybn` | `False`, `False` |
| `G_eval_mode`, `skip_init`, `no_optim` | `True`, `True`, `True` |
| `accumulate_stats` | `False` |
| `num_standing_accumulations` | `16` (not performed by conversion) |
| `G_fp16`, `G_mixed_precision` | `False`, `False` |
| `BN_eps`, `SN_eps` | `1e-4`, `1e-4` |
| `num_G_SVs`, `num_G_SV_itrs` | `1`, `1` |

The config explains why the saved file is intended for the root BigGAN
architecture, but it does not establish numerical compatibility with every
modern PyTorch release.

## Deprecated v1 model API

`TFHub/biggan_v1.py` defines `Generator128`, `Generator256`, and `Generator512`
with the old TFHub-compatible topology. The generators use:

- a class embedding linear layer;
- a spectral-normalized first generator linear layer;
- conditional `GBlock`s with `ConditionalBatchNorm2d`;
- self-attention at a resolution-dependent block;
- a scaled cross-replica BN output stage; and
- a spectral-normalized colorize convolution.

The file also contains `SpectralNorm`, `SelfAttention`, `GBlock`,
`ConditionalBatchNorm2d`, and a `Discriminator` reference. The conversion
script uses the generator classes and their state-dict layout, not the v1
`Discriminator`.

`truncated_z_sample(batch_size, z_dim, truncation=0.5, seed=None)` uses
`scipy.stats.truncnorm` and returns a scaled truncated-normal NumPy array, but
it is not called by the CLI. `denorm` is also a helper only. Neither helper
makes truncation-supported sampling available without the required standing
statistics procedure.

## CLI flags (`parse_args`)

All flags in the source are listed below. Boolean flags are false unless
present.

| Flag | Default | Behavior |
|---|---|---|
| `--resolution`, `-r` | `None` | Integer choice `128`, `256`, or `512`; `None` converts all resolutions. |
| `--redownload` | `False` | Re-fetch/re-export the TFHub module and overwrite the existing HDF5 path if present. |
| `--weights_dir` | `pretrained_weights` | Directory for HDF5 intermediates and `.pth` state dictionaries. Created by the script. |
| `--samples_dir` | `pretrained_samples` | Directory for generated JPEGs. Created by the script. |
| `--no_ema` | `False` | Do not select `/ema_b999900` variables for mapper suffixes. |
| `--verbose` | `False` | Print extra per-layer loading messages. |
| `--generate_samples` | `False` | After each conversion, generate a random-class sample JPEG. |
| `--batch_size` | `64` | Number of latent vectors/class ids for each sample image grid. |
| `--parallel` | `False` | Use `torch.nn.parallel.data_parallel` for generation. Requires compatible visible CUDA devices. |

There is no CLI flag for truncation, seed, class id, CPU mode, module URL,
HDF5 filename, or standing-stat accumulation. Change requests involving those
controls require deliberate source modification and separate verification.
