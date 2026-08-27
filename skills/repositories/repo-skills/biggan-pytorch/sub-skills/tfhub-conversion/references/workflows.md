# TFHub conversion workflows

This reference describes the source repository's `TFHub/converter.py` as a
legacy procedure. It is self-contained, but it is not a guarantee that the
procedure can run on a modern machine. The workflow was not runtime verified.
Use it only after the operator has intentionally supplied compatible
TensorFlow 1.x, TensorFlow Hub, `parse`, PyTorch/torchvision, and CUDA support.

## 1. Inspect the source and choose the artifact

The converter accepts the DeepMind TFHub BigGAN generator modules at:

```text
https://tfhub.dev/deepmind/biggan-128/2
https://tfhub.dev/deepmind/biggan-256/2
https://tfhub.dev/deepmind/biggan-512/2
```

The supported resolution-to-latent mapping is:

| Resolution | CLI latent dimension | Legacy generator blocks | HDF5 intermediate | PyTorch output |
|---:|---:|---:|---|---|
| 128 | 120 | 5 | `biggan-128.h5` | `biggan-128.pth` |
| 256 | 140 | 6 | `biggan-256.h5` | `biggan-256.pth` |
| 512 | 128 | 7 | `biggan-512.h5` | `biggan-512.pth` |

`--resolution` selects one row. If omitted, the script processes all three
rows. Decide whether an existing HDF5 file is trusted and reusable before
using the default cache behavior; the HDF5 file is an intermediate export,
not the final PyTorch artifact.

## 2. Prepare the legacy execution context

The source imports these runtime components:

- TensorFlow with TensorFlow 1.x graph APIs;
- `tensorflow_hub`, including the old `hub.Module` interface;
- `parse`, used by `convert_from_v1` to parse layer names;
- `h5py` for the intermediate file;
- PyTorch and `torchvision.utils.save_image`;
- NumPy and SciPy (`scipy.stats.truncnorm`) for the deprecated
  `biggan_v1.py` reference model.

The root `BigGAN.py` is imported after `sys.path.append('..')`. Start in the
`TFHub` directory so that this append resolves to the repository root and the
sibling `biggan_v1.py` import is unambiguous:

```bash
cd /path/to/BigGAN-PyTorch/TFHub
python -c "import tensorflow as tf, tensorflow_hub as hub, parse, torch, h5py; print(tf.__version__)"
```

This is a probe only. It does not establish that the exact Hub release and
TensorFlow 1.x graph semantics are compatible. In particular, importing a
modern TensorFlow 2.x package is not a supported substitute: the converter
calls `tf.reset_default_graph()`, `tf.global_variables_initializer()`,
`tf.Session()`, and `tf.global_variables()`, then instantiates
`hub.Module(module_path)`.

Ensure CUDA before requesting samples:

```bash
CUDA_VISIBLE_DEVICES=0 python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

The converter defines `DEVICE = 'cuda'` unconditionally. Do not use a CPU
probe as evidence that conversion plus sampling works.

## 3. Convert one resolution

A controlled one-resolution invocation is:

```bash
cd /path/to/BigGAN-PyTorch/TFHub
CUDA_VISIBLE_DEVICES=0 python converter.py \
  --resolution 128 \
  --weights_dir /absolute/path/to/weights \
  --samples_dir /absolute/path/to/samples \
  --verbose
```

The script creates `weights_dir` and `samples_dir` with `os.makedirs(...,
exist_ok=True)`. Use explicit, writable directories so that generated files do
not get confused with source files or an unrelated experiment.

The stages for resolution `R` are:

1. **Resolve the module.** `MODULE_PATH_TMPL` formats the TFHub URL for `R`.
2. **Reuse or download/export.** `dump_tfhub_to_hdf5` opens
   `<weights_dir>/biggan-R.h5` in read mode if it already exists and
   `redownload` is false. Otherwise it resets the TF1 default graph,
   constructs `hub.Module(module_path)`, initializes global variables in a
   `tf.Session`, reads every TensorFlow global variable, and writes each one
   to an HDF5 dataset keyed by its TensorFlow variable name.
3. **Build the legacy reference topology.** The module
   `biggan_v1.py` supplies `Generator128`, `Generator256`, or `Generator512`
   and the initial PyTorch state-dict shape. This code is deprecated and is
   present to make the port possible; it is not the normal root sampling
   implementation.
4. **Load TF tensors into the v1 state dict.** `TFHub2Pytorch` walks the
   generator blocks, attention, linear layers, colorize layer, conditional
   HyperBN layers, and scaled cross-replica BN. TensorFlow convolution and
   linear dimensions are permuted into the PyTorch layout. EMA variable names
   are selected by default.
5. **Remap v1 names.** `convert_from_v1` uses `parse.parse` and explicit
   resolution-dependent maps to rename the old v1 state dict into the root
   BigGAN naming scheme. It also handles the concatenated class/latent BN
   dimensions, first-linear reshaping, shared embedding transpose, and
   spectral-normalization `u0` shape adjustments.
6. **Construct and save the root model.** `get_config(R)` supplies the
   conversion configuration, `BigGAN.Generator(**config)` is instantiated,
   and the remapped dictionary is loaded with `strict=False` to ignore missing
   `sv0` entries. The dictionary—not the full model object or optimizer—is
   saved with `torch.save` to `<weights_dir>/biggan-R.pth`.

The converter does not compare TensorFlow and PyTorch outputs. Treat a clean
exit and a file on disk as necessary but not sufficient evidence of parity.

## 4. Convert and sample in one pass

The README's sample recipe is:

```bash
cd /path/to/BigGAN-PyTorch/TFHub
CUDA_VISIBLE_DEVICES=0 python converter.py -r 128 --generate_samples --parallel
```

A more explicit version is:

```bash
CUDA_VISIBLE_DEVICES=0 python converter.py \
  --resolution 256 \
  --weights_dir /absolute/path/to/weights \
  --samples_dir /absolute/path/to/samples \
  --generate_samples \
  --batch_size 16 \
  --parallel
