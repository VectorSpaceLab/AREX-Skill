# MMPreTrain model-zoo inference troubleshooting

Use this guide to classify failures before retrying. Keep model-name, checkpoint/network, dependency, device, data, prototype, and visualization problems separate.

## Missing model-index assets

Symptoms:

- `list_models()` or `ModelHub.get(...)` fails before returning names.
- Error text mentions `.mim/model-index.yml`, model-index loading, package metadata, or missing packaged files.

Likely cause: the installed MMPreTrain distribution does not expose the packaged model-index assets expected by `ModelHub`.

Actions:

1. Confirm the import works independently: `python -c "import mmpretrain; print(mmpretrain.__version__)"`.
2. Reinstall MMPreTrain in a way that includes package data/model-index assets, then rerun `list_models('resnet18')`.
3. If using an editable/development install, ensure the package data assets are included in the installed distribution metadata rather than relying on a source checkout path.
4. Do not bypass this by hard-coding repository config paths in runtime guidance; fix the install or use a user-supplied config path deliberately routed through the training/config sub-skill.

## Invalid or ambiguous model names

Symptoms:

- `ValueError: Failed to find model "..."`.
- `inference_model` cannot map the model to an inferencer.

Actions:

1. Use `list_models(pattern)` or `scripts/list_models.py` to copy an exact model name.
2. Filter by task if the user knows the task, for example `list_models('blip', task='Image Caption')`.
3. Remember that many names include dataset, training recipe, source, and resolution suffixes. A family name such as `resnet50` may not be a complete model-zoo key.
4. For a config path supplied by the user, route config inspection/authoring questions to `../training-and-evaluation/SKILL.md`.
5. If the model exists but `inference_model` raises `No available inferencer for the model`, instantiate the task-specific inferencer only if the model's task is supported; otherwise route to training/evaluation or tools as appropriate.

## Checkpoint download, network, and cache failures

Symptoms:

- Timeout, DNS, HTTP, SSL, permission, or cache errors during inferencer construction.
- Construction tries to download even though the user expected offline behavior.
- Warning says default checkpoint cannot be found.

Actions:

1. For no-download work, set `pretrained=False`. This is the default for `get_model` but **not** for task inferencers.
2. For meaningful predictions without network, pass a local checkpoint string: `pretrained='checkpoints/model.pth'`.
3. When network is allowed, either use `pretrained=True` for the model-zoo default or pass an explicit checkpoint URL.
4. If a known URL should map to a local mirror, use `url_mapping=(pattern, replacement)` through `get_model` or an inferencer constructor `**kwargs`.
5. Verify the checkpoint matches the model architecture. Shape/key mismatch is a checkpoint/model compatibility issue, not a model-index issue.
6. Ensure the checkpoint/cache destination is writable and has enough disk space.
7. Keep random-weight outputs from `pretrained=False` out of any quality or accuracy claim.

## CPU/GPU device mismatch

Symptoms:

- `Torch not compiled with CUDA enabled`, `CUDA unavailable`, invalid device ordinal, or device placement errors.
- Inference works on CPU but fails after `device='cuda'`.

Actions:

1. Check the active PyTorch install: `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`.
2. Use `device='cpu'` in CPU-only environments.
3. Use `device='cuda:0'` only when the installed PyTorch build and driver support CUDA.
4. Loading checkpoints maps weights to CPU first; later movement to CUDA can still fail if CUDA support is missing.
5. If using `device_map='auto'`, verify optional dispatch/offload dependencies are installed and set a writable `offload_folder` when disk offload is used.
6. Reduce `batch_size` or `prepare_batch_size` if GPU/CPU memory is exhausted.

## Missing multimodal extras

Symptoms:

- Caption/VQA/grounding/retrieval model construction fails with missing tokenizer, transformer, sentencepiece, or other optional package imports.
- Basic classification/list-model APIs work, but multimodal inferencers fail.

Actions:

1. Treat base classification success as insufficient evidence for multimodal readiness.
2. Install the optional dependencies required by the selected multimodal model family in the active environment.
3. Re-run a minimal constructor smoke with `pretrained=False` first when possible, then retry with the checkpoint.
4. If the model requires large external language/vision components, confirm cache permissions and network policy before allowing default downloads.
5. If optional dependencies are unavailable, report the multimodal workflow as dependency-gated rather than misrouting to training.

## Retrieval prototype and cache problems

Symptoms:

- `Unsupported prototype type`.
- Prototype preparation fails on unreadable images or text files.
- `topk` errors, stale matches, shape/key mismatches, or suspicious results after reusing a cache.

Actions:

1. For `ImageRetrievalInferencer` and `TextToImageRetrievalInferencer`, use an image directory, list of image paths, dataset config dict, `BaseDataset`, or `DataLoader` as `prototype`.
2. For `ImageToTextRetrievalInferencer`, use a list of strings or a text file with one prototype string per line.
3. Keep `topk <= number_of_prototypes`.
4. Delete and rebuild `prototype_cache` when the model name, checkpoint, preprocessing, prototype content/order, `fast_match`, or relevant code version changes.
5. Use a smaller `prepare_batch_size` when prototype feature generation runs out of memory.
6. Ensure cache parent directories exist and are writable.
7. For image folders, verify every prototype image is readable by OpenCV/MMCV. Remove corrupt files or build an explicit clean list.
8. If a dataset config dict is needed, route schema and custom dataset questions to `../datasets-and-customization/SKILL.md`.

## Headless visualization

Symptoms:

- Window/display errors, process hangs waiting for a GUI, or no visual output is saved.

Actions:

1. Use `show=False` in non-interactive or server sessions.
2. Use `show_dir='outputs/vis'` to save visualization files.
3. For classification, tune `resize`, `rescale_factor`, and `draw_score` if the rendered text/image is unreadable.
4. For grounding/retrieval, tune `line_width`, `bbox_color`, `resize`, `figsize`, and `topk` as supported by the inferencer.
5. If plotting/image backends are missing, treat this as an optional visualization dependency issue; core inference may still work without visualization.

## Output serialization and interpretation

Symptoms:

- JSON dumping fails on NumPy arrays or tensors.
- Classification outputs are huge because `pred_scores` contains all class scores.
- User expects class names but receives only labels/scores.

Actions:

1. Convert NumPy arrays and tensors to Python lists before JSON serialization, or remove `pred_scores` when only top predictions are needed.
2. Pass `classes=[...]` to `ImageClassificationInferencer` when custom class names are needed and checkpoint metadata does not provide them.
3. Use `return_datasamples=True` for raw `DataSample` objects, but do not expect them to be JSON serializable.
4. In retrieval outputs, `match_score` can be a tensor; cast it to `float` before JSON/export.
5. Keep `pretrained=False` results labeled as random/untrained.

## Feature extraction and model surgery issues

Symptoms:

- `FeatureExtractor` returns unexpected tuple/list shapes.
- `stage='backbone'` or another extract keyword fails.
- Classification postprocessing fails after removing the head/neck.

Actions:

1. Use `get_model(..., pretrained=False, head=None, neck=None, backbone=dict(out_indices=(...)))` for no-download surgery.
2. Use `FeatureExtractor(model)` or direct `model.extract_feat` instead of classification inferencer when the classifier head is removed.
3. Check the selected model's `extract_feat` contract; not every architecture supports the same `stage` keyword or output structure.
4. Run one small CPU image through the extractor and print shapes before scaling to batches.
