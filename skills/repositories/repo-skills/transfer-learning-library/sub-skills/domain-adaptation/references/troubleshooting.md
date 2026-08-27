# Troubleshooting

Use this file when the user reports a shape error, import failure, optional dependency issue, or benchmark-environment mismatch.

## Feature / logit shape mismatches

The most common errors are caused by mixing up features, logits, probabilities, or label tensors.

### DANN / ADDA

- `DomainDiscriminator` expects 2-D feature tensors shaped `(N, F)`.
- DANN/CDAN adversarial discriminators usually expect probability outputs with `sigmoid=True`.
- If you see a `mat1 and mat2 shapes cannot be multiplied` error, the discriminator input size usually does not match the feature dimension you passed.

### CDAN

- Pass raw logits shaped `(N, C)` plus features shaped `(N, F)`.
- Do not pass class indices.
- If `randomized=True`, make sure `num_classes`, `features_dim`, and `randomized_dim` are all positive and consistent with the discriminator input.

### DAN / JAN / CORAL / BSP

- These families use feature tensors, not labels.
- Keep the source and target feature dimension identical.
- MK-MMD / JMMD recipes typically assume matching mini-batch sizes in the example flows.
- CORAL and covariance-style losses need at least two samples per batch.

### MCD

- The discrepancy helpers consume probability-like predictions, not class indices.
- If you see a shape issue, check whether you accidentally passed features or hard labels into `classifier_discrepancy`.

### MDD

- The main and adversarial heads must produce `(N, C)` logits.
- `mdd.ImageClassifier` returns `(outputs, outputs_adv)` in training mode and only `outputs` in eval mode.
- Remember to call `step()` after each training forward; otherwise the warm-start GRL schedule will not advance.

### OSBP

- `UnknownClassBinaryCrossEntropy` expects logits with an extra unknown-class slot: `(N, C+1)`.
- If the last column is missing, the open-set boundary cannot be learned.

### Partial-DA weighting

- `ClassWeightModule` expects logits shaped `(N, C)`.
- `ImportanceWeightModule` expects discriminator scores on source features, not labels.
- The debugging-only `partial_classes_index` helpers are not a replacement for real target supervision.

### RegDA heatmaps

- `RegressionDisparity` and `JointsKLLoss` expect heatmaps shaped `(B, K, H, W)`.
- If the heatmap generator produces the wrong spatial size, the criterion will fail even though the backbone is fine.

## NumPy alias compatibility

Older TLLib code still uses aliases such as `np.int`, `np.float`, and `np.long` in some helper paths.

- If you see `AttributeError: module 'numpy' has no attribute ...`, you are likely running with a modern NumPy release that removed those aliases.
- The clean fix is to use a compatible NumPy version for the environment that runs the legacy helper.
- The fallback fix is to use a shimmed environment or a newer helper path when one exists.
- Treat this as an environment compatibility issue, not as a failure of the DA algorithm itself.

## TorchVision / older TLLib compatibility

This repository was verified with an older PyTorch / TorchVision stack.
Modern TorchVision releases can break older model imports because of changes such as removed `model_urls` helpers or missing `torchvision.models.utils` symbols.

- If a vision import fails after a TorchVision upgrade, pin to the verified stack rather than assuming the DA logic is broken.
- Keep the smoke helper on the installed `tllib` package only; do not add source-checkout paths to `PYTHONPATH`.
- If the user insists on a newer stack, explain that the result is a compatibility port, not the verified baseline.

## CUDA, downloads, and training limits

Benchmark launchers often assume:

- CUDA is available,
- the datasets can be downloaded or prepared manually,
- training will run for many epochs,
- logs and checkpoints can be written freely.

If any of those assumptions are false, keep the guidance at the workflow-reference level and do not claim benchmark reproduction.
The bundled smoke helper is CPU-only and exists only to validate API wiring.

## Detectron2 and WILDS optional stacks

### Detectron2 object detection

- D-adapt needs a Detectron2-compatible runtime plus the expected detection extras.
- If Detectron2 or the CUDA wheels are missing, keep the object-detection branch as reference-only guidance.

### WILDS

- WILDS branches may additionally need `wilds`, `apex`, `transformers`, `torch_sparse`, `torch_geometric`, `ogb`, or `tensorflow` depending on the modality.
- Missing optional packages should not be reported as failures of the core DA skill.
- If the user asks for a benchmark recipe that depends on these stacks, clearly state the optional dependency boundary.
