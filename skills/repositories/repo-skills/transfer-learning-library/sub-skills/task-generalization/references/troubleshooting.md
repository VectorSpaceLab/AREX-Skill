# Troubleshooting: Task Generalization

This file covers common failures in TLLib domain-generalization and task-adaptation workflows.

## Train/eval mode mistakes

| Symptom | Check | Fix |
| --- | --- | --- |
| MixStyle changes validation outputs | MixStyle module is still in `train()` during validation | Call `model.eval()` for validation/test; MixStyle should be inactive in eval mode |
| MixStyle appears to do nothing in training | Module is in `eval()` or `p` is too low | Call `model.train()`, confirm feature tensor is 4D, and log `p`/`alpha` |
| Co-Tuning/LwF classifier returns one tensor when training expects two | Classifier is in eval mode | Use `classifier.train()` during training; these classifiers return source and target logits only in training mode |
| BatchNorm/IBN/StochNorm statistics unstable | Very small per-domain batch size | Increase per-domain batch size, accumulate batches carefully, or freeze normalization layers only after measuring impact |
| Source reference model drifts during DELTA/L2-SP | Source model included in optimizer or left with train-time stochastic layers | Freeze source parameters and set source model to eval mode for reference features/logits |

## StochNorm conversion and CPU/GPU behavior

TLLib 0.4 StochNorm training forward creates its stochastic branch mask on CUDA. Consequences:

- CPU-only evaluation of converted StochNorm models can pass because eval mode uses running statistics.
- CPU-only training can fail with a CUDA-related error even when the rest of the model is on CPU.
- Real StochNorm training should use CUDA or a patched implementation that creates the mask on `input.device`.

Checklist:

```python
from tllib.normalization.stochnorm import StochNorm2d, convert_model

model = convert_model(model, p=0.5)
assert any(isinstance(m, StochNorm2d) for m in model.modules())
model.eval()  # CPU smoke path
```

If conversion appears ineffective:

- Confirm the original model actually used `BatchNorm1d`, `BatchNorm2d`, or `BatchNorm3d` modules.
- Convert before creating optimizer parameter groups.
- Verify no later model-loading step replaced the converted modules with fresh BatchNorm modules.
- Note that TLLib 0.4's `convert_model` preserves BatchNorm statistics but may not propagate arbitrary custom BatchNorm subclasses.

## MixStyle misuse

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Shape error | Input is not `[batch, channels, height, width]` | Insert MixStyle into convolutional feature maps, not logits or flattened features |
| No domain-generalization gain | Batch contains one domain or too few samples | Use mixed-domain mini-batches and at least two samples |
| Stochastic reproducibility issues | MixStyle uses random permutation and Beta sampling | Set Python/Torch seeds for debug; report variability across seeds |
| Inference mismatch | User expects MixStyle active at test time | Explain that MixStyle is a train-time augmentation/regularizer |

## Checkpoint and state-dict mismatches

| Error | Cause | Fix |
| --- | --- | --- |
| `Missing key(s)` for backbone layers | Checkpoint architecture does not match model or prefix not mapped | Inspect keys, use matching backbone, strip known prefixes such as `module.` or `module.encoder_q.` deliberately |
| `Unexpected key(s): fc.*` | Loading a classifier head into a backbone-only model | Split or drop `fc.*` keys, or load into the correct head module |
| `size mismatch for fc.weight` | Source and target class counts differ | Initialize target head; do not force-load incompatible source FC |
| `Module layerX not found` in `IntermediateLayerGetter` | DELTA layer name not valid for this model | Print model children and choose existing layers that match source/target models |
| Feature-map shape mismatch in DELTA | Source and target layer selections differ or model variants differ | Use corresponding layers and matching input transforms |
| Source logits cache shape mismatch in LwF | Dataset order, sample count, or source class count changed | Regenerate logits with the current dataset order and source classifier |

See [checkpoint conversion](checkpoint-conversion.md) for MoCo-style conversion before task adaptation.

## Pretrained download requirements

- IBN factories with `pretrained=True` download external IBN checkpoints.
- Standard model factories may download ImageNet-style weights depending on the factory and arguments.
- MoCo checkpoints are external user-provided artifacts and must be converted before some workflows.
- Offline or air-gapped runs should use `pretrained=False` for smoke checks and explicit local checkpoint paths for experiments.

Do not let a runtime helper silently download large pretrained checkpoints. Ask the user for explicit approval and paths.

## Negative transfer from regularizer misuse

| Symptom | Likely regularizer issue | Fix |
| --- | --- | --- |
| Target accuracy below ERM and source-like predictions persist | L2-SP or DELTA trade-off too high | Lower trade-off; exclude target head from SP; warm up with CE |
| Features collapse or singular-value penalty dominates | BSS `k` or trade-off too high | Start with `k=1` and small trade-off; log BSS penalty separately |
| Co-Tuning worsens performance | Relationship matrix noisy or target labels misindexed | Recompute relationship; verify rows correspond to target classes and columns to source classes |
| LwF loss unstable | Saved source logits not aligned with current samples | Regenerate logits with deterministic ordering; store sample IDs with logits when possible |
| IRM/VREx underfits every domain | Penalty annealed too early or too strong | Increase warmup, lower trade-off, and validate per-domain CE losses |
| GroupDRO focuses on one domain only | `eta` too high or domain losses on different scales | Lower `eta`, normalize losses consistently, and log domain weights |

Always compare against ERM fine-tuning before attributing improvements or regressions to a regularizer.

## GPU, data, and optional dependency needs

- CPU component checks verify imports, tensor shapes, and finite losses only.
- Full DG/task-adaptation training usually requires CUDA, image datasets, log/checkpoint storage, and enough time for benchmark-scale loops.
- Many image-classification benchmark recipes use optional model packages such as `timm`; MLDG-style inner-loop workflows may need optional differentiable-optimization tooling.
- Re-identification DG and large fine-grained datasets are not covered by tiny CPU smoke checks.
- Dataset preparation, image-list formats, transforms, and model factory choices belong in [vision-data-models](../../vision-data-models/SKILL.md).

## Legacy package compatibility

TLLib 0.4 was developed against older PyTorch/TorchVision APIs. If imports fail in a modern environment:

- Prefer a Python/PyTorch/TorchVision stack close to the package era for verification.
- Modern TorchVision releases removed or moved some symbols used by older TLLib model code.
- NumPy versions that removed deprecated aliases can break old scientific code paths.
- Treat optional CUDA/Detectron2/WILDS/timm issues as workflow-specific unless the user needs that exact backend.

## Smoke script failures

Run the smoke script from an environment where `tllib` is installed:

```bash
python path/to/tllib_task_generalization_smoke.py --verbose
```

If it fails:

1. Confirm `python -c "import tllib"` works in the same environment.
2. Confirm PyTorch imports and can allocate CPU tensors.
3. Read the failing check name in the JSON/error output.
4. If only StochNorm training is failing on CPU, use eval-mode smoke or switch to CUDA for real StochNorm training.
5. If CORAL or GroupDRO fails, verify tensor shapes and domain indices before attempting benchmark training.
