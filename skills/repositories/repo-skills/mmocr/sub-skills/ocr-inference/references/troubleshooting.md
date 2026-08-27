# MMOCR inference troubleshooting

Use this reference when MMOCR inference construction, execution, saved outputs, or visualization behaves unexpectedly.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `At least one of det, rec and kie should be provided.` | `MMOCRInferencer()` was constructed with no task selected. | Pass at least one of `det`, `rec`, or `kie`. For OCR use `det`+`rec`; for KIE chain use all three. |
| Error for unknown model name, missing metafile entry, or invalid config | Model alias/name is wrong for that inferencer type, or a config path does not exist. | Use a known task-appropriate alias (`DBNet`, `CRNN`, `SAR`, `SDMGR`, etc.) or pass an existing local `.py` config path. Match model type to inferencer type. |
| Network/download/cache failure during model construction | A model-zoo name was used without a local checkpoint, so MMOCR tried to resolve pretrained weights. | Use local `weights`/`det_weights`/`rec_weights`/`kie_weights`, pre-populate the model cache, or intentionally allow network access. The bundled smoke helper never downloads by default. |
| `kie_config is only applicable when det_config and rec_config are both provided` | `kie` was passed to `MMOCRInferencer` without both `det` and `rec`. | Initialize KIE chain as `MMOCRInferencer(det=..., rec=..., kie=...)`. If boxes/text already exist, use direct `KIEInferencer` instead. |
| Save flags fail with `out_dir must be specified...` | `save_vis=True` or `save_pred=True` was used while `out_dir` was empty. | Keep `out_dir` non-empty. MMOCR's default is `results/`; explicit empty strings are invalid when saving. |
| No pop-up window, Qt/OpenCV display error, process hangs around visualization | `show=True` was used in a headless session or without a usable display. | Set `show=False`; use `out_dir`, `save_vis=True`, and optionally `return_vis=True` if arrays are needed in memory. |
| CUDA device error or CPU-only environment failure | `device="cuda:N"` was requested when CUDA is unavailable or the checkpoint/backend is incompatible. | Check CUDA first; use `device="cpu"` for portable smoke tests. Do not use CPU success as proof of CUDA performance or memory fit. |
| KIE chain fails after detection/recognition, especially on blank images | The detection stage produced no boxes, and MMOCR's KIE chain has a known empty-detection failure path because KIE receives no instances. | Check `det_polygons` before expecting KIE output. Lower visualization threshold only for drawing; it may not create detections. Try a clearer image or run detection only first. |
| JSON saved but visualization missing, or visualization saved but `result["visualization"]` is empty | Save flags and return flags are separate. | `save_vis=True` writes files; `return_vis=True` returns arrays. `save_pred=True` writes JSON; `print_result=True` prints predictions. Check `out_dir/vis/` and `out_dir/preds/`. |

## No task selected

`MMOCRInferencer` is a wrapper over detection, recognition, and KIE inferencers. It refuses to initialize when all task arguments are `None`:

```python
from mmocr.apis import MMOCRInferencer

# Wrong: no task selected.
# MMOCRInferencer()

# Valid modes:
MMOCRInferencer(det="DBNet", device="cpu")
MMOCRInferencer(rec="CRNN", device="cpu")
MMOCRInferencer(det="DBNet", rec="CRNN", device="cpu")
MMOCRInferencer(det="DBNet", rec="SAR", kie="SDMGR", device="cpu")
```

## Invalid model name or config path

Model strings are either metadata names/aliases or local config paths. Common fixes:

1. Match the task type: do not pass a recognition-only alias to `TextDetInferencer`, or a detection alias to `TextRecInferencer`.
2. If using a config path, verify the `.py` file exists in the current project or package assets and is readable.
3. If using a model-zoo alias, check for spelling and case. Examples include `DBNet`, `DB_r18`, `CRNN`, `SAR`, `svtr-small`, and `SDMGR`.
4. If using a custom model, ensure custom modules are registered before constructing the inferencer; route custom-component work to `../model-api-components/`.

