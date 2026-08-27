# SMP Model-Building Troubleshooting

Use this page when a `segmentation_models_pytorch` model fails during construction or a first forward pass. Keep checks small, offline, and shape-focused before moving to training, preprocessing, saving, or export workflows.

## Quick Triage

1. Verify the architecture key with `smp.MODEL_ARCHITECTURES_MAPPING.keys()` or the table in [API Reference](api-reference.md).
2. Use `encoder_weights=None` to rule out pretrained download/cache problems.
3. Create a tiny NCHW tensor whose channel count equals `in_channels`.
4. Use `model.eval()` and `torch.inference_mode()` for smoke checks.
5. Inspect whether the result is a tensor or `(mask, label)` tuple.
6. If height/width fail, pad or resize to be divisible by the encoder output stride, except where the architecture explicitly supports arbitrary sizes.

The bundled [model_smoke_test.py](../scripts/model_smoke_test.py) performs these checks and prints JSON.

## Wrong Architecture Key

Symptom:

```text
KeyError: Wrong architecture type `...`. Available options are: [...]
```

Cause: `smp.create_model` lower-cases `arch` and looks it up in `MODEL_ARCHITECTURES_MAPPING`.

Fix:

```python
model = smp.create_model("deeplabv3plus", encoder_name="resnet34", encoder_weights=None)
```

Valid keys are `unet`, `unetplusplus`, `manet`, `linknet`, `fpn`, `pspnet`, `pan`, `deeplabv3`, `deeplabv3plus`, `upernet`, `segformer`, and `dpt`. Use class constructors such as `smp.DeepLabV3Plus(...)` when you want Python attribute errors instead of config-key errors.

## Wrong Encoder Name

Symptoms vary by encoder registry and may mention an unknown encoder, unsupported encoder, missing timm model, or invalid DPT encoder prefix.

Fixes:

- Confirm the encoder exists and supports the chosen architecture in [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md).
- Start with `resnet18` or `resnet34` for non-DPT smoke tests.
- For `DPT`, use a timm ViT-style encoder with the `tu-` prefix, such as `tu-vit_tiny_patch16_224`.
- Avoid `mit_b*` encoders with `Linknet` or `UnetPlusPlus`; SMP rejects those combinations.
- For `FPN` with `mit_b*` encoders, keep `encoder_depth=5`.

## Pretrained Weight Download Or Network Failure

Symptoms may include network timeouts, authentication/cache errors, Hugging Face or timm download errors, or missing weight files.

Cause: many examples and defaults use `encoder_weights="imagenet"`; `smp.create_model` also defaults to `encoder_weights="imagenet"` if you omit the argument.

Fix:

```python
model = smp.create_model(
    arch="unet",
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=3,
    classes=1,
)
```

Only use a named pretrained weight set after the runtime environment has the required cache/network access and the preprocessing contract has been handled by [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md).

## Wrong Input Channel Count

Symptom:

```text
RuntimeError: Given groups=1, weight of size ..., expected input[...] to have 3 channels, but got 1 channels instead
```

Cause: `in_channels` was not set to match `x.shape[1]`.

Fix:

```python
model = smp.Unet("resnet34", encoder_weights=None, in_channels=1, classes=1)
x = torch.zeros(1, 1, 64, 64)
mask = model.eval()(x)
```

If using pretrained weights, SMP can adapt first-layer weights for different `in_channels`, but this still does not replace correct preprocessing or a smoke test.

## Wrong Class Count

Symptoms:

- The model output has unexpected channel count.
- Loss functions complain about logits/target class shape mismatch.
- Binary segmentation returns more than one mask channel or multiclass segmentation returns only one.

Cause: `classes` controls segmentation mask channels, not dataset labels by itself.

Fix:

```python
model = smp.FPN("resnet34", encoder_weights=None, in_channels=3, classes=7)
mask = model(torch.zeros(2, 3, 64, 64))
assert tuple(mask.shape[:2]) == (2, 7)
```

Route loss-mode and target-shape decisions to [Training And Evaluation](../../training-evaluation/SKILL.md).

## Aux Output Tuple Unpacking

Symptom:

```text
AttributeError: 'tuple' object has no attribute 'shape'
```

