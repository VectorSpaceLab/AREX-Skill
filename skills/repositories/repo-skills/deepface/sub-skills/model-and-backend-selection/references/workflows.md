# Model And Backend Workflows

## Inspect Without Building Models

```bash
python sub-skills/model-and-backend-selection/scripts/inspect_deepface_models.py --json
```

This prints installed package versions and static inventories. It does not download weights unless `--build TASK MODEL` is passed.

## TensorFlow / Keras Compatibility

If import errors mention `tf_keras`, install the compatibility package:

```bash
pip install tf-keras
```

## Optional Dependencies

Install only the optional package needed for the selected detector/database/backend. Examples include `dlib`, `mediapipe`, `ultralytics`, `facenet-pytorch`, `insightface`, `onnxruntime`, database clients, and GPU-capable framework wheels.

## Encryption Prerequisites

Encrypted embeddings require a LightPHE cryptosystem and embeddings that are non-negative and L2-normalized. For models that can produce negative raw values, use `minmax_normalize=True` and `l2_normalize=True` when appropriate.
