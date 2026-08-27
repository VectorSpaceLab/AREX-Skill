# Deployment And Sharing

## Local Save And Load

Use `model.save_pretrained(save_directory)` after training or fine-tuning. SMP writes the model configuration, model weights, and a model card into the target directory. Use `smp.from_pretrained(save_directory)` to reconstruct the saved architecture and restore weights.

```python
import segmentation_models_pytorch as smp

model = smp.Unet("resnet34", encoder_weights=None, classes=2)
model.save_pretrained("leaf-segmentation-unet")
restored = smp.from_pretrained("leaf-segmentation-unet")
restored.eval()
```

For smoke tests and examples, set `encoder_weights=None` so the code does not attempt to download pretrained encoder weights. For real trained checkpoints, preserve the constructor choices used at training time unless intentionally overriding them at load time.

## Model Card Metadata

`save_pretrained` accepts `dataset` and `metrics`; SMP forwards them into the generated model card.

```python
model.save_pretrained(
    "leaf-segmentation-unet",
    dataset="leaf-segmentation-v1",
    metrics={"miou": 0.91, "dice": 0.94},
)
```

Use metadata to document the training dataset and headline metrics, but keep private data paths, credentials, and machine-specific details out of the model card.

## Hugging Face Hub Flow

The same API can push to the Hugging Face Hub when credentials and network access are available:

```python
model.save_pretrained(
    "username/leaf-segmentation-unet",
    push_to_hub=True,
    private=True,
    dataset="leaf-segmentation-v1",
    metrics={"miou": 0.91},
)

restored = smp.from_pretrained("username/leaf-segmentation-unet")
```

Use local directories for offline or CI checks. Use a Hub repo id such as `username/model-name` only when the environment has `huggingface-hub`, an authenticated token for writes/private reads, and permitted network access.

## Loading With A Different Class Count

Use `strict=False` when reusing a saved checkpoint with a different output head, usually for fine-tuning on a new dataset with a different number of classes.

```python
model = smp.from_pretrained("leaf-segmentation-unet", classes=5, strict=False)
```

SMP filters mismatched tensors before calling PyTorch `load_state_dict`. For class-count changes, expect the segmentation-head weight and bias to be reinitialized for the new class count while compatible encoder/decoder weights are restored. The warning is intentional: train the new head before relying on predictions.

## Preprocessing Transform Sharing

SMP saves the model, not the entire inference pipeline. If the deployment pipeline needs a resize/normalize transform, save that transform separately with a tool that supports `save_pretrained`, such as Albumentations.

```python
import albumentations as A

preprocessing = A.Compose([A.Resize(256, 256), A.Normalize()])
preprocessing.save_pretrained("username/leaf-segmentation-unet", push_to_hub=True)
restored_preprocessing = A.Compose.from_pretrained("username/leaf-segmentation-unet")
```

Keep training augmentations separate from deterministic inference preprocessing. If saving multiple transforms, use distinct keys supported by the transform library.

## Conversion Scripts Are Maintainer Utilities

The repository includes checkpoint-conversion scripts for DPT, SegFormer, and UPerNet source checkpoints. Treat those as reference material for maintainers or checkpoint publishers, not as the normal user flow. For ordinary trained SMP models, prefer `save_pretrained`, `smp.from_pretrained`, and deployment export checks.
