# BAPPS Evaluation Troubleshooting

## Purpose

Read this when BAPPS evaluation fails because of split layout, label handling, or metric compatibility.

## Common issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for `ref`, `p0`, `p1`, `judge`, or `same` | The split directory does not have the expected subdirectories. | Recreate the fixture with `../../scripts/make_tiny_bapps_fixture.py` or correct the split path. |
| Score is unexpectedly low or zero | The split files are misaligned or the wrong split root was chosen. | The bundled helper enforces exact file alignment; fix the file names so each subdirectory contains the same relative keys. |
| `test_dataset_model.py --dataset_mode jnd` fails in the stock repo | The stock JND path passes a list into `JNDDataset.initialize`. | Use `scripts/score_bapps.py` instead of the buggy stock path. |
| `ImportError: cannot import name 'compare_ssim'` | Modern `scikit-image` no longer exports that symbol. | Use the bundled helper, which uses `skimage.metrics.structural_similarity` when available. |
| `batch_size > 1` with L2 or SSIM seems awkward | The stock classes were written for batch size 1. | The bundled helper iterates safely over batches, but `batch_size=1` is still the simplest choice for these metrics. |
| The metric downloads trunk weights on first use | The LPIPS backbone cache is empty. | Allow the one-time download or pre-cache the backbone weights before offline evaluation. |
| A CUDA request falls back to CPU | Torch cannot see a CUDA device in the current environment. | Leave `USE_GPU=0` or install a CUDA-capable Torch build in a CUDA-visible environment. |

## Recovery order

1. Run `python skills/disco/perceptual-similarity/scripts/check_lpips_env.py`.
2. Build a tiny fixture with `../../scripts/make_tiny_bapps_fixture.py`.
3. Re-run `scripts/score_bapps.py` on the tiny fixture.
4. Only after the tiny fixture works should you move to the full BAPPS split tree.

## Notes on stock vs bundled behavior

- The bundled helper intentionally does not rely on the stock JND loader.
- The bundled helper intentionally does not rely on `skimage.measure.compare_ssim`.
- The bundled helper validates alignment instead of guessing between subdirectories.

## Read next

- `../../references/bapps-dataset.md`
- `../../references/api-reference.md`
