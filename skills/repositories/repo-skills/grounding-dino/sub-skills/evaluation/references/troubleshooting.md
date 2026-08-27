# Evaluation Troubleshooting

## Preflight Checks

Run help first; it must not require weights or COCO data:

```bash
python sub-skills/evaluation/scripts/grounding_dino_coco_eval.py --help
```

Then validate real inputs with the same command shape you plan to benchmark. The helper checks paths, COCO JSON structure, category IDs, a sample of image files, device availability, and importable runtime dependencies before loading the model.

## Common Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Missing config file` | `--config_file` points to a nonexistent or mistyped config path. | Pass a local config file that matches the checkpoint, such as the Swin-T OGC config for the Swin-T OGC checkpoint. |
| `Missing checkpoint file` | Weights were not downloaded or `--checkpoint_path` points to a directory. | Download weights outside this helper and pass the local `.pth` path. The helper never downloads checkpoints. |
| `Missing annotation JSON` | `--anno_path` is not a file or is not the COCO instances JSON. | Point to `annotations/instances_val2017.json` or a valid COCO-style JSON. |
| `Missing image directory` | `--image_dir` does not exist or points to `annotations/` instead of images. | Point to the directory containing files named by `images[*].file_name`, such as `val2017/`. |
| `Image files referenced by COCO JSON were not found` | Annotation JSON and image root are from different datasets/splits, or `file_name` has nested prefixes not present under the root. | Pair the annotation file and image folder from the same split; inspect `images[0].file_name` and confirm it resolves under `--image_dir`. |
| `COCO categories must contain integer id values` | Custom JSON has missing, string, negative, or duplicate category IDs. | Keep official COCO integer category IDs for benchmarks; for subsets, preserve the original IDs instead of remapping labels arbitrarily. |
| `No categories found` | The JSON is not an instances-style COCO annotation file. | Use an object detection instances JSON with a nonempty `categories` list. |
| `ModuleNotFoundError: pycocotools` | The active environment lacks COCO API dependencies. | Install the package's base dependencies including `pycocotools`, then retry `--help` and imports. |
| `CUDA device requested but torch.cuda.is_available() is False` | CPU-only Torch, hidden GPU, wrong CUDA runtime, or unavailable device. | Use `--device cpu` for smoke tests or install/use a CUDA-enabled Torch environment and visible GPU. |
| `invalid device ordinal` | `cuda:N` names a GPU index that is not visible. | Use `cuda`, a valid `cuda:0`-style index, or set the visible devices before running. |
| Very slow evaluation | Full COCO val2017 on CPU or too many dataloader workers for the machine. | Use GPU for benchmark runs; use `--device cpu --num_workers 0` only for tiny smoke tests. |
| `NameError: _C`, custom C++ op warning, or deformable attention op failure | GroundingDINO custom extension was not built or is incompatible with the current Torch/CUDA stack. | Reinstall/build GroundingDINO in the target environment; if using CPU-only smoke tests, distinguish harmless import warnings from runtime failures in model forward. |

## Low AP Diagnostics

If AP is far below the expected Swin-T OGC COCO zero-shot signal of about `48.5`, check these in order:

1. **Checkpoint/config pairing**: Swin-T OGC checkpoint with Swin-T OGC config; Swin-B checkpoint with Swin-B config. Mixed pairs can load partially or run with poor AP.
2. **Dataset split**: use official COCO val2017 images with `instances_val2017.json` for benchmark comparison.
3. **Category IDs**: preserve official category IDs such as `1` for person and the COCO gaps where IDs are not contiguous. Remapped IDs change evaluator matching.
4. **Category names**: keep lower-case COCO names. Custom aliases, plurals, or slash-separated names alter token spans and positive maps.
5. **`--num_select`**: default `300` matches the demo intent. Smaller values can drop true positives; larger values can alter precision/recall behavior.
6. **Transforms and image scale**: the helper uses resize `800`, max size `1333`, tensor conversion, and ImageNet normalization. Changing these breaks comparability.
7. **Device/dependencies**: CPU and GPU should produce similar metrics in principle, but dependency drift, custom op differences, or precision/kernel changes can cause small deviations.
8. **Mini-subsets**: AP on a few images has high variance and should not be compared to the full COCO benchmark.

## Category-caption Issues

GroundingDINO evaluation builds one caption from category names: `person . bicycle . car . ... .`. Token spans map each category to text-token positions. If category names are malformed, the model may still run but produce labels that do not correspond to the evaluator's categories.

Use this checklist for custom COCO-style data:

- Ensure every category has a unique integer `id` and nonempty string `name`.
- Prefer simple lower-case object names separated by spaces, not commas or sentence fragments.
- Keep `categories` stable between training/evaluation annotations and prediction interpretation.
- For benchmark claims, do not rename official COCO categories.

## Smoke Tests vs Benchmarks

A useful smoke test can use a mini-COCO JSON and one or two local images on CPU. It should verify that the helper validates inputs, loads the model, prints the category prompt, updates the evaluator, and emits a COCO summary. It cannot verify the published AP. A benchmark run needs the official dataset, matching weights/config, and a realistic GPU-backed environment.
