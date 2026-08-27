# MMAction2 model/extension troubleshooting

Use this guide for model-family, registry, customization, multimodal, and export failures. Route pure data/config, training/testing, or inference issues to the sibling sub-skills named in `SKILL.md`.

## Import or registry probe fails immediately

**Symptoms**

- `ModuleNotFoundError: No module named 'mmcv'` or `No module named 'mmengine'`.
- Assertion error saying MMCV or MMEngine is outside the supported version range.
- Registry probe cannot import `mmaction`.

**Likely cause**

MMAction2 imports MMCV and MMEngine during package import and checks compatible version ranges. Core registry probing cannot proceed until those dependencies are installed.

**Recovery**

- Install compatible MMEngine and MMCV for the user's PyTorch/CUDA/CPU environment.
- Re-run the registry probe after package import succeeds.
- Do not diagnose model-family failures until the core import works.

## `KeyError: ... is not in the ... registry`

**Symptoms**

- A config with `type='MyBackbone'`, `type='MyDataset'`, or `type='MyTransform'` fails during build.
- A project config works from one directory but not another.

**Likely cause**

The class was not imported, was registered into the wrong registry, or the default scope is not `mmaction`.

**Recovery**

1. Confirm `default_scope='mmaction'` unless the component deliberately belongs to another OpenMMLab package.
2. In standalone code, call `register_all_modules(init_default_scope=True)` before building.
3. For custom classes, import the module explicitly or add `custom_imports = dict(imports=['package.module'], allow_failed_imports=False)`.
4. Confirm the decorator matches the component: `@MODELS.register_module()` for backbones/heads/losses/models, `@DATASETS.register_module()` for datasets, `@TRANSFORMS.register_module()` for transforms, `@METRICS.register_module()` for metrics.
5. Run the registry probe and check whether the class name appears in the expected registry.

## Default scope conflict

**Symptoms**

- A model component name resolves in one script but not in another.
- Warnings say the current default scope is not `mmaction` and will be forced.
- Mixed MMDetection/MMPose/MMAction2 configs resolve components unpredictably.

**Likely cause**

MMEngine's current default scope points to another package. MMAction2 can set `mmaction`, but detection/pose subcomponents may need explicit scoped configs.

**Recovery**

- For pure MMAction2 work, set `default_scope='mmaction'` and call `register_all_modules(init_default_scope=True)`.
- For AVA/spatio-temporal detection configs, keep MMAction2 as the top-level scope but use explicit `_scope_='mmdet'` where detection components require MMDetection.
- Avoid repeated global scope changes inside reusable library code; initialize scope at the script/config boundary.

## Custom project class imports locally but config still fails

**Symptoms**

- `import my_project.models` succeeds, but registry build fails.
- The config uses a short type name, but the registry contains a different name.

**Likely cause**

The class decorator did not run, the class name differs from the config `type`, or `custom_imports` imports the package but not the module containing the decorated class.

**Recovery**

- Import the exact module that defines the decorated class.
- Confirm the class name or explicit registry name matches the config `type`.
- Use `allow_failed_imports=False` so failed imports stop early.
- Avoid relying on `__init__.py` side effects unless they are intentionally maintained.

## Classifier `num_classes` mismatch

**Symptoms**

- Linear layer checkpoint keys mismatch in shape, for example `[400, 2048]` vs `[2, 2048]`.
- Loss or metric complains about label range or top-k larger than classes.
- Predictions have the wrong number of scores.

**Likely cause**

The head still uses the source dataset class count, or a checkpoint for a different label space is loaded into a modified head.

**Recovery**

- Set `model.cls_head.num_classes` or detection `bbox_head.num_classes` to the target label space.
- If fine-tuning from a different label space, load only compatible backbone/neck weights or allow/reinitialize the head according to the user's training plan.
- Update label files and top-k metric options to match the target classes.
- For multi-label tasks, use multi-hot labels and a compatible loss/metric instead of integer-label assumptions.

## `in_channels` or tensor flattening mismatch

**Symptoms**

