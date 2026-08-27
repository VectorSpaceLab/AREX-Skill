# Batch Evaluation Metrics

## What The Repository Computes

`test_batch.py` optionally computes entropy-based Inception Score (IS) and Conditional Inception Score (CIS) over generated outputs:

- `--compute_IS` accumulates predictions over all generated images and reports `exp(mean(KL(p(y|x) || p(y))))` style score.
- `--compute_CIS` computes a per-input conditional distribution across styles, then reports an exponentiated mean entropy/KL-style quantity.

The implementation uses SciPy entropy and a user-provided Inception classifier state dict loaded through the repository utility.

## Additional Prerequisites

Metrics are not a free extension of inference. They require:

- the same legacy CUDA/PyTorch runtime as translation;
- a translated-input folder and generator checkpoint;
- a compatible Inception classifier checkpoint for the target domain;
- enough GPU memory to upsample outputs to 299x299 and run the classifier;
- a clear decision about whether A-to-B uses `--inception_b` or B-to-A uses `--inception_a`.

## When To Skip Metrics

Skip or defer metrics when the user only needs image translation, when no domain-specific Inception model exists, when the task is a quick smoke check, or when runtime/GPU constraints are unresolved. Do not fabricate metric values from sample images.

## Command Builder Pattern

Use the batch helper with explicit metric model paths:

```bash
python scripts/munit_batch_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/edges2shoes_folder.yaml \
  --input-folder datasets/edges2shoes/testA \
  --output-folder outputs/batch_edges2shoes \
  --checkpoint models/edges2shoes.pt \
  --a2b 1 \
  --compute-is \
  --compute-cis \
  --inception-b models/inception_edges2shoes_b.pt
```

The helper prints the corresponding `test_batch.py` command; it does not load the generator or Inception checkpoint.

## Interpretation Boundaries

IS/CIS values are only comparable under the same dataset split, checkpoint, number of styles, preprocessing, and Inception classifier. Treat them as experiment diagnostics, not as a universal measure of image quality.