## Missing checkpoint, cache, or network access

A model-zoo name without explicit local weights can trigger pretrained weight resolution. That is convenient online but fragile in restricted environments. Prefer explicit local checkpoints for reproducibility:

```python
from mmocr.apis import MMOCRInferencer

ocr = MMOCRInferencer(
    det="local_det_config.py",
    det_weights="local_det_checkpoint.pth",
    rec="local_rec_config.py",
    rec_weights="local_rec_checkpoint.pth",
    device="cpu",
)
```

If a checkpoint URL is intentionally used, treat it as a network-dependent operation. If a local checkpoint was trained with MMEngine and includes config metadata, some standard inferencers can be constructed with `weights="local_checkpoint.pth"` and no separate `model`, but this only works when the checkpoint actually contains the needed config.

## KIE initialization and input failures

### KIE through `MMOCRInferencer`

`kie` is only effective when both detection and recognition models are selected. This is because the high-level chain creates KIE instances from detected boxes and recognized text.

Wrong:

```python
from mmocr.apis import MMOCRInferencer

# Missing recognition model.
# MMOCRInferencer(det="DBNet", kie="SDMGR")
```

Right:

```python
from mmocr.apis import MMOCRInferencer

kie = MMOCRInferencer(det="DBNet", rec="SAR", kie="SDMGR", device="cpu")
```

### Direct `KIEInferencer`

Direct KIE expects structured dictionaries, not bare image paths:

```python
from mmocr.apis import KIEInferencer

sample = {
    "img": "receipt_or_form_image",
    "instances": [
        {"bbox": [10, 20, 120, 45], "text": "TOTAL"},
        {"bbox": [125, 20, 210, 45], "text": "$12.30"},
    ],
}

inferencer = KIEInferencer(model="SDMGR", device="cpu")
result = inferencer(sample, show=False)
```

For no-visual KIE configs, provide `img_shape` if `img` is not present. For visual KIE configs, include `img` so MMOCR can draw outputs.

## Empty detections before KIE

The high-level KIE chain has a known fragile path when detection returns no text regions: KIE receives no instances and can fail. Debug in stages:

```python
from mmocr.apis import MMOCRInferencer

detector = MMOCRInferencer(det="DBNet", device="cpu")
det_result = detector("receipt_or_form_image", show=False)
print(det_result["predictions"][0].get("det_polygons", []))
```

If detections are empty, fix image quality, model selection, input orientation, or checkpoint choice before running KIE. `pred_score_thr` controls visualization drawing and is not a reliable way to create missing detections.

## Headless visualization

In non-GUI environments, `show=True` may silently do nothing, raise an OpenCV/Qt display error, or hang. Use file outputs instead:

```python
result = inferencer(
    "image_or_folder",
    out_dir="mmocr_outputs/headless",
    save_pred=True,
    save_vis=True,
    return_vis=False,
    show=False,
)
```

If the caller needs visualization arrays in Python memory, add `return_vis=True`; saved files alone do not guarantee `result["visualization"]` is populated.

## Output file confusion

Remember the four independent output controls:

- `save_pred=True`: write JSON under `out_dir/preds/`.
- `save_vis=True`: write images under `out_dir/vis/`.
- `return_vis=True`: return visualization arrays in `result["visualization"]`.
- `print_result=True`: print predictions to stdout.

For `MMOCRInferencer`, high-level JSON keys are prefixed by task (`det_polygons`, `rec_texts`, `kie_labels`, etc.). For standard inferencers, keys are task-local (`polygons`, `text`, `labels`, `texts`, etc.). Mixing these schemas is a common source of downstream `KeyError`s.

## CPU versus CUDA

Use CPU to establish that imports, configs, input paths, and output flags are sane. Move to CUDA only after checking device availability and memory constraints:

```python
import torch
print(torch.cuda.is_available())
```

If CUDA is unavailable, use `device="cpu"`. If CUDA is available but inference fails, confirm that the installed Torch/MMCV/MMDetection stack matches the CUDA runtime and that the checkpoint architecture matches the selected config.
