# TFHub conversion troubleshooting

This workflow is legacy and was not runtime verified. Use the failure class and
source behavior below to diagnose an intentional attempt; do not “fix” a TF2
failure by silently changing the documented environment and calling it
supported.

## TensorFlow and Hub API failures

### `reset_default_graph`, `Session`, or `global_variables` is missing

`converter.py` calls TensorFlow 1.x graph APIs directly:

```python
tf.reset_default_graph()
tf.global_variables_initializer()
sess = tf.Session()
initializer = tf.global_variables_initializer()
sess.run(initializer)
for var in tf.global_variables():
    ...
```

It also calls `tensorflow_hub.Module(module_path)`, the old TF1 module API.
These calls are not an ordinary TensorFlow 2.x eager workflow. Install and
isolate the exact legacy TensorFlow/Hub combination required by the checkout,
or stop and record the environment block. A compatibility namespace can be
useful for investigation but is not evidence that this converter works.

### `hub.Module` cannot load the module

Check, in order:

1. the requested URL is exactly the source template with `128`, `256`, or
   `512` and version `/2`;
2. the machine has network access, DNS, and permission to write the TensorFlow
   Hub cache;
3. the TensorFlow Hub release still understands the module format; and
4. no local HDF5 is being mistaken for a valid substitute.

If a trusted HDF5 already exists, the converter can avoid the module download
when `--redownload` is absent. It still needs the legacy TensorFlow imports at
module import time and the rest of the PyTorch conversion stack.

## Dependency and import failures

### `No module named parse`

`convert_from_v1` uses `parse.parse` to decode legacy names such as
`GBlock.0.conv0.module.weight_u`. Install the standalone `parse` package in
the same environment as the converter. This is not Python's built-in
`argparse`.

### `No module named biggan_v1` or `No module named BigGAN`

Use the source layout and working directory expected by the script:

```bash
cd /path/to/BigGAN-PyTorch/TFHub
python converter.py --resolution 128
```

`biggan_v1.py` is a sibling of `converter.py`. The script's `sys.path.append('..')`
expects the current directory's parent to be the repository root for
`BigGAN.py`. A command launched from the repository root can find the sibling
script through Python's script directory but may append the wrong parent for
`BigGAN.py`; do not rely on that accidental behavior.

If an embedding/application imports this module rather than invoking it,
provide both the `TFHub` directory and repository root on `PYTHONPATH`, or
make the import path change explicit in a separately reviewed patch. Do not
edit paths in place during a conversion run without recording the change.

### `torchvision` import or `save_image` failure

The converter imports `torchvision.utils.save_image` at module import time and
uses it for JPEG output. Check that PyTorch and torchvision are a compatible
pair in the legacy environment. This is independent of whether TensorFlow
imports successfully.

## HDF5 and variable-name failures

### HDF5 file exists but conversion reports a missing key

Cache-first behavior trusts any existing `<weights_dir>/biggan-R.h5` unless
`--redownload` is present. A partial, stale, wrong-resolution, or differently
exported file can therefore fail in `load_tf_tensor`, which expects names such
as:

```text
module/Generator/GBlock/.../w:0
module/Generator/GBlock/.../u0:0
module/Generator/ScaledCrossReplicaBN/bn/accumulated_mean:0
```

The exact path is built with `os.path.join`, so inspect the HDF5 keys rather
than guessing. Preserve the old file, choose a clean `weights_dir`, or use
`--redownload` only after confirming that replacing the cache is acceptable.
Do not mix an HDF5 file from one resolution with another output name.

### HDF5 cannot be opened or is empty

Check that the previous process closed the write handle and that the file is
not zero bytes or truncated. `dump_tfhub_to_hdf5` writes all TensorFlow global
variables in one pass, including scalar accumulation counters. Remove or move
an incomplete file only after recording its provenance, then rerun the download
path with network access. A successful open alone does not prove that all
required variables are present.

### EMA variable lookup fails

