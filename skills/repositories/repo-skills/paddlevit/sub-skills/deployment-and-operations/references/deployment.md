# Export, inference, prediction, and quantization

## Dynamic model to static/inference files

The BEiT and T2T-ViT export examples establish the common pattern, but they
must be syntax-checked before execution. In this checkout,
`image_classification/T2T_ViT/export_models.py` contains
`input_spec=[InputSpec(...), name='x']`, which is invalid Python because the
`name=` keyword is outside the `InputSpec` call. Treat that file as
reference-only until locally corrected to `InputSpec(..., name='x')` (or to an
unnamed `InputSpec`); do not claim that the checked-in script ran.

1. Resolve the model's own config and builder from its standalone directory.
2. Build the dynamic Paddle model and load a compatible `.pdparams` state
   dict. Training checkpoints may be wrapped in `model`; BEiT prefers
   `model_ema` when present, otherwise `model`. Confirm the wrapper policy for
   the selected family before loading.
3. Call `model.eval()`; do not export a training-mode graph.
4. Construct an `InputSpec` for dynamic batch and the model's configured NCHW
   shape, usually `[None, channels, image_size, image_size]` and `float32`.
   If the model accepts a different shape or named input, use the model's own
   contract.
5. Optionally apply the documented static `BuildStrategy` optimizations
   (`enable_inplace`, `memory_optimize`, reduction/fusion settings) one at a
   time when debugging. An optimization failure is an export compatibility
   issue, not evidence of a bad checkpoint.
6. Call `paddle.jit.to_static(model, input_spec=..., build_strategy=...)` and
   `paddle.jit.save(model, output_prefix)`.

`output_prefix` is a path stem, not a filename with `.pdmodel` appended. A
successful export is expected to produce exactly this core set:

```text
<output_prefix>.pdmodel
<output_prefix>.pdiparams
<output_prefix>.pdiparams.info
```

The BEiT example writes prefixes such as `./beit_base_patch16_224`. The T2T
example writes `t2t_vit_7_static/inference`, resulting in
`inference.pdmodel`, `inference.pdiparams`, and `inference.pdiparams.info` in
that directory. Validate the set with `scripts/validate_checkpoint_manifest.py`
before handing it to inference. Do not rename one member or mix members from
different exports.

Export is model-family-specific despite the shared pattern. Dynamic shape
access in `reshape`/`flatten`/`transpose`, multiple unknown dimensions, or
functional operations in `forward` can prevent conversion. The source docs
suggest replacing Python shape reads with Paddle shape operations, avoiding
multiple `-1` dimensions, and moving suitable functional operations into
`paddle.nn` layers. Apply such code changes only in the owning model and test
them separately; do not hide the failure by claiming an export exists.

## Paddle Inference execution

The BEiT inference example uses:

```python
config = paddle_infer.Config("<prefix>.pdmodel", "<prefix>.pdiparams")
predictor = paddle_infer.create_predictor(config)
input_name = predictor.get_input_names()[0]
handle = predictor.get_input_handle(input_name)
handle.reshape([batch, channels, height, width])
handle.copy_from_cpu(float32_nchw_batch)
predictor.run()
output_name = predictor.get_output_names()[0]
out = predictor.get_output_handle(output_name).copy_to_cpu()
```

For a real image, the example uses RGB conversion, resize, `ToTensor`, and
normalization with model-appropriate mean/std. The repository's representative
ViT defaults use `CROP_PCT=0.875` and mean/std `[0.5, 0.5, 0.5]`, while another
model may define different values. Match the original validation transform:
resize policy, crop size, interpolation, RGB/channel order, tensor layout,
scale/range, mean, and standard deviation. The inference API accepts NumPy
arrays; convert Paddle tensors with `.numpy()` before `copy_from_cpu`.

A random `float32` tensor is a useful predictor wiring smoke only. It cannot
validate accuracy, class labels, preprocessing, or checkpoint correctness.
For parity, run the same deterministic batch through the dynamic model and
exported predictor, compare shape/dtype first, then compare values with a
stated tolerance. Static optimization, provider/device choice, and numerical
precision can change the tolerance requirement.

## Custom prediction boundary

The available prediction documentation is a customization recipe rather than
a universal `predict` command. It says to add a dataset loader, test
transforms, and a `predict` path to a model's `dataset.py` and `main_*` script.
Prediction returns per-batch softmax tensors and elapsed time without labels;
it is not validation and must not be reported as accuracy. For a new dataset:

- implement `paddle.io.Dataset.__len__` and `__getitem__`;
- use transforms that preserve the model's preprocessing contract;
- add the dataset name to that model's `get_dataset` dispatch;
- ensure the prediction dataloader does not require labels;
- decide and document ordering, output serialization, and class mapping.

Do not edit a source checkout or overwrite a checkpoint merely to prove the
prediction path. Use a copy/new branch and a synthetic input where possible.

## Quantization boundary

The PaddleSlim documentation describes offline post-training quantization of a
static model. Its example consumes a static directory and emits a different
layout, e.g. `__model__` and `__params__`, then evaluates it with a separate
script. This is optional tooling, can be version-sensitive, and needs a
representative calibration/evaluation data policy. It is not performed by the
safe probes and is not equivalent to the three `paddle.jit.save` artifacts.

Before quantization, keep an immutable manifest of the float static export,
record Paddle/PaddleSlim versions and input name, choose a new quantized output
path, and compare float versus quantized outputs on a fixed batch. Never call
an artifact quantized solely because a directory exists. Do not download
PaddleSlim or calibration data as part of diagnosis.

## Optional PyTorch/timm weight porting

Porting is an adapter task, not deployment inference:

- instantiate structurally equivalent Paddle and PyTorch models in eval mode;
- manually map every parameter and buffer name, including BatchNorm/custom
  buffers;
- account for the documented Paddle Linear weight transpose and verify whether
  other 2-D tensors must *not* be transposed;
- use a batch (not one scalar) and compare outputs with a stated `allclose`
  tolerance before `paddle.save` to `.pdparams`;
- retain a mapping manifest and source framework versions.

`torch` and `timm` are optional external dependencies and are deliberately not
required by this sub-skill. Missing packages should be reported as an optional
porting limitation, not fixed by an unapproved network install. A converted
checkpoint must still pass the selected Paddle model's load and forward smoke
before export.

## Evidence boundary

Primary evidence: `docs/paddlevit-export-en.md`,
`image_classification/BEiT/export_models.py`,
`image_classification/BEiT/infer_exported_models.py`,
`image_classification/T2T_ViT/export_models.py`,
`docs/paddlevit-predict-cn.md` (the requested English prediction file is absent
in this checkout), and `docs/paddlevit-quant-cn.md`.
