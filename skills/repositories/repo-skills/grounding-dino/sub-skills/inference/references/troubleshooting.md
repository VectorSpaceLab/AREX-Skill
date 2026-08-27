# GroundingDINO Inference Troubleshooting

Use this guide for single-image inference failures from the function API, `Model` wrapper, or bundled CLI helper.

## File And Argument Validation

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `missing config` | The config path does not exist or points to a directory. | Provide a packaged GroundingDINO config file such as the Swin-T or Swin-B config copied with the installed package or skill workflow. |
| `missing checkpoint` | No model weights were supplied. | Download or provide a compatible `.pth` checkpoint yourself; the helper never downloads weights. |
| `missing image` or `image could not be opened` | Bad path, unsupported image, or corrupted image. | Verify the file path and open it with PIL/OpenCV before model inference. |
| Threshold error | `box_threshold` or `text_threshold` is outside `[0, 1]`. | Use typical values such as `0.35` for boxes and `0.25` for text. |
| `provide --text-prompt or --classes` | No prompt source was supplied. | Use `--text-prompt "cat . dog ."` or `--classes cat dog`. |

## CPU, CUDA, And Custom Ops

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `CUDA device requested but torch.cuda.is_available() is false` | `--device cuda` was selected in a CPU-only environment. | Add `--cpu-only` or use `--device cpu`. |
| CPU-only warning about custom C++ ops | The package can run many inference paths without the CUDA extension, but some optimized ops may be unavailable. | For CPU smoke tests, proceed if imports and inference work. For GPU/CUDA performance, reinstall with a matching CUDA toolkit. |
| `NameError: name '_C' is not defined` | GroundingDINO custom C++/CUDA extension did not build or cannot be imported. | Reinstall GroundingDINO after ensuring PyTorch, CUDA runtime, compiler, and `CUDA_HOME` are aligned. |
| Runtime error mentioning `CUDA_HOME` | CUDA extension build cannot find the CUDA toolkit. | Set `CUDA_HOME` to the CUDA toolkit root that matches the active PyTorch CUDA version, then reinstall the package. |
| Checkpoint loads but GPU OOM occurs | Large image, Swin-B config, or limited GPU memory. | Try CPU for validation, use a smaller image, or use the Swin-T config/checkpoint pair. |

Do not assume CUDA is available because the machine has a GPU. Always check with `torch.cuda.is_available()` in the active Python environment.

## No Detections Or Poor Labels

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Zero detections | `box_threshold` is too high, object is absent, prompt is mismatched, or checkpoint/config pair is wrong. | Lower `box_threshold`, verify visible objects, and confirm config/checkpoint compatibility. |
| Labels combine multiple classes | Prompt lacks period separators or `remove_combined` is not enabled for multi-category prompts. | Use `cat . dog . person .`; try `--remove-combined` in normal prompt mode. |
| Labels are too long/noisy | `text_threshold` is too low. | Increase `text_threshold` gradually, such as from `0.25` to `0.35`. |
| Expected object missing but other objects detected | Prompt token does not match the visual concept or threshold is too strict. | Try synonyms and lower thresholds; separate categories with periods. |
| Unexpected class ID from `predict_with_classes` | `phrases2classes` uses substring matching. | Avoid overlapping class names or inspect phrases before trusting `detections.class_id`. |

## Token Span Problems

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `malformed token spans` | The span value is not valid Python literal syntax. | Quote the whole argument and use bracketed integer pairs, e.g. `"[[[9, 10], [11, 14]]]"`. |
| `outside caption bounds` | Offsets were computed against a different prompt. | Recompute offsets on the normalized caption: lowercased, stripped, final period present. |
| `selects only whitespace` | A span covers spaces instead of words. | Adjust the range to cover non-whitespace phrase text. |
| `did not align with tokenizer tokens` | Offsets land on punctuation or a boundary the tokenizer cannot map. | Shift the start/end by one character or span the full word. |
| Token-span run ignores `text_threshold` | Expected behavior from the demo workflow. | Tune `box_threshold`; token spans use phrase-specific logits instead of text-threshold phrase extraction. |

## API Misuse

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Colors look wrong in custom visualization | Function API image is RGB, OpenCV uses BGR. | `annotate` returns BGR for `cv2.imwrite`; convert explicitly if using PIL/matplotlib. |
| Boxes are in the wrong place | Normalized `cxcywh` boxes were treated as pixel `xyxy`. | Convert from `cxcywh` to `xyxy` and scale by image width/height before drawing. |
| `predict_with_caption` crashes on image shape | The wrapper expects a BGR NumPy image, usually from `cv2.imread`. | Check `image is not None` and pass a 3-channel BGR array. |
| Import fails for `supervision` | The wrapper and `annotate` depend on `supervision`. | Install the package dependencies used by GroundingDINO, including `supervision>=0.22.0`. |

## Fast Diagnostic Commands

Check helper help without model weights:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py --help
```

Check CUDA visibility in the current environment:

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.version.cuda)"
```

Check public signatures:

```bash
python - <<'PY'
import inspect
from groundingdino.util import inference
for name in ['preprocess_caption', 'load_model', 'load_image', 'predict', 'annotate']:
    print(name, inspect.signature(getattr(inference, name)))
print('Model', inspect.signature(inference.Model))
PY
```
