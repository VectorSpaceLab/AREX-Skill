# Conversion troubleshooting

Use the smallest safe check first. From this directory, the argument inspector
uses only the Python standard library; it does not import `convert_models.py`,
open checkpoints, create an output, initialize a backend, or use a network:

```bash
python3 scripts/inspect_conversion_args.py --list
```

For a concrete plan, add the four identity flags plus both parameter paths:

```bash
python3 scripts/inspect_conversion_args.py \
  --src-fwk gluon --dst-fwk pytorch \
  --src-model resnet18 --dst-model resnet18 \
  --src-params ./resnet18.params --dst-params ./resnet18.pth
```

A nonzero exit is a plan block. It does not prove that the framework
implementation or checkpoint is broken.

## Unknown or reversed framework label

**Symptom:** the inspector reports an unknown label or unsupported edge.

**Repair:** use exact labels `gluon`, `mxnet`, `pytorch`, `chainer`, `keras`,
`tensorflow`, `tf2`, and `tfl`. Use `tensorflow` for legacy TensorFlow 1.x;
there is no `tf1` alias. Use `tf2` for TensorFlow 2.x/Keras models and `tfl`
only as the TF2-to-TFLite destination. Consult [the direction
matrix](direction-matrix.md) rather than reversing `--src-fwk` and
`--dst-fwk`.

The real CLI's parser accepts strings rather than enumerating labels, but its
model-preparation and dispatch branches support only the matrix. Do not “fix”
`tensorflow -> tf2` by swapping labels: that edge is absent and needs a
separate conversion workflow.

## Required flags, paths, and collisions

**Symptom:** the inspector reports missing flags, a non-positive count, or
identical source/destination paths.

**Repair:** provide `--src-fwk`, `--dst-fwk`, `--src-model`, `--dst-model`,
`--src-params`, and `--dst-params`. The real parser defaults both paths to an
empty string, but loaders and writers generally need explicit local paths. Use
positive values for all four class/channel counts. Never use the same path for
source and destination.

`--check-files` performs only a presence check. For ordinary file sources it
requires an existing regular file and does not open it. For an MXNet source,
`--src-params` is a prefix for epoch 0; the safe check looks for the usual
`<prefix>-symbol.json` and `<prefix>-0000.params` pair. It does not load or
parse them. Without `--check-files`, path existence is not asserted.

The destination extension is a convention, not a CLI validation rule. Use
`.params`, `.pth`, `.npz`, `.h5`/`.tf2.h5`, or `.tflite` according to the edge
and then verify the resulting artifact through model inference. TF1's
`np.savez_compressed` may append `.npz` when the destination path does not
already have that suffix.

## CPU-only Gluon to PyTorch

**Symptom:** a plan includes `--cpu-only --src-fwk gluon --dst-fwk pytorch`.

**Status:** blocked/unverified by policy. The focused Gluon/PyTorch examples
create `mx.gpu(0)`, move the PyTorch model and input with `.cuda()`, and compare
outputs. They do not prove CPU behavior.

**Checklist before reconsideration:**

1. Confirm the intended model names exist on both endpoints and that the
   architecture, class count, input channels, and parameter shapes match.
2. Confirm a local Gluon `.params` file and writable destination `.pth` path;
   do not substitute a pretrained auto-loader.
3. Confirm compatible MXNet and PyTorch/CUDA backends through the framework
   compatibility route.
4. Obtain explicit approval for a short CPU smoke test separate from the
   GPU-backed evidence. Until then, report this as blocked optional, not passed.

The main conversion script currently sets `use_cuda=False`; that is an
implementation detail, not a CPU test result and not an override of this gate.

## PyTorch flags and checkpoint loading

**Symptom:** a PyTorch checkpoint fails to load or has unexpected keys.

**Repair:** `--src-params` must be accepted by `torch.load`. The loader unwraps
a top-level `state_dict` dictionary. `--load-ignore-extra` filters stored keys
to keys present in the destination model and then loads them; it is not a
shape conversion and does not make a different architecture safe.

`--remove-module` is used only when `--load-ignore-extra` is false. It loads a
stored DataParallel-style `module.` wrapper through a temporary
`torch.nn.DataParallel` model and then transfers the unwrapped state. If both
flags are passed, the ignore-extra branch wins and the remove-module branch is
not used. Both flags are accepted by the real parser for every edge;
`--load-ignore-extra` also reaches the Gluon source loader, while
`--remove-module` remains PyTorch-only.

## Missing or wrong source checkpoint

**Symptom:** `FileNotFoundError`, an assertion from a model loader, or an
unexpected empty parameter map.

**Repair by source:**

- `gluon`: `--src-params` must be an existing Gluon parameter file.
- `mxnet`: `--src-params` must be the prefix resolving to the epoch-0 symbol
  and parameter files consumed by `mx.model.load_checkpoint`; do not pass an
  invented destination extension.
- `pytorch`: `--src-params` must be readable by `torch.load`; review the
  `state_dict`, `--remove-module`, and `--load-ignore-extra` rules above.
- `tensorflow`: `--src-params` must be a NumPy archive readable by `np.load`.
  This is the TF1 artifact path, not a TF2 HDF5 weights file.
