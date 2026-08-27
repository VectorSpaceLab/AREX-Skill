---
name: ocr-inference
description: "Use MMOCR inference APIs and safe CLI preflights for text
  detection, recognition, OCR chains, KIE, text spotting, outputs, and
  visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ocr-inference

Use this sub-skill when the task is to run or debug MMOCR inference: text detection, text recognition, a detection+recognition OCR chain, KIE on OCR results, text-spotting inference notes, visualization, prediction dumping, model/checkpoint/device selection, and safe preflight checks.

## Route first

- For concrete OCR/KIE inference calls, start with [Inference workflows](references/inference-workflows.md).
- For exact class signatures, accepted inputs, output keys, batching, devices, model names, and save/visualization arguments, use [API reference](references/api-reference.md).
- For failure triage, especially KIE initialization, model-name errors, missing checkpoints, headless visualization, or output-directory confusion, use [Troubleshooting](references/troubleshooting.md).
- For a no-download preflight CLI, use the bundled [MMOCR inference smoke helper](scripts/mmocr_inference_smoke.py).

## Boundaries

Use sibling sub-skills instead of this one when the task is outside runtime inference:

- Training, testing, metric evaluation, schedule changes, config editing, or checkpoint evaluation: `../training-evaluation-configs/`.
- Dataset preparation, annotation conversion, dataset-zoo mechanics, dictionaries, or data-format migration: `../data-preparation/`.
- Model internals, custom backbones/heads/losses/postprocessors/registries, or project component implementation: `../model-api-components/`.

## Safe default operating pattern

1. Decide the mode: detection only, recognition only, OCR chain, KIE chain, direct `KIEInferencer`, or `TextSpotInferencer`.
2. Prefer local config+checkpoint paths for offline or reproducible work. Passing a model-zoo name without a local weight may trigger a model download/cache lookup during real inference.
3. Use `device="cpu"` when CUDA availability is unknown. Use `device="cuda:0"` only after confirming CUDA is available.
4. In headless sessions, keep `show=False`; use `out_dir`, `save_pred=True`, and `save_vis=True` to produce JSON and visualization files.
5. For KIE through `MMOCRInferencer`, initialize with all three components: `det`, `rec`, and `kie`. KIE without both detection and recognition is invalid.
6. If a save flag is enabled, keep `out_dir` non-empty. MMOCR writes predictions below `preds/` and visualizations below `vis/` inside that output directory.

## Minimal examples

Headless OCR chain with the high-level inferencer:

```python
from mmocr.apis import MMOCRInferencer

ocr = MMOCRInferencer(det="DBNet", rec="CRNN", device="cpu")
result = ocr(
    "image_or_folder",
    batch_size=1,
    det_batch_size=1,
    rec_batch_size=4,
    out_dir="mmocr_outputs/ocr",
    save_pred=True,
    save_vis=True,
    print_result=True,
    show=False,
)
print(result["predictions"][0].keys())
```

No-download preflight from this sub-skill directory:

```bash
python scripts/mmocr_inference_smoke.py image_or_folder --det DBNet --rec CRNN --device cpu
```

The helper only preflights by default. Add `--execute` only when local weights are supplied or `--allow-download` is intentionally set.
