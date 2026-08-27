# Facenet model definitions

Facenet training scripts dynamically import a model definition module from `src/models/`.

## Shared `inference(...)` contract

Each model module exports:

```python
inference(images, keep_probability, phase_train=True, bottleneck_layer_size=128, weight_decay=0.0, reuse=None)
```

The function returns a tuple `(prelogits, end_points)` or `(bottleneck, None)` for the dummy model.

## `inception_resnet_v1`

- The main FaceNet architecture used in the README pretrained models.
- Uses `tensorflow.contrib.slim` layers.
- Suitable default for most FaceNet workflows.

## `inception_resnet_v2`

- A related Inception-ResNet architecture with similar parameters.
- Useful when the user explicitly asks for an alternative model definition or compatibility comparison.

## `squeezenet`

- A lightweight alternative architecture.
- Often used in tests and smaller training runs.

## `dummy`

- A simplified fully connected bottleneck model used only by tests.
- Not a real face-recognition model.

## Choosing `embedding_size`

The training scripts set `bottleneck_layer_size` on the model definition and then normalize the resulting prelogits into `embeddings:0`. `embedding_size` should match downstream expectations when freezing, comparing, or validating with pretrained checkpoints.
