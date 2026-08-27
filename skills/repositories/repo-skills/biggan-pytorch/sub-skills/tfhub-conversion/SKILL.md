---
name: tfhub-conversion
description: "Converts legacy DeepMind TFHub BigGAN generator modules at 128,
  256, or 512 resolution into BigGAN-PyTorch state dictionaries and optionally
  generates CUDA sample images through the repository's reference converter."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TFHub conversion

Use this route only for the repository's legacy `TFHub/converter.py` workflow:
porting a DeepMind BigGAN generator downloaded from TensorFlow Hub into a
PyTorch `.pth` state dictionary. The supported resolutions are **128, 256, and
512**. This is not a general TensorFlow-to-PyTorch conversion tool and it does
not convert a discriminator or a complete training checkpoint.

> **Reference-only status.** This workflow is reference-only unless an isolated
> environment with legacy TensorFlow 1.x-compatible APIs, TensorFlow Hub, the
> required Python packages, network access (or a suitable existing HDF5
> intermediate), and a compatible CUDA GPU for sampling is deliberately
> available. It was **not runtime verified**. In particular, do not report a
> successful conversion merely because the Python files parse or because
> `load_state_dict(..., strict=False)` returns.

## Read before acting

- Read `references/workflows.md` for the end-to-end command sequence, working
  directory requirement, download/cache behavior, outputs, and sample checks.
- Read `references/api-reference.md` for the converter functions, resolution
  table, TensorFlow-to-PyTorch mappings, and every command-line flag.
- Read `references/troubleshooting.md` before changing environments or
  interpreting a failure.

## Prerequisites and hard constraints

The converter imports all of the following: PyTorch, torchvision, h5py,
TensorFlow, `tensorflow_hub`, and `parse`. The adjacent
`TFHub/biggan_v1.py` also imports NumPy and SciPy. The repository's normal
PyTorch dependencies therefore are not sufficient by themselves. Keep the
legacy TensorFlow/TFHub dependencies isolated from the normal training
environment.

The source uses TensorFlow 1.x graph/session APIs, including
`tf.reset_default_graph()`, `tf.global_variables_initializer()`, and
`tf.Session()`, plus the TF1-style `hub.Module(...)` API. **TensorFlow 2.x is
not a drop-in replacement.** Do not “fix” this route by silently substituting
TF2 or by claiming compatibility through `tf.compat.v1` without separately
reviewing the TFHub module and the complete conversion behavior.

The converter has two important layout assumptions:

1. Launch it from the `TFHub` directory, for example
   `cd /path/to/BigGAN-PyTorch/TFHub`. It imports the sibling
   `biggan_v1.py` and appends `..` to find the repository-level `BigGAN.py`.
   Running from another directory can produce relative-import or module-path
   failures.
2. `DEVICE` is hard-coded to `cuda`. Conversion itself reads weights and builds
   a PyTorch generator, but the optional sample path moves the generator and
   tensors to CUDA. There is no supported CPU sampling fallback in this
   script.

## Operational outline

1. Choose one resolution first. The `--resolution/-r` flag accepts exactly
   `128`, `256`, or `512`. Omitting it converts all three in sequence.
2. Ensure the TFHub URL can be reached, or place the matching intermediate
   `biggan-<resolution>.h5` in the selected weights directory. If the HDF5
   exists and `--redownload` is absent, the converter reuses it without
   contacting TFHub.
3. Run `converter.py` from `TFHub`. It loads the module with
   `tensorflow_hub`, initializes the TF graph, writes every TF global variable
   to HDF5, maps the HDF5 variables through the legacy `biggan_v1.py` model and
   `convert_from_v1`, then instantiates the current `BigGAN.Generator`.
4. It saves the converted generator **state dictionary** as
   `biggan-<resolution>.pth` under `--weights_dir`. This is not a complete
   checkpoint containing optimizer, discriminator, or EMA training objects.
5. If `--generate_samples` is supplied, it samples random latent vectors and
   random ImageNet class ids on CUDA and writes
   `biggan<resolution>_samples.jpg` under `--samples_dir`. Use `--parallel` only
   when the visible GPUs and the legacy `nn.parallel.data_parallel` path are
   appropriate.
6. Treat output existence as only a file-level check. A meaningful acceptance
   check requires loading the intended state dictionary into the matching
   current generator and visually or numerically checking generated images;
   neither conversion nor `strict=False` loading proves semantic equivalence.

## Truncation limitation

The TFHub README explicitly says that this port is currently set up to run
without truncation. The converter's `generate_sample` does **not** call
`biggan_v1.truncated_z_sample`; it uses `torch.randn` and does not establish
standing statistics for truncation levels. The missing per-truncation standing
statistics mean that truncation curves or quality claims at non-default
truncation values are not reproduced by this route. Accumulate and validate
standing statistics separately before attempting truncation experiments, and
record that extra procedure with the result.

## Scope and non-goals

This route covers only the checked-in TFHub conversion script and its adjacent
legacy reference model. It does not modernize the code, download weights on the
user's behalf, guarantee TF2 operation, provide a CPU implementation, create
standing statistics, or certify image quality. Do not import this sub-skill into
an automatic runtime router without preserving its explicit reference-only and
not-runtime-verified warnings.