- `tf2 -> tfl` through `convert_models.py`: `--src-params` is ignored. The
  branch calls `tensorflow2.utils.prepare_model` with `use_pretrained=True`
  and an empty weight path, so it may obtain pretrained weights. This is not a
  no-network local-input route.

Do not replace a missing local file with a pretrained option during a safe
plan; model providers may download weights.

## Destination path or format mismatch

**Symptom:** conversion completes partly, a destination loader rejects the
artifact, or a later load cannot find expected keys.

**Repair:** use the destination convention from the matrix and keep
`--dst-model`, class count, and input channels aligned with the source model.
The CLI does not enforce extensions. Parameter order and names are matched by
conversion-specific sorting/remapping, then shapes are asserted. Grouped or
depthwise convolutions and model-specific special cases can change the mapping;
an extension alone never proves the format.

For `gluon -> tensorflow` and `tensorflow -> tensorflow`, remember that
`tensorflow_.utils.save_model_params` stores evaluated TF1 variables in a
compressed NumPy archive. If a destination path is supplied without `.npz`,
NumPy's save helper can create a suffixed file instead of the literal path.

## Parameter key or shape assertion

**Symptom:** an assertion or error reports `src_key`, `dst_key`, `src_shape`, or
`dst_shape`, or a Gluon-to-Gluon run warns about a mismatch.

**Repair:** stop and inspect the pair instead of using a permissive flag as a
blanket fix. The conversion functions reorder keys and transpose selected
convolution/dense layouts, but they do not repair a different architecture.
Check:

- model identifiers and whether the target model exists in both endpoints;
- `--src-num-classes` versus `--dst-num-classes`;
- `--src-in-channels` versus `--dst-in-channels`;
- grouped/depthwise convolution and channel format;
- PyTorch `module.` wrappers and extra keys.

`gluon -> gluon` is the explicit fine-tuning exception: when class or channel
counts differ, it marks the run as fine-tuning and skips mismatched parameters.
Do not generalize that behavior to the other edges.

## Model type and TensorFlow generation/backend error

**Symptom:** a model build enters an unexpected branch, or `tf.Session`,
`tf.placeholder`, `tf.global_variables`, or `tf.lite.TFLiteConverter` is
missing.

**Repair:** classify the edge before installing anything:

- TF1 edges (`--src-fwk tensorflow` or `--dst-fwk tensorflow`) require the
  legacy graph/session API and the TF1 model package.
- TF2 destinations require TensorFlow 2.x/Keras model code. The code constructs
  a destination model, calls it once to create weights, and then maps weights.
- For a TF2 destination, exactly `--model-type image` selects the image input
  shape. Every other string in the source code selects the audio branch; the
  inspector conservatively accepts only `image` and `audio`.
- TF2-to-TFLite requires `tensorflow` with `tf.lite`, a model that can be
  called once, and conversion-compatible operations.
- MXNet, PyTorch, Chainer, and Keras imports are conditional on the selected
  edge, but the top-level CLI still imports `cvutil` before dispatch.

Use the framework compatibility route for optional backend installation and
model inference for model construction/load diagnostics. Do not silently
install incompatible TF1 and TF2 stacks together.

## TF2-to-TFLite local conversion

**Symptom:** conversion starts a weight download, `--src-params` appears to be
ignored, or the interpreter cannot allocate tensors.

**Repair:** use a separately prepared local-input TF2-to-TFLite wrapper, not
the CLI branch. This runtime skill's inspector does not perform export:

```text
--model MODEL --input ./model.tf2.h5 --output-dir ./tflite-out
```

The local-input contract is `--model`, optional `--input`, optional
`--input-shape`, and optional `--output-dir`; it does not accept the
`convert_models.py` flags `--src-params` or `--dst-params`. With `--input`, a
proper wrapper should load local weights, call the model, convert with
`tf.lite.TFLiteConverter.from_keras_model`, write `<output-dir>/<model>.tflite`
only when the directory exists, allocate an interpreter, invoke random input,
and compare TensorFlow and TFLite results.

In this snapshot, `--input-shape` is declared as `type=int` without `nargs`,
while the code slices it as a sequence. Therefore custom multi-value shapes
are unverified and blocked optional: `--input-shape 224` fails later, and
`--input-shape 1 224 224 3` is rejected by argparse. The declared default is
`(1, 640, 480, 3)`; omit the flag only when that shape matches the model, or use
a separately reviewed wrapper/fix.

## Publication preparation is not a dry run

**Symptom:** the repository's publication-preparation helper fails before
conversion with missing `resume` or `train.log`, or unexpectedly starts
evaluation/data work.

**Repair:** reserve that helper for a separately approved publication workflow.
It requires `--model`, an existing local Gluon `--resume` file, and a sibling
`train.log`; it processes fixed framework targets, evaluates outputs, and
writes metadata plus result artifacts. For argument review, use the bundled
inspector instead. Do not invoke publication preparation as a smoke test.

## Verification boundary

The native conversion examples are not a safe planning check. The GPU-backed
Gluon-to-PyTorch, Gluon-to-TF1, and Gluon-to-TF2 cases are recorded as evidence
of their explicit setup and comparisons, but CPU-only variants are
unverified/blocked optional cases. Do not run long training, download weights
or datasets, or execute native conversion tests as part of this sub-skill.
