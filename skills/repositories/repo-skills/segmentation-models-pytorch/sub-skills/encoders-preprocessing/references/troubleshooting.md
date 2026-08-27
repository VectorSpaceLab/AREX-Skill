# Encoder and Preprocessing Troubleshooting

## `KeyError: Wrong encoder name`

Cause: the requested name is not in the native SMP registry and is not a valid `tu-` timm universal name.

Fix:

```python
from segmentation_models_pytorch.encoders import get_encoder_names
print(get_encoder_names()[:20])
```

- Check spelling, hyphens, underscores, and case.
- Native SMP names are lowercase registry keys such as `resnet34`, `mobilenet_v2`, `efficientnet-b0`, and `mit_b0`.
- Timm universal names must start with `tu-` and use a timm model name after the prefix.
- DPT names must start with `tu-`, but DPT uses a ViT-specific encoder path and only tested compatible names should be treated as safe.

## Wrong Pretrained Weights

Native encoder error pattern: `Wrong pretrained weights ... Available options are ...`.

Fix:

- Use one of the listed strings, often `"imagenet"`, `"ssl"`, `"swsl"`, `"advprop"`, or family-specific options.
- Use `None` for random initialization and offline-safe construction.
- Keep the preprocessing `pretrained=` string aligned with the model `encoder_weights=` string.

For `tu-` encoders:

- Do not pass `"imagenet"` as `encoder_weights`; SMP warns that `tu-` weights should be `True` or `None`.
- Put the pretrained variant in the encoder name when timm uses a tagged name, such as `tu-vit_base_patch16_224.augreg_in21k`.
- Use `encoder_weights=True` to request timm pretrained weights or `encoder_weights=None` for random initialization.

## Hugging Face Download or Fallback Errors

Native pretrained weights and native preprocessing configs try Hugging Face Hub first. For some older settings, SMP can fall back to legacy URLs or bundled preprocessing metadata; otherwise it re-raises the download/config error.

Fix:

- If downloads are not allowed, use `encoder_weights=None` and avoid constructing with pretrained native weights.
- If only preprocessing params are needed offline, resolve them once in a connected environment and store the resulting `input_space`, `input_range`, `mean`, and `std` in the model's own config.
- If a native encoder has no bundled fallback for the requested setting, do not expect `get_preprocessing_params` to work offline unless the Hugging Face config is already cached by the underlying libraries.
- For `tu-` encoders, timm owns pretrained config lookup; upgrade timm or choose a timm name with a known pretrained config if SMP says params are unavailable.

## Deprecated `timm-` Prefix Warning

Warning pattern: `` `timm-` encoders are deprecated ... use `tu-` equivalent encoders instead ``.

Fix:

- Replace equivalent `timm-regnet*`, `timm-res2*`, `timm-resnest*`, `timm-mobilenetv3*`, and `timm-gernet*` requests with `tu-...`.
- For `timm-mobilenetv3*`, use `tu-tf_mobilenetv3*` where the timm equivalent requires the `tf_` prefix.
- For ported `timm-efficientnet-*` and `timm-skres*` registry names, decide whether to stay on the native/ported registry or move to a timm universal `tu-` model by validating the exact target name.

## `tu-` Preprocessing Params Unavailable

Error pattern: `<model> does not have pretrained weights and preprocessing parameters`.

Cause: `timm.models.is_model_pretrained(model_name)` returned false for the name after removing `tu-`.

Fix:

- Choose a timm name that includes a pretrained tag when timm requires one.
- Check the installed timm version if a documented model is not recognized.
- For random initialization, skip SMP pretrained preprocessing and use dataset normalization.
- For deployment of a previously trained model, load normalization from that model's saved config instead of querying timm dynamically.

## DPT Fixed-Size or Resolution Errors

DPT ViT backbones often expect the resolution they were trained with.

Fix:

- Inspect `model.encoder.is_fixed_input_size` and `model.encoder.input_size` after construction.
- Resize or pad inputs to the trained size when fixed-size behavior is required.
- If using another resolution, pass `dynamic_img_size=True` only if the chosen timm encoder supports it.
- Avoid passing `output_stride` to DPT; its ViT encoder rejects dilated output stride.
- If the encoder has no prefix tokens, set `decoder_readout="ignore"` to avoid a warning about `cat` / `add` readout modes.

## Output Stride or Dilation Failure

Native encoders generally support default `output_stride=32`; dilated modes use `8` or `16` when supported. Some timm models do not support `output_stride` at all.

Fix:

- Use `output_stride=32` unless the architecture explicitly needs dilation.
- For DeepLabV3 and DeepLabV3+, use supported encoder output stride values from their constructors.
- For PAN, use `16` or `32` as the constructor allows.
- Validate a candidate with `check_encoder.py --output-stride 16` before building a full model around it.

## Preprocessing Function Shape Surprise

SMP's preprocessing helper expects channel-last arrays and performs normalization only.

Fix:

- Apply it before converting to channel-first PyTorch tensors, or adapt the mean/std normalization yourself for tensors.
- Do resizing, padding, augmentation, tensor conversion, batching, and dtype conversion outside `get_preprocessing_fn`.
- Check whether `input_space` is `RGB` or `BGR` before assuming channel order.