By default `TFHub2Pytorch` appends `/ema_b999900` to `w`, `b`, `gamma`, and
`beta` lookups. If the source export has only non-EMA names, retry deliberately
with `--no_ema`. Record this choice because it changes the converted weights;
do not use it merely to hide unrelated missing keys.

### `strict=False` still reports incompatible tensors

The root load intentionally tolerates missing `sv0` entries. It does not make
arbitrary shape mismatches safe. Check the selected resolution, `Z_DIMS`,
`biggan_v1` class, source module version, and the v1-to-root remapping before
accepting a `.pth` file. Inspect missing and unexpected keys beyond the known
`sv0` exception.

## CUDA and sample-generation failures

### CUDA is unavailable or the sampler tries to use a CPU

The source sets `DEVICE = 'cuda'` and `generate_sample` calls `G.to(DEVICE)`
and creates latent/class tensors on that device. Conversion-only static work
may import on CPU, but CLI sampling is not a CPU path. Provision a compatible
CUDA PyTorch installation and visible GPU, or omit `--generate_samples` and
report that sampling was not verified.

### Out-of-memory during sampling

`--batch_size` defaults to 64 and all tensors are generated at the selected
resolution. Lower it, start without `--parallel`, and expose only the intended
GPU with `CUDA_VISIBLE_DEVICES`. Use a new samples directory for retries so a
partial JPEG is not mistaken for a successful sample. A conversion that writes
a `.pth` before sampling can leave a valid-looking weight artifact even though
sampling failed; record each stage separately.

### `--parallel` fails or does not use the intended GPUs

`--parallel` calls `torch.nn.parallel.data_parallel`, not a distributed launch
or a configured process group. Confirm the visible-device list and that the
batch can be split across those devices. For a single GPU, omit the flag. Do
not infer multi-GPU correctness from a successful single-GPU conversion.

### Sample image is missing

The script creates `samples_dir` in `__main__`, then names the file
`biggan{resolution}_samples.jpg`. Confirm that `--generate_samples` was
present, that the process reached the post-conversion stage, and that the
parent directory is writable. If `converter.py` is called as a library,
`generate_sample` itself does not create the parent directory.

## Truncation and standing statistics

### A user asks for a truncation flag or a truncation sample

There is no converter CLI flag for truncation. `generate_sample` uses
`torch.randn`, and `biggan_v1.truncated_z_sample` is an unused legacy helper.
The README states that the ported models are set up without truncation and
that standing statistics must be accumulated at each truncation level before
using it. Do not claim that changing the latent distribution alone is enough.

A truncation experiment belongs in a separately verified compatible sampling
workflow: accumulate the generator's standing batch-normalization statistics
for the exact truncation level, retain the resulting state, and compare output
behavior. If that procedure and runtime are unavailable, report truncation as
unsupported/unverified rather than fabricating a command.

## Network, cache, and reproducibility issues

### A rerun unexpectedly reuses old weights

The existence of `biggan-R.h5` suppresses download unless `--redownload` is
passed. Use a new explicit weights directory for independent provenance, or
record `--redownload` and preserve the old HDF5. The script does not write a
manifest containing the remote module digest.

### All-resolutions run stops partway through

The loop is sequential over 128, 256, and 512. List artifacts and logs after a
failure and identify the last completed resolution. Re-run only the missing
resolution with `--resolution`; do not assume later output exists because an
earlier resolution succeeded.

## Evidence and stop rule

The following are static expectations, not checks performed by this skill:

- the expected HDF5 and `.pth` names exist after a complete conversion;
- the optional JPEG has the expected resolution-dependent filename;
- the state dict has only the documented tolerable missing `sv0` entries; and
- an image was generated on the intended CUDA device.

The TFHub module download, TF1 graph execution, HDF5 export, state-dict
conversion, CUDA sampling, and numerical parity remain **not runtime verified**
unless the operator runs them in an approved legacy environment and preserves
the logs and artifact paths. Stop and report the precise blocker when that
runtime is unavailable.
