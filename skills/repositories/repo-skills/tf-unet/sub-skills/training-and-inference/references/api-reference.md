# API reference

## Public model symbols

| Symbol | Signature | Purpose | Important notes |
| --- | --- | --- | --- |
| `create_conv_net` | `create_conv_net(x, keep_prob, channels, n_class, layers=3, features_root=16, filter_size=3, pool_size=2, summaries=True)` | Build the U-Net graph and return the output map, variables, and shrinkage offset. | Uses `VALID` convolutions, so the output is smaller than the input. |
| `Unet` | `Unet(channels, n_class, cost="cross_entropy", cost_kwargs={}, **kwargs)` | Build the full model object with placeholders, cost, gradients, prediction, and accuracy nodes. | Resets the default graph during initialization. |
| `Trainer` | `Trainer(net, batch_size=1, verification_batch_size=4, norm_grads=False, optimizer="momentum", opt_kwargs={})` | Train a `Unet` instance and manage summaries, checkpoints, and predictions. | Supported optimizers are `momentum` and `adam`. |
| `error_rate` | `error_rate(predictions, labels)` | Return percent error from dense predictions and one-hot labels. | Compares `argmax(..., 3)` on the channel axis. |
| `get_image_summary` | `get_image_summary(img, idx=0)` | Build a TensorBoard-ready image summary tensor. | Expects a 4D tensor and normalizes the slice to 0-255. |

## `Unet` attributes

After construction, the model exposes these useful nodes and helpers:

- `x`: input placeholder shaped `[None, None, None, channels]`
- `y`: one-hot label placeholder shaped `[None, None, None, n_class]`
- `keep_prob`: dropout probability placeholder
- `cost`: selected loss node
- `cross_entropy`: auxiliary cross-entropy node
- `predicter`: pixel-wise softmax prediction
- `accuracy`: mean accuracy over the current batch
- `offset`: how many pixels the valid-convolution graph removes from each spatial dimension
- `variables`: trainable variables collected from the encoder and decoder blocks

## Cost-function options

`cost="cross_entropy"`

- Default path.
- Accepts `class_weights` in `cost_kwargs` for weighted multi-class loss.
- Accepts `regularizer` in `cost_kwargs` for L2 regularization.

`cost="dice_coefficient"`

- Segmentation-style loss implemented from the softmax prediction and labels.
- Useful when you want a Dice-style objective rather than cross entropy.

## `Trainer.train`

Signature:

`train(data_provider, output_path, training_iters=10, epochs=100, dropout=0.75, display_step=1, restore=False, write_graph=False, prediction_path='prediction')`

Important behavior:

- `data_provider` must be callable and return `(batch_x, batch_y)`.
- `output_path` stores the checkpoint.
- `prediction_path` stores JPEG prediction visualizations.
- If `restore` is `False`, the trainer recreates the output directories.
- `verification_batch_size` controls the test batch used for prediction snapshots.
- `write_graph=True` writes a `graph.pb` file in the output directory.

## `tf_unet.util`

| Function | Purpose | Notes |
| --- | --- | --- |
| `crop_to_shape(data, shape)` | Crop a batch tensor to a target spatial shape. | Used to align labels with prediction outputs. |
| `expand_to_shape(data, shape, border=0)` | Pad a tensor to a larger target shape. | Useful when rebuilding full-sized outputs from cropped predictions. |
| `combine_img_prediction(data, gt, pred)` | Concatenate input, ground truth, and prediction into a display image. | Expects one-hot ground truth and predictions. |
| `save_image(img, path)` | Save an RGB image as JPEG. | Used by the trainer when writing prediction snapshots. |
| `create_training_path(output_path, prefix="run_")` | Create a numbered run directory. | Helpful when you want to avoid overwriting earlier runs. |
| `to_rgb(img)` | Convert grayscale or multi-channel arrays to displayable RGB. | Normalizes values to the 0-255 range. |

## `tf_unet.layers`

These helpers are the low-level graph-building primitives:

- `weight_variable`
- `weight_variable_devonc`
- `bias_variable`
- `conv2d`
- `deconv2d`
- `max_pool`
- `crop_and_concat`
- `pixel_wise_softmax`
- `cross_entropy`

They are useful when you need to reason about the graph internals or debug a shape mismatch.