- Linear layer error like `mat1 and mat2 shapes cannot be multiplied`.
- Assertion from a head that feature channels do not match `in_channels`.
- `view`/`reshape` errors around `num_segs`, `num_clips`, or batch size.

**Likely cause**

The head is paired with a backbone/neck that emits a different channel count or feature layout, or the dataset pipeline produced a format for the wrong recognizer family.

**Recovery**

- Match `cls_head.in_channels` to the final feature channels emitted by the chosen backbone/neck.
- For `Recognizer2D`, ensure the pipeline/preprocessor yields `N x views x C x H x W` before flattening.
- For `Recognizer3D`, ensure `N x views x C x T x H x W`.
- For `RecognizerGCN`, ensure skeleton input resembles `B x num_clips x num_person x T x V x C`.
- For `RGBPoseHead`, provide separate RGB and pose channel counts.
- If using TPN/SlowFast/context/LFB components, account for concatenated or multi-pathway features.

## `average_clips` failure or unexpected prediction shape

**Symptoms**

- `ValueError` says an `average_clips` value is unsupported.
- Prediction output remains per-clip/per-view when a single video-level score was expected.

**Likely cause**

`average_clips` must be `score`, `prob`, or `None`. Setting it to `None` intentionally preserves per-view scores and changes downstream shape.

**Recovery**

- Use `prob` for probability averaging after softmax or `score` for raw-score averaging.
- Use `None` only for feature extraction or workflows that explicitly consume per-clip scores.
- Verify the number of clips/views generated by the test pipeline.

## Multimodal or retrieval model raises install-extra error

**Symptoms**

- Building `VindLURetrieval`, `VindLURetrievalMC`, or `VindLUVQA` raises an error asking for multimodal extras.
- CLIP/tokenizer imports fail.

**Likely cause**

MMAction2 registers placeholders for some multimodal models when required packages such as `transformers>=4.28.0` are absent. CLIP-related surfaces can also require `openai-clip`.

**Recovery**

- Install the multimodal or CLIP dependencies requested by the error message in the user's environment.
- Re-run the registry probe and verify the class is no longer a placeholder.
- Do not substitute an RGB-only recognizer for a retrieval/VQA model unless the task has changed.

## AVA/spatio-temporal detection components missing

**Symptoms**

- Import errors involving `mmdet`, ROI heads, bbox heads, or `bbox2roi`.
- Detection configs with `FastRCNN` fail to build while ordinary recognition configs build.

**Likely cause**

AVA/MultiSports-style detection uses MMDetection registries and structures for ROI/bbox components.

**Recovery**

- Install a compatible MMDetection version for the user's OpenMMLab stack.
- Confirm detection components use explicit MMDetection scope where needed.
- Keep recognition and detection heads separate; detection bbox heads have different class semantics and input shapes.

## ONNX export fails

**Symptoms**

- `onnxruntime` missing.
- Export script warns the model type is not supported.
- Unsupported operator or dynamic-axis error.
- Post-export output difference is large.

**Likely cause**

The chosen export utility is specialized for GCN, PoseC3D, or spatio-temporal detection and may not support the model family. Optional ONNX packages may be absent.

**Recovery**

- Confirm the model is one of the intended export families before exporting.
- Install `onnx`/`onnxruntime` if the user wants export plus comparison.
- Provide explicit input dimensions: frames, persons, joints, heatmap/image size, or spatial shape.
- Treat synthetic-input ONNXRuntime comparison as a smoke check only; validate deployment separately.

## TorchServe packaging fails

**Symptoms**

- Import error says `torch-model-archiver` is required.
- `.mar` archive builds but labels are wrong at serving time.
- Existing archive is overwritten unexpectedly.

**Likely cause**

TorchServe packaging requires an optional archiver package, a label file matching the head class order, and explicit overwrite handling.

**Recovery**

- Install `torch-model-archiver` in the packaging environment.
- Verify the label file line count and order match `cls_head.num_classes`.
- Use a staging output folder and require explicit overwrite confirmation.
- Smoke-test the archive in the user's serving environment before treating it as deployable.
