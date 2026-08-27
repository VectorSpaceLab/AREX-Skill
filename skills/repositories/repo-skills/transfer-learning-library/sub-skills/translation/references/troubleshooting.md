# Translation Troubleshooting

Use this when TLLib translation components import but a CycleGAN/FDA/CyCADA/SPGAN workflow fails. For dataset paths and model factories, route to `vision-data-models`; for downstream domain-adaptation training, route to `domain-adaptation`.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` from `tllib.translation` or `torchvision` | TLLib 0.4 expects older PyTorch/TorchVision import paths. | First run the repository-level install check. If model imports fail under modern TorchVision, use a TLLib-era stack such as Python 3.8 with older Torch/TorchVision or patch imports deliberately in the user's project. Do not debug translation math until imports are stable. |
| Generator checkpoint has many missing/unexpected keys | Factory, `ngf`, `norm`, channel count, or `DataParallel` prefix does not match the checkpoint. | Reconstruct the generator with the training-time architecture. Strip only a leading `module.` prefix if present. Keep `strict=True` until you intentionally understand every mismatch. |
| Translated output is grayscale, has wrong colors, or fails channel assertions | PIL image mode or normalization range differs from the generator expectation. | Convert inputs with `.convert('RGB')` for RGB generators. Match `mean` and `std` used during training. Remember CycleGAN generators usually output `tanh` values in `[-1, 1]` before denormalization. |
| CUDA device mismatch errors | Generator, input tensor, or `Translation(device=...)` uses different devices. | Move the generator to the same device passed to `Translation`; when validating, use CPU first. Use CUDA only after the CPU smoke and checkpoint load succeed. |
| FDA raises image-size or broadcasting errors | Source and target amplitudes have different `C x H x W` shapes. | Resize source and target images consistently before FDA. Rebuild the amplitude cache if target images or preprocessing changed. |
| FDA reuses stale target style after changing target images | Cached `.npy` amplitudes are still present. | Instantiate `FourierTransform(..., rebuild=True)` or clear the dedicated amplitude cache directory. Use a cache path specific to the target domain/preprocessing recipe. |
| `SemanticConsistency` changes labels unexpectedly | The implementation rewrites ignored labels in place before cross entropy. | Pass `labels.clone()` when labels are needed later. Make the ignore index tuple explicit, for example `ignore_index=(255,)`. |
| `CrossEntropyLoss` shape error in semantic consistency | Logits and labels do not follow `N x C x ...` versus `N x ...`. | Validate shapes before the call. For segmentation use logits `N x C x H x W` and labels `N x H x W`; for classification use `N x C` and `N`. |
| SPGAN Siamese network matrix-size error | Input image size or `nsf` changed but the fixed fully connected input size was not changed. | Use the expected re-id tensor size (`N x 3 x 256 x 128`) and default `nsf=64` for the stock implementation, or modify the network deliberately. |
| Full CycleGAN/SPGAN/FDA benchmark training is too slow or fails on data | Original benchmark workflows are data-, GPU-, and optional-dependency-heavy. | Treat full training as an explicitly authorized downstream experiment. This skill verifies component APIs and recipes, not benchmark reproduction. Prepare datasets, GPUs, logging directories, and optional packages before attempting training. |

## Minimal recovery order

1. Run `scripts/tllib_translation_smoke.py` from this sub-skill.
2. If it fails at import time, fix package/Torch/TorchVision compatibility first.
3. If it passes, isolate the user's failing component: generator, discriminator, GAN loss, FDA, semantic consistency, or SPGAN.
4. Validate tiny synthetic inputs before using real images.
5. Only then connect the component to dataset/model/training workflows in sibling sub-skills.
