# Model selection and construction overview

## Shared tensor and mode contract

DLTK's complete 3D networks consume channel-last rank-5 tensors:

```text
[batch, x, y, z, channels]
```

The spatial axis names are generic array axes; they do not imply a particular medical-image orientation. Keep orientation, resampling, and channel stacking decisions in the data pipeline. Sparse segmentation labels normally omit the channel axis and therefore have `[B, X, Y, Z]`.

Pass one of `tf.estimator.ModeKeys.TRAIN`, `EVAL`, or `PREDICT` to `mode`. DLTK's `tf.layers.batch_normalization` calls use `training=(mode == TRAIN)`, so:

- `TRAIN` constructs moving-statistic update ops. The surrounding optimizer step must depend on `tf.get_collection(tf.GraphKeys.UPDATE_OPS)`.
- `EVAL` and `PREDICT` read moving statistics rather than current-batch statistics.
- The network builders return tensors only. They do not create a `tf.estimator.EstimatorSpec`, optimizer, checkpoint, or export receiver.

Use [training-and-estimators](../../training-and-estimators/SKILL.md) for the surrounding `model_fn` and [data-pipelines](../../data-pipelines/SKILL.md) for Reader and feature/label schemas.

## Family decision table

| Task | Builder | Core behavior | Return keys |
|---|---|---|---|
| Volume classification or scalar/vector regression | `resnet_3d` | Strided 3D residual encoder, global average pool, dense output | `logits`, `y_prob`, `y_` |
| Segmentation with concatenated skips | `residual_unet_3d` | Residual encoder/decoder; linear upsample plus channel concat | `logits`, `y_prob`, `y_` |
| Lighter asymmetric decoder | `asymmetric_residual_unet_3d` | Same encoder, one residual decoder unit at each scale | `logits`, `y_prob`, `y_` |
| Segmentation with additive skips | `residual_fcn_3d` | Residual encoder; class-filter conversion and additive upscore paths | `logits`, `y_prob`, `y_` |
| Experimental multi-path segmentation | `deepmedic_3d` | Normal and subsampled pathways, crop/upsample/concat, conv FC layers | `logits`, `y_prob`, `y_` |
| Reconstruction and latent representation | `convolutional_autoencoder_3d` | Strided encoder, dense bottleneck, transpose-convolution decoder | `hidden_units`, `x_` |
| GAN generator | `dcgan_generator_3d` | Trainable linear upsample followed by 3D convolutions and BN | `gen` |
| GAN discriminator | `dcgan_discriminator_3d` | Strided 3D convolutions, flatten, dense scalar | `logits`, `probs`, `pred` |
| Super-resolution | `simple_super_resolution_3d` | Conv feature extraction and one transpose-convolution upsampler | `x_` |

## Output semantics

For segmentation with `num_classes > 1`:

```text
logits: [B, X, Y, Z, K]
y_prob: softmax(logits), same shape
y_:     argmax(logits, axis=-1), [B, X, Y, Z]
```

For ResNet with `num_classes > 1`, the same keys have classification shapes `[B, K]`, `[B, K]`, and `[B]`. `num_classes=1` still computes `softmax` over one channel, so `y_prob` is always one; the package's `y_` branch thresholds the raw output at `0.5`. For scalar regression, consume `logits` and ignore the classification-oriented convenience outputs.

The autoencoder's `hidden_units` is `[B, num_hidden_units]`; reconstructed `x_` has the input rank and channel count. Super-resolution `x_` has each spatial dimension multiplied by `upsampling_factor`. GAN `gen` follows the cumulative generator strides; discriminator `logits`/`probs`/`pred` are `[B, 1]`.

## Filters, strides, and spatial compatibility

For ResNet, UNet, FCN, autoencoder, generator, and discriminator, every filter scale needs one spatial stride entry: `len(filters) == len(strides)`. Each stride used by these 3D operators should be a three-element `(sx, sy, sz)` sequence of positive integers.

Recommended construction sequence:

1. Start with a known static input shape and all-one strides.
2. Verify output keys and ranks with small filters such as `(2, 4)`.
3. Introduce a factor of 2 on one scale at a time.
4. Keep decoder skip dimensions exact. UNet concatenates, FCN adds; neither silently crops encoder skips.
5. Make input spatial sizes divisible by cumulative downsampling factors when using `same` downsampling followed by exact integer upsampling. Odd extents can round during stride convolutions and then fail at concat/add.
6. Keep static channel counts. Linear upsampling and residual channel handling read channels from `TensorShape` during graph construction.

`vanilla_residual_unit_3d` uses max pooling with `padding='valid'` on the residual branch for non-unit strides while the convolution branch uses `padding='same'`. Test non-unit strides on the actual spatial extent rather than assuming every odd size will align.

## Family notes

### ResNet

Choose `num_classes=1` for a scalar regression head or `K > 1` for classification. Global average pooling means the final output does not retain a spatial map. The application age-regression workflow consumes `outputs['logits']` with mean squared error; classification consumes logits with a classification loss.

### Residual UNets and FCN

All complete segmentation builders preserve the rank-5 logits contract when stride schedules are spatially compatible. The public tutorial builds a small FCN in an Estimator `model_fn` and passes the resulting dictionary as predictions. The MRBrainS application uses residual UNet and sparse cross-entropy.

UNet's decoder residual units after concatenation reduce concatenated channels to `filters[scale]`. The asymmetric version always builds one decoder residual unit per scale even though `num_res_units` still controls encoder depth. FCN converts the decoder activation to `num_classes` channels before linear upsampling and adds a class-channel projection of the skip.

### DeepMedic

The source begins with an explicit WIP warning: this implementation will not yield the same accuracy as the original DeepMedic. It center-crops a normal pathway and one or more subsampled pathways, runs mostly `VALID` convolutions, linearly upsamples subsampled paths, center-crops to the normal path, and concatenates them. Default crop and layer sequences are tightly coupled. Override all pathway filter/kernel/stride/crop sequences as one validated configuration, not independently. Its note says the original uses repeat upsampling while this implementation uses a linear/bilinear-style operation.

### Convolutional autoencoder

The encoded shape is flattened using a static product, passed through `hidden_units`, projected back, reshaped, and decoded. Every encoded spatial dimension and channel count therefore needs to be statically known at graph build time. Match stride scale count to filters and choose input extents compatible with complete downsample/upsample cycles.

### DCGAN

The generator expects a rank-5 noise tensor rather than a flat noise vector. Each scale calls trainable `linear_upsample_3d` and a 3D convolution, batch normalization, and leaky ReLU; it returns `gen` without a final tanh/sigmoid in this implementation. The discriminator returns a scalar logit and sigmoid probability per sample. Its `pred` key is `tf.cast(logits > 0.5, tf.int32)`, not `probs > 0.5`.

The repository's application uses a custom monitored-session GAN loop. Do not infer that these builders form a drop-in `tf.contrib.gan` or Estimator training solution; route orchestration to the training sub-skill.

### Simple super-resolution

The builder first extracts features with same-padded convolutions, then upsamples once using `tf.layers.conv3d_transpose`. Output channels equal input channels and output spatial extents are multiplied by the 3-element factor. The repository application creates low-resolution training input by artificial downsampling of a high-resolution source and compares `x_` against the corresponding high-resolution target. Preserve that provenance: the example demonstrates a supervised synthetic degradation setup, not recovery of arbitrary details from unknown acquisition degradation.

## Loss and metric semantics

`dice_loss` is differentiable because it applies softmax to logits. It expects sparse labels and computes spatial sums only over axes 1, 2, and 3, which matches rank-5 logits and rank-4 labels. `include_background=False` slices away class zero. `only_present=True` masks class/sample entries whose one-hot label sum is zero; otherwise only `NaN` Dice entries are removed. If all selected entries are masked, the mean may be `NaN`; validate label presence.

The NumPy `dice` metric compares integer predictions and labels class by class. If a class is absent in both arrays, its numerator and denominator are zero and the implementation yields `NaN`; report or mask absent classes explicitly. `abs_vol_difference` divides each absolute count difference by the true class count plus `1e-6`. `crossentropy` expects one-hot labels and returns the mean categorical cross-entropy.

`tests/test_activations.py` verifies the public leaky-ReLU behavior: with `alpha=0.1`, `1.0` stays `1.0` and `-1.0` becomes `-0.1` in a `tf.Session`.
