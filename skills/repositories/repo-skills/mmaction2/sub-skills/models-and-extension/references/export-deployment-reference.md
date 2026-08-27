# MMAction2 export and deployment reference

This reference describes MMAction2 export/deployment utility contracts and caveats. It is intentionally conservative: exporting, publishing, and packaging mutate user artifacts, so future agents should ask for explicit input/output paths and never run these workflows as a hidden side effect.

## Safety defaults

- Do not download model weights or datasets while preparing an export plan unless the user explicitly asks for it.
- Do not overwrite checkpoints, ONNX files, TorchServe archives, or converted configs without an explicit destination and overwrite confirmation.
- Prefer CPU dry-run checks for parser/config compatibility, but real ONNX/TorchServe packaging may require optional packages and enough memory.
- Verify that `default_scope='mmaction'` and `register_all_modules`/imports are active before constructing models.
- Route ordinary training/test/inference execution to sibling sub-skills; this reference covers artifact conversion and deployment packaging only.

## Publishing a checkpoint

The publishing utility contract is:

- Inputs: an existing checkpoint file and a temporary output checkpoint filename.
- Behavior: load the checkpoint on CPU; remove runtime-only keys such as optimizer state, parameter schedulers, message hub state, and stored data-preprocessor mean/std; save a smaller checkpoint; compute SHA-256; rename the output to include date and the first eight hash characters.
- Side effect: writes and renames an output file. The input checkpoint should remain unchanged, but always choose an output in a staging directory.
- Caution: if project-specific metadata contains sensitive fields, inspect and scrub the checkpoint `meta` before publishing.

Use this only after the user asks to prepare a public checkpoint and supplies the exact input and output locations.

## Config conversion utility

MMAction2 includes a recognizer config conversion utility for older OpenMMLab-style recognizer configs. Its contract is:

- Inputs: old recognizer config and output config.
- Converts dataset/data-loader fields to MMEngine-style dataloaders.
- Moves image normalization into `model.data_preprocessor`.
- Moves `average_clips` from `model.test_cfg` into `model.cls_head.average_clips` when present.
- Converts old optimizer/evaluation/runtime fields into `optim_wrapper`, `param_scheduler`, `train_cfg`, `val_cfg`, `test_cfg`, and `default_hooks`.
- Sets `default_scope='mmaction'`.

Do not use it for arbitrary non-recognizer configs without reviewing the generated output. Detection, localization, multimodal, and project configs may need manual handling.

## ONNX export utility contracts

MMAction2's ONNX utilities are specialized wrappers, not a universal exporter.

### GCN skeleton ONNX

- Intended model type: skeleton graph recognizers such as STGCN/AAGCN-like `RecognizerGCN` models.
- Required inputs: config, checkpoint.
- Important flags: number of frames, maximum persons, number of joints, device, output ONNX file.
- Default shape logic: if joint count is not supplied, common graph layouts map `openpose -> 18`, `nturgb+d -> 25`, `coco -> 17`.
- Exported input convention: a dynamic skeleton tensor with batch, person, and frame axes; class-score output has dynamic batch.
- Optional dependencies: `onnxruntime` is used to check exported output; PyTorch ONNX export is required.

### PoseC3D ONNX

- Intended model type: PoseC3D-like skeleton heatmap recognizers, not generic GCN models.
- Required inputs: config, checkpoint.
- Important flags: number of frames, heatmap/image size, number of joints, device, output ONNX file.
- Default joint count: if not supplied, use the backbone input-channel setting as the number of joints/channels.
- Exported input convention: a dynamic tensor with batch and frame axes; class-score output has dynamic batch.
- Optional dependencies: `onnxruntime` for post-export comparison.

### Spatio-temporal detection ONNX

- Intended model type: AVA/MultiSports-style spatio-temporal detection with a `FastRCNN`-style model and ROI/bbox heads.
- Required inputs: config, checkpoint.
- Important flags: number of frames, spatial shape, device, output ONNX file.
- Exported input convention: video clip tensor plus ROI tensor; dynamic axes include batch, height, width, and number of RoIs.
- Optional dependencies: MMDetection for `bbox2roi` and detection components; `onnxruntime` for output checks.
- Caution: this export path uses synthetic proposals for export validation. It does not replace full detection/inference validation.

## TorchServe archive contract

The TorchServe packaging utility converts a config, checkpoint, label file, and handler into a `.mar` archive.

- Required inputs: config path, checkpoint path, output folder, label file.
- Optional inputs: model name, model version, force-overwrite flag.
- Optional dependency: `torch-model-archiver` provides the `model_archiver` package; without it the utility raises an import error with an installation hint.
- Behavior: creates a temporary copy of the config and label map, uses the bundled MMAction2 TorchServe handler, and writes `{model_name}.mar` to the output folder.
- Caution: the label file must match `cls_head.num_classes` and class order. Mismatched labels produce valid archives with wrong user-facing classes.

## Feature extraction and CLIP-related utilities

The clip-level feature extraction surface can preserve per-clip features by setting head averaging to `None` or force score averaging for feature tensors. Important cautions:

- For TSM-like models, `num_segments` must match the clip length or segment count expected by the pipeline.
- Long-video extraction needs an explicit clip interval.
- Preserving multiple clips can increase memory and output size quickly.
- CLIP/action-text workflows may require optional packages such as `openai-clip`, `transformers`, and multimodal extras.

## Optional dependency map

| Surface | Likely optional packages | Failure shape |
| --- | --- | --- |
| Core model/config build | `torch`, `mmengine`, compatible `mmcv` | Import fails before registry probing, often with a version-range assertion or missing module |
| Video decoding pipelines | `decord`, `opencv`, `av`, `pims`, `PyTurboJPEG` depending on transforms | Dataset/pipeline build succeeds but sample loading fails |
| Audio | `librosa`, `soundfile` | Audio feature extraction or loading fails |
| Spatio-temporal detection | `mmdet`; sometimes detector checkpoints in user workflows | ROI head, bbox utilities, or detection APIs unavailable |
| Pose/skeleton demos that estimate pose | `mmpose`; sometimes `mmdet` for person detection | Pose inference APIs unavailable |
| Multimodal/VindLU | `transformers>=4.28.0`, multimodal extras | Registry placeholder raises an install-extra error |
| CLIP similarity/action-text | `openai-clip` plus text/tokenizer dependencies | Import or tokenizer/model build failure |
| ONNX export checks | `onnx`, `onnxruntime` | Export or post-export comparison fails |
| TorchServe | `torch-model-archiver`, TorchServe runtime packages | `.mar` packaging import failure |

## Deployment decision checklist

1. Identify task family first: video recognition, skeleton GCN, PoseC3D, spatio-temporal detection, localization, retrieval/multimodal, or audio.
2. Confirm the model type and head shape in the config before selecting an export path.
3. Confirm optional packages with the registry probe or package manager.
4. Confirm the checkpoint was trained for the same `num_classes`, keypoint layout, modality, and input shape.
5. Choose a new output path. Never overwrite the user's only checkpoint or deployment artifact.
6. For ONNX, compare PyTorch and ONNXRuntime outputs on a synthetic input only as a smoke check; it does not prove end-to-end task accuracy.
7. For TorchServe, verify label-file order and run a small request in the user's serving environment after packaging.