```

After conversion, `generate_sample` switches the returned generator to eval
mode, moves it to `cuda`, creates `batch_size` standard-normal latent vectors,
creates random integer ImageNet class ids in `[0, 1000)`, and calls the root
model as `G(z, G.shared(y))`. With `--parallel`, it uses
`torch.nn.parallel.data_parallel`; without it, it calls the generator on the
current CUDA device. It writes normalized, per-image-scaled output with
`torchvision.utils.save_image` to:

```text
<samples_dir>/biggan128_samples.jpg
<samples_dir>/biggan256_samples.jpg
<samples_dir>/biggan512_samples.jpg
```

The `--parallel` switch is a request to use PyTorch data parallelism, not a
portable distributed-training setup. Keep the CUDA devices visible and the
batch size within memory. A single GPU can use the non-parallel path.

## 5. Convert all resolutions

To convert every supported module, omit `--resolution`:

```bash
CUDA_VISIBLE_DEVICES=0 python converter.py \
  --weights_dir /absolute/path/to/weights \
  --samples_dir /absolute/path/to/samples \
  --generate_samples \
  --batch_size 4
```

The script loops over `RESOLUTIONS`, which is `[128, 256, 512]` in the source.
A failure at a later resolution does not make earlier artifacts equivalent to a
complete run; record which HDF5, `.pth`, and JPEG files were produced.

## 6. Cache and re-download policy

Default behavior is cache-first:

```text
biggan-R.h5 exists and --redownload is absent  -> reuse HDF5
otherwise                                      -> fetch Hub module and rewrite HDF5
```

`--redownload` overwrites the existing HDF5 export. It does not mean “refresh
only if the remote module changed”; it deliberately takes the overwrite path.
The `.pth` file is then overwritten by the subsequent conversion. Preserve a
copy or use a new `weights_dir` when provenance matters.

The module download may be served from the local TensorFlow Hub cache even
when the converter does not need a live network request. Conversely, a stale
or partial HDF5 can suppress the download and fail later during variable lookup.
Inspect file size and HDF5 keys before treating a cache as trusted.

## 7. Truncation limitation

Do not add a truncation argument to the converter command: none exists. The
legacy helper `biggan_v1.truncated_z_sample` can draw a truncated normal for
reference code, but `converter.py` does not call it. Its sample path uses
`torch.randn` and the conversion config sets `accumulate_stats=False`.

The README warns that the ported models are set up for use without truncation.
If a later sampling experiment needs truncation, standing batch-normalization
statistics must be accumulated separately at each desired truncation level in
the compatible root BigGAN sampling workflow. Do not claim that the converted
`.pth` has valid truncation-specific statistics merely because it contains
TensorFlow running statistics.

## 8. Artifact handoff checklist

Record the following for each conversion:

- source URL and resolution;
- TensorFlow, `tensorflow_hub`, `parse`, PyTorch, torchvision, h5py, NumPy,
  SciPy, and CUDA versions;
- whether HDF5 was reused or re-downloaded;
- `--no_ema` choice and whether `--verbose` was enabled;
- absolute HDF5, `.pth`, and optional JPEG paths;
- visible CUDA devices and batch size for sampling;
- load-state missing/unexpected keys, if any; and
- explicit statement that TFHub download, conversion, CUDA sampling, and
  numerical parity are unverified unless the operator actually runs and
  records those checks.
