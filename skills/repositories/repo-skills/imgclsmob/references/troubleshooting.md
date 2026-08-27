# Cross-cutting troubleshooting

## Import and version boundary

Use the same interpreter for installation and execution. The verified core
requires an MXNet 1.9.1-compatible NumPy version below 2, plus compatible CPU
PyTorch/torchvision wheels and the external `pytorchcv` provider. MXNet 1.9.1
can fail during import when NumPy 2 APIs such as `PZERO` are absent; repair by
using a compatible NumPy release rather than patching model code.

The repository's local framework utilities are not the same as the public
provider packages. If a task needs the repository's train/eval entrypoints,
install the selected framework package and make sure that entrypoint can import
its sibling utility modules. The bundled inference, dataset-layout, command,
and conversion-plan helpers intentionally avoid those source-only imports.

Do not install the broad legacy dependency list blindly. It mixes obsolete
TensorFlow GPU, Tensorpack, Chainer, Keras-MXNet, and CUDA package variants.
Route a missing optional backend through
[framework-compatibility](../sub-skills/framework-compatibility/SKILL.md), and
record the exact import/package result before proceeding.

## Model and checkpoint failures

- An unsupported provider name is an API/model-selection error. Use a name
  registered by the selected provider and preserve lowercase model identifiers.
- A pretrained request may download weights. For an offline smoke, omit
  `pretrained` and use one synthetic input; for a real run, use a local
  checkpoint and matching architecture/class/channel settings.
- Gluon `.params`, PyTorch `.pth`/state dictionaries, Keras HDF5, TF1 NumPy
  archives, TF2 weights, Chainer NPZ, and TFLite bytes are different formats.
  Route translation to [conversion](../sub-skills/conversion/SKILL.md), not to
  a generic `torch.load` or `load_parameters` guess.
- PyTorch `module.` prefixes indicate DataParallel wrapping. Removing that
  prefix does not fix a different model, class count, or tensor shape. Use the
  model-inference checkpoint reference for key diagnostics.
- A `rank-2`/class-count assertion from a bundled smoke is useful: it proves
  the model was called, but it is not an accuracy claim.

## Dataset and command failures

Run the bundled filesystem-only checker before any real dataset command. It
must report `ok`; it never decodes images, imports frameworks, or downloads
native caches. `ImageNet1K` means `train/<class>/...` and `val/<class>/...` with
1000 class directories in each split. `ImageNet1K_rec` means four non-empty
record/index files and is Gluon-only. CIFAR/SVHN cache checks are presence-only,
so a non-empty directory does not prove that a framework can decode it.

Use the command builder for a safe plan. Start CPU runs with `--num-gpus 0`,
zero workers, and a small batch. Keep `--use-pretrained` and `--all` off for
no-network work. A local model resume file is distinct from an optimizer
resume state; set `--start-epoch` deliberately when resuming training.

## Backend and hardware failures

CPU success is not CUDA success. Positive GPU counts require a matching
framework build, compatible drivers/runtime, and an actual device probe. The
current core evidence does not validate the repository's GPU conversion cases.
TensorFlow 1, TensorFlow 2, Keras, Chainer, and Tensorpack require separate
compatibility decisions; do not mix their generations in one environment and
do not silently fall back to PyTorch while claiming the requested backend.

## Side-effect policy

The bundled helpers are no-network and non-destructive by default. Treat
pretrained providers, missing native dataset caches, bulk conversion/publication
helpers, long training, and output-directory writes as explicit side effects.
Validate paths and backend requirements first, then ask for or document the
user's permission and resource boundary before enabling them.
