# Inference troubleshooting

## Import and provider failures

- **`ModuleNotFoundError: mxnet` or `gluoncv2`:** install a compatible CPU
  MXNet and the public `gluoncv2` provider package/environment. The source
  public provider import is `gluoncv2.model_provider`. PyTorch availability
  does not prove that Gluon is installed.
- **`ModuleNotFoundError: torch` or `pytorchcv`:** install the CPU PyTorch
  runtime and the external `pytorchcv` provider. Do not replace the requested
  provider with a torchvision model.
- **`ModuleNotFoundError: gluoncv2`:** install the public `gluoncv2` package
  (and its compatible MXNet runtime), or use the package source distribution
  in the environment that owns the model command.
- **`Unsupported model`:** the provider lowercases the requested name but does
  not guess aliases. Use a name present in the installed provider's registry,
  such as `resnet18`.

## Initialization and preprocessing

- **Gluon reports an uninitialized parameter:** the script explicitly calls
  `net.initialize(mx.init.MSRAPrelu(), ctx=mx.cpu())` before its first forward.
  Check that the installed MXNet version and provider are compatible.
- **Output shape is not `(1, C)`:** verify NCHW order, three input channels,
  the square crop, and that the selected provider name is an image classifier
  rather than a detector, segmenter, pose model, or feature extractor.
- **Expected class-count assertion fails:** `--expected-classes` defaults to
  `1000`. Select the checkpoint's actual class count and pass that count to
  `--expected-classes`; do not hide a classifier mismatch by ignoring keys.
- **Predictions look wrong:** verify RGB conversion, `/255.0`, the exact
  ImageNet mean/std, shorter-side resize, and center crop. The zero-image
  default is not suitable for judging accuracy.

## Local checkpoint failures

- **The checkpoint path is missing or cannot be opened:** confirm that the
  path is a local regular file and that the process can read it. The scripts
  do not download or search a cache.
- **Gluon load failure:** use an MXNet parameter file produced for the exact
  provider model, class count, input-channel count, and compatible parameter
  names. The scripts pass `ignore_extra=False`, so missing or extra names are
  intentionally visible; tensor shape mismatches remain errors.
- **PyTorch says the checkpoint is not a mapping:** save a state dict directly
  or under a top-level `state_dict` key. Optimizer-only files and arbitrary
  training metadata are not accepted.
- **PyTorch reports `module.` keys:** rerun with `--remove-module` only when
  the file was saved by `torch.nn.DataParallel`. Do not strip arbitrary key
  prefixes.
- **PyTorch reports missing/unexpected keys or a size mismatch:** rebuild with
  the exact provider model and `--classes` value. Loading is strict and these
  failures are useful evidence of an incompatible checkpoint.
- **CUDA deserialization error:** the script always uses
  `torch.load(FILE, map_location=torch.device("cpu"))`; keep the model and
  input on CPU. A checkpoint's device provenance does not change its model
  compatibility.

## Device, image, and statistics issues

- **Pillow is missing:** install Pillow only when using `--image`; omitted
  images use NumPy's zero-image smoke and do not need Pillow.
- **A small or unusual image fails during crop:** ensure it decodes to a
  positive-size RGB image. The script resizes the shorter side before taking
  the centered crop.
- **`--input-size` or `--top-k` is rejected:** both must be positive. `top-k`
  is capped at the number of output classes.
- **Parameter count differs from a model card:** compare provider version,
  architecture variant, classifier count, and whether the other count includes
  frozen/non-trainable parameters. The printed count is trainable parameters,
  not FLOPs or latency.
- **FLOPs/MACs helper fails on a custom layer:** hook-based statistics are not
  universal. Treat the printed parameter count and output-shape assertion as
  the bounded smoke result, or use the provider's supported layer set.

For long training/evaluation or dataset-root and resume validation, use
[training-evaluation](../../training-evaluation/SKILL.md). For parameter
conversion, use [conversion](../../conversion/SKILL.md). For TensorFlow,
Keras, or Chainer backend issues, use
[framework-compatibility](../../framework-compatibility/SKILL.md).
