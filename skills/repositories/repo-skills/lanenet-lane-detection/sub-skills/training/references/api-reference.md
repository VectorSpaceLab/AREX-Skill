# LaneNet Training API Reference

This reference captures the source APIs that matter for training. Use it to reason about backbone choice, trainer behavior, loss outputs, and config-owned knobs.

## LaneNet model entry points

| Object | Signature | Notes |
| --- | --- | --- |
| `lanenet_model.lanenet.LaneNet.__init__` | `(self, phase, cfg)` | Use `phase='train'` for training and `phase='test'` for inference. The front-end is selected by `cfg.MODEL.FRONT_END`. |
| `LaneNet.inference` | `(self, input_tensor, name, reuse=False)` | Returns `(binary_seg_prediction, instance_seg_prediction)`. In the training graph this is reused to expose the binary prediction tensor for mIoU summaries. |
| `LaneNet.compute_loss` | `(self, input_tensor, binary_label, instance_label, name, reuse=False)` | Returns the loss dictionary used by the trainers. |

Expected training input tensor shape:

```python
input_tensor = tf.placeholder(dtype=tf.float32, shape=[batch_size, 256, 512, 3], name='input_tensor')
```

## Front-end dispatch

| `MODEL.FRONT_END` value | Implementation | Notes |
| --- | --- | --- |
| `bisenetv2` | `semantic_segmentation_zoo.bisenet_v2.BiseNetV2` | Default front end in the shipped config. |
| `vgg` | `semantic_segmentation_zoo.vgg16_based_fcn.VGG16FCN` | Supported by the front-end map. Use only with matching checkpoint expectations. |

Both front ends return a dictionary with the same keys that LaneNet expects:

| Key | Meaning |
| --- | --- |
| `binary_segment_logits` | Binary lane/non-lane logits consumed by the backend. |
| `instance_segment_logits` | Instance branch feature map consumed by the backend. |

## Trainer entry points

| Object | Signature | Notes |
| --- | --- | --- |
| `trainner.tusimple_lanenet_single_gpu_trainner.LaneNetTusimpleTrainer` | `(self, cfg)` | Builds a single-GPU training graph and uses the train TFRecord set only. |
| `trainner.tusimple_lanenet_multi_gpu_trainner.LaneNetTusimpleMultiTrainer` | `(self, cfg)` | Builds multi-tower training plus validation graph and uses both train and val TFRecord sets. |

The trainers read these config values directly:

| Config key | Default | Role |
| --- | --- | --- |
| `MODEL.FRONT_END` | `bisenetv2` | Backbone selector. |
| `MODEL.EMBEDDING_FEATS_DIMS` | `4` | Instance embedding channels. Must match the checkpoint. |
| `TRAIN.MODEL_SAVE_DIR` | `model/tusimple/` | Root directory for saved checkpoints. |
| `TRAIN.TBOARD_SAVE_DIR` | `tboard/tusimple/` | Root directory for TensorBoard logs. |
| `TRAIN.MODEL_PARAMS_CONFIG_FILE_NAME` | `model_train_config.json` | JSON copy of the effective config saved to TensorBoard dir. |
| `TRAIN.RESTORE_FROM_SNAPSHOT.ENABLE` | `False` | Enables restore. |
| `TRAIN.RESTORE_FROM_SNAPSHOT.SNAPSHOT_PATH` | `''` | Snapshot base path to restore. |
| `TRAIN.SNAPSHOT_EPOCH` | `8` | Snapshot interval in epochs. |
| `TRAIN.BATCH_SIZE` | `32` | Total training batch size. |
| `TRAIN.VAL_BATCH_SIZE` | `4` | Validation batch size for the multi-GPU trainer. |
| `TRAIN.EPOCH_NUMS` | `905` | Training epochs. |
| `TRAIN.WARM_UP.ENABLE` | `True` | Enables warm-up learning rate. |
| `TRAIN.WARM_UP.EPOCH_NUMS` | `8` | Warm-up duration. |
| `TRAIN.FREEZE_BN.ENABLE` | `False` | Excludes BN gamma/beta from trainable vars when enabled. |
| `TRAIN.COMPUTE_MIOU.ENABLE` | `True` | Enables mIoU summaries. |
| `TRAIN.COMPUTE_MIOU.EPOCH` | `1` | Record mIoU every N epochs. |
| `TRAIN.MULTI_GPU.ENABLE` | `True` | Chooses the multi-GPU trainer when true. |
| `TRAIN.MULTI_GPU.GPU_DEVICES` | `['0', '1']` | Logical GPU device list used by the multi-GPU trainer. |
| `TRAIN.MULTI_GPU.CHIEF_DEVICE_INDEX` | `0` | Tower index used for the main summaries. |
| `SOLVER.LR` | `0.001` | Initial learning rate. |
| `SOLVER.LR_POLICY` | `poly` | Policy used by the trainer. |
| `SOLVER.LR_POLYNOMIAL_POWER` | `0.9` | Poly decay power. |
| `SOLVER.OPTIMIZER` | `sgd` | Default optimizer. The README notes SGD is more stable than Adam. |
| `SOLVER.MOMENTUM` | `0.9` | Momentum for SGD. |
| `SOLVER.WEIGHT_DECAY` | `0.0005` | L2 regularization strength. |
| `SOLVER.MOVING_AVE_DECAY` | `0.9995` | Exponential moving average decay. |
| `SOLVER.LOSS_TYPE` | `cross_entropy` | Binary loss type. |
| `GPU.GPU_MEMORY_FRACTION` | `0.9` | TensorFlow session memory fraction. |
| `GPU.TF_ALLOW_GROWTH` | `True` | Allow memory growth. |

## Loss dictionary returned by `LaneNetBackEnd.compute_loss`

| Key | Meaning |
| --- | --- |
| `total_loss` | Binary loss + discriminative loss + L2 regularization. |
| `binary_seg_loss` | Class-weighted binary lane segmentation loss. |
| `discriminative_loss` | Instance-segmentation discriminative loss. |
| `instance_seg_logits` | Pixel embedding tensor after the 1x1 embedding convolution. |
| `binary_seg_logits` | Binary logits passed through the backend. |

## Backend inference behavior

`LaneNetBackEnd.inference(...)` returns:

| Output | Meaning |
| --- | --- |
| `binary_seg_prediction` | Argmax over softmaxed binary logits. |
| `instance_seg_prediction` | Embedding tensor after batch norm, ReLU, and 1x1 embedding convolution. |

The training graph wraps the binary prediction with `tf.identity(..., name='binary_segmentation_result')` before computing mIoU summaries.

## Discriminative-loss constants

The backend calls `lanenet_discriminative_loss.discriminative_loss(...)` with fixed parameters:

| Parameter | Value |
| --- | --- |
| `delta_v` | `0.5` |
| `delta_d` | `3.0` |
| `param_var` | `1.0` |
| `param_dist` | `1.0` |
| `param_reg` | `0.001` |

The helper returns the total discriminative loss plus its variance, distance, and regularization components. The backend adds the binary loss and L2 regularization to form `total_loss`.

## Warm-up and decay note

Both trainers use warm-up when enabled, starting at roughly `LR / 1000`. After warm-up, a poly decay schedule takes over. The single-GPU trainer decays toward `1e-6`; the multi-GPU trainer decays toward `1e-9`.