or downstream code receives a tuple where it expected a tensor.

Cause: passing `aux_params` creates a classification head, so forward returns `(mask, label)`.

Fix:

```python
aux_params = {"pooling": "avg", "dropout": 0.5, "activation": "sigmoid", "classes": 4}
model = smp.Unet("resnet18", encoder_weights=None, classes=2, aux_params=aux_params)
mask, label = model(torch.zeros(1, 3, 64, 64))
assert tuple(mask.shape) == (1, 2, 64, 64)
assert tuple(label.shape) == (1, 4)
```

Remember: `classes` controls mask channels; `aux_params["classes"]` controls label channels.

## Spatial Shape Divisibility

Symptom:

```text
RuntimeError: Wrong input shape height=..., width=.... Expected image height and width divisible by ...
```

Cause: SMP's base `SegmentationModel.check_input_shape` checks divisibility by `model.encoder.output_stride` for architectures that require it. `Unet` is the main exception in SMP because it sets `requires_divisible_input_shape=False`.

Fixes:

- Use a height and width divisible by the model's output stride, commonly `32` for standard encoders.
- Pad or resize images before the model, then crop masks back if needed.
- Inspect `model.encoder.output_stride` and `model.requires_divisible_input_shape` during debugging.

```python
model = smp.FPN("resnet18", encoder_weights=None).eval()
print(model.requires_divisible_input_shape, model.encoder.output_stride)
x = torch.zeros(1, 3, 64, 64)
mask = model(x)
```

## DPT Fixed Or Dynamic Image Size

Symptoms:

- DPT construction fails because the encoder does not start with `tu-`.
- DPT forward fails on a size different from the ViT encoder's expected training size.
- Timm encoder messages mention fixed image size, patch size, or positional embedding mismatch.

Fixes:

```python
model = smp.DPT(
    encoder_name="tu-vit_tiny_patch16_224",
    encoder_weights=None,
    classes=1,
)
x = torch.zeros(1, 3, 224, 224)
mask = model.eval()(x)
```

When the specific timm encoder supports it, pass `dynamic_img_size=True`:

```python
model = smp.create_model(
    arch="dpt",
    encoder_name="tu-vit_tiny_patch16_224",
    encoder_weights=None,
    classes=1,
    dynamic_img_size=True,
)
```

For a bundled smoke test, use:

```bash
python sub-skills/model-building/scripts/model_smoke_test.py --arch dpt --encoder tu-vit_tiny_patch16_224 --height 224 --width 224
```

## Architecture-Specific Value Errors

Common validated parameter errors:

| Architecture | Error cause | Fix |
| --- | --- | --- |
| `pan` | `encoder_output_stride` is not `16` or `32`. | Use `encoder_output_stride=16` or `32`. |
| `deeplabv3` | `encoder_output_stride` is not `8` or `16`. | Use `encoder_output_stride=8` or `16`. |
| `deeplabv3plus` | `encoder_output_stride` is not `8` or `16`, or unsupported depth. | Use output stride `8` or `16`; use depth `3`, `4`, or `5`. |
| `dpt` | Encoder name lacks `tu-` prefix or `decoder_readout` is not `ignore`, `add`, or `cat`. | Use a timm encoder with `tu-` prefix and a supported readout mode. |
| `fpn` | `mit_b*` encoder uses depth other than `5`. | Keep `encoder_depth=5` or choose another encoder. |
| `linknet` / `unetplusplus` | `mit_b*` encoder is selected. | Choose a supported encoder or a different architecture. |

## Smoke-Test Before Training Or Export

Run a shape-only check first:

```bash
python sub-skills/model-building/scripts/model_smoke_test.py --arch unet --encoder resnet18 --in-channels 1 --classes 1 --height 64 --width 64
```

Run an aux-output check:

```bash
python sub-skills/model-building/scripts/model_smoke_test.py --arch unet --encoder resnet18 --classes 2 --aux --aux-classes 4
```

If these pass but training fails, route to [Training And Evaluation](../../training-evaluation/SKILL.md). If saving, loading, tracing, or exporting fails, route to [Model Export](../../model-export/SKILL.md).
