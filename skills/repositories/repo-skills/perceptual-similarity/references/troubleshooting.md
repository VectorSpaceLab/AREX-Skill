# Troubleshooting

## Purpose

Read this when install, import, backend, dataset, or compatibility issues block LPIPS, BAPPS evaluation, or BAPPS training.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lpips'` | The package is not installed in the active environment. | Install the public package and rerun `scripts/check_lpips_env.py`. |
| `torchvision` downloads backbone weights on first use | The pretrained AlexNet/VGG/SqueezeNet trunk is not cached yet. | Allow network access once, or pre-cache the torchvision weights before running a no-network workflow. |
| `ImportError: cannot import name 'compare_ssim' from 'skimage.measure'` | The stock legacy SSIM path depends on an old `scikit-image` symbol that modern releases no longer export. | Use the bundled BAPPS helper, which uses a modern `skimage.metrics.structural_similarity` fallback. |
| `test_dataset_model.py --dataset_mode jnd` fails with a list/path error | The stock source loader passes a list into `JNDDataset.initialize`. | Use the bundled `score_bapps.py` helper instead of the buggy stock JND path. |
| `train.py` fails because `checkpoints/...` is missing | The source training script expects the checkpoint directory to exist. | Use the bundled `train_bapps.py` helper, which creates the directory automatically, or create the directory first. |
| `ModuleNotFoundError: dominate` from the old training stack | The source `train.py` imports the HTML/visualization path. | Install `dominate` only if you intentionally run the old stock script; the bundled training helper does not need it. |
| `CUDA unavailable` or `torch.cuda.is_available() -> False` | The environment is CPU-only. | Use CPU mode; the bundled helpers are CPU-friendly by default. Only request GPU mode when the environment has a CUDA-capable Torch build and a visible device. |
| `FileNotFoundError` or `ValueError` for BAPPS splits | The split path or subdirectory layout is wrong. | Use `scripts/make_tiny_bapps_fixture.py` for smoke tests, then verify that the required subdirectories and `.npy` labels exist. |
| Distances look reversed or nonsensical | Images were not scaled consistently. | LPIPS expects RGB tensors normalized to `[-1, 1]`. The bundled image loaders and helper scripts handle this automatically. |

## Recovery order

1. Run `python skills/disco/perceptual-similarity/scripts/check_lpips_env.py`.
2. If you need smoke data, run `python skills/disco/perceptual-similarity/scripts/make_tiny_bapps_fixture.py --output-root /tmp/perceptual-similarity-fixture`.
3. Use the sub-skill helper that matches the task:
   - `metric-usage` for pairwise comparison or LPIPS loss.
   - `bapps-evaluation` for 2AFC/JND scoring.
   - `bapps-training` for training or fine-tuning.
4. If a failure involves the stock repo scripts instead of the bundled helpers, prefer the bundled helper path unless you explicitly need to study the old behavior.

## When to stop and change the environment

Stop and change the environment when:

- The required public package cannot be imported.
- The intended GPU backend is missing and the task genuinely requires GPU verification.
- A download-only dependency such as pretrained trunk weights is unavailable and the workflow cannot proceed offline.

## Reference links inside the skill tree

- `references/api-reference.md`
- `references/bapps-dataset.md`
- `sub-skills/metric-usage/references/troubleshooting.md`
- `sub-skills/bapps-evaluation/references/troubleshooting.md`
- `sub-skills/bapps-training/references/troubleshooting.md`
