# Keras segmentation-models API reference

## Public builders

### `Unet`

```python
Unet(
    backbone_name='vgg16',
    input_shape=(None, None, 3),
    input_tensor=None,
    encoder_weights='imagenet',
    freeze_encoder=False,
    skip_connections='default',
    decoder_block_type='upsampling',
    decoder_filters=(256, 128, 64, 32, 16),
    decoder_use_batchnorm=True,
    n_upsample_blocks=5,
    upsample_rates=(2, 2, 2, 2, 2),
    classes=1,
    activation='sigmoid',
)
```

### `Nestnet`

Same signature as `Unet`.

### `Xnet`

Same signature as `Unet`.

### `FPN`

```python
FPN(
    backbone_name='vgg16',
    input_shape=(None, None, 3),
    input_tensor=None,
    encoder_weights='imagenet',
    freeze_encoder=False,
    fpn_layers='default',
    pyramid_block_filters=256,
    segmentation_block_filters=128,
    upsample_rates=(2, 2, 2),
    last_upsample=4,
    interpolation='bilinear',
    use_batchnorm=True,
    classes=21,
    activation='softmax',
    dropout=None,
)
```

### `PSPNet`

```python
PSPNet(
    backbone_name='vgg16',
    input_shape=(384, 384, 3),
    input_tensor=None,
    encoder_weights='imagenet',
    freeze_encoder=False,
    downsample_factor=8,
    psp_conv_filters=512,
    psp_pooling_type='avg',
    use_batchnorm=True,
    dropout=None,
    final_interpolation='bilinear',
    classes=21,
    activation='softmax',
)
```

## Helpers

### `get_backbone(name, *args, **kwargs)`

Returns the selected classification backbone constructor result.

### `get_preprocessing(backbone)`

Returns the matching preprocessing function for the selected backbone.

### `freeze_model(model)`

Marks every layer trainable flag as `False`.

### `set_trainable(model)`

Marks every layer trainable flag as `True` and recompiles the model.

### `extract_outputs(model, layers, include_top=False)`

Returns intermediate outputs from named or indexed layers.

## Practical usage pattern

1. Choose `backbone_name`.
2. Decide whether you need pretrained weights (`encoder_weights='imagenet'`) or
   a safe structural smoke (`encoder_weights=None`).
3. Use `get_preprocessing(backbone)` if you are preparing raw images.
4. Confirm the input shape obeys the chosen backbone and head constraints.
5. Build the model before considering training or BRATS2013 workflows.

## Shape and weight warnings

- `include_top=True` can change the allowed weight variants.
- `PSPNet` is the strictest architecture in this snapshot because it checks the
  input shape before building.
- The original helper code in `keras/helper_functions.py` is useful evidence for
  older custom losses and metrics, but the runtime skill should prefer the public
  builders above.
