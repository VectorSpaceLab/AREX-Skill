# Troubleshooting Feature Evaluation

## CUDA Out of Memory

Symptoms: extraction crashes with CUDA OOM, the process is killed, or throughput collapses after a few batches.

- Lower `--batch-size`; ViT-L/14 and 336px checkpoints need more memory than ViT-B/32.
- Use `--device cpu` for small offline jobs when GPU memory is constrained.
- Ensure extraction uses `torch.no_grad()` or `torch.inference_mode()` and `model.eval()`.
- Move features to CPU after each batch and avoid keeping image tensors on GPU.
- Close other GPU processes or use a smaller CLIP model.

## Dtype or Device Mismatch

Symptoms: errors mention tensors on different devices, expected scalar type Half/Float, or CPU/CUDA mismatch.

- Move preprocessed image batches and tokenized text tensors to the same device used by `clip.load`.
- Do not manually cast input images to fp16; `encode_image` casts to the model visual dtype internally.
- Convert exported features to CPU `float32` before saving, especially when extracting on CUDA.
- If using a JIT archive, prefer `jit=False` unless the workflow specifically needs TorchScript behavior.

## Missing scikit-learn

Symptoms: `ModuleNotFoundError: No module named 'sklearn'` during a linear-probe workflow.

- Feature extraction does not require scikit-learn; save `.npz` features first.
- Install scikit-learn only in the user's evaluation environment when linear probes are needed.
- Keep logistic-regression examples optional and do not make them a dependency of extraction helpers.

## Unnormalized Features

Symptoms: similarity/search rankings look wrong, image-image nearest neighbors are dominated by feature magnitude, or scores differ from CLIP examples.

- Normalize both image and text features with L2 norm before cosine similarity.
- Confirm the `.npz` archive records `normalized=True` when it is used for retrieval.
- Do not mix raw features from one archive with normalized features from another.
- Remember that `model(image, text)` normalizes internally, but `encode_image` and `encode_text` return raw features.

## Dataset Download or Fixture Issues

Symptoms: examples fail while trying to fetch CIFAR100, Country211, Rendered SST2, or YFCC100M-derived data.

- Treat dataset downloads as opt-in. They are not required for validating the extraction helper.
- Use local user-owned image directories or tiny fixtures for offline checks.
- Country211 is documented as an 11 GB archive, Rendered SST2 as 131 MB, and the YFCC100M subset as metadata for 14,829,396 images; do not download them in routine skill validation.
- Check dataset licenses and allowed use before storing or sharing derived features.

## Misleading Linear-Probe Accuracy

Symptoms: a linear probe reports unexpectedly high or low accuracy, or results change after label edits.

- Verify train/validation/test split isolation and avoid tuning on the test set.
- Sweep regularization such as `C` on a validation split rather than copying one value blindly.
- Report per-class metrics when classes are imbalanced or sensitive.
- Re-check prompt/class taxonomy choices; CLIP behavior can vary with class construction.
- Treat linear-probe accuracy as one diagnostic, not proof of deployment readiness. The model card notes that linear probes can underestimate model performance.

## Large-Batch Performance Problems

Symptoms: extraction is slower at larger batch sizes, CPU workers stall, or disk writes dominate runtime.

- Increase batch size only until GPU utilization improves; too-large batches can reduce throughput.
- Use a small number of DataLoader workers first, then tune for local storage and CPU capacity.
- Keep image decoding and preprocessing deterministic; skip unreadable images and record them separately.
- Save compressed `.npz` once at the end for small/medium runs; for very large runs, shard outputs deliberately and record shard metadata.
- Avoid mixing benchmark downloads, feature extraction, and classifier training in one unbounded command.
