# InternImage Detection Troubleshooting

Use this for InternImage MMDetection 2.x detection, instance segmentation, image-demo, and SAM-prompted mask failures. It distills source evidence from detection entrypoints, custom plugin packages, DCNv3 operator code, config families, and SAM integration code.

## Version and dependency mismatches

Symptoms:

- Registry errors or import failures after installing modern OpenMMLab packages.
- Config parsing fails with missing runner/data-pipeline APIs.
- Errors involving `mmcv`, `mmdet`, `timm`, `numpy`, `pydantic`, or `yapf` after environment changes.

Likely cause and fix:

- The inspected detection stack targets MMDetection `2.28.1`, `mmcv-full==1.5.0`, `timm==0.6.11`, PyTorch with CUDA, `numpy<2.0`, `pydantic==1.10.13`, and `yapf==0.40.1`.
- Do not silently run these configs under MMDetection 3.x. Treat that as a migration task.
- Prefer an isolated environment for this workflow; mixed OpenMMLab generations commonly fail in confusing ways.

## Custom module and registry failures

Symptoms:

- `ModuleNotFoundError: No module named 'mmcv_custom'`
- `ModuleNotFoundError: No module named 'mmdet_custom'`
- `ModuleNotFoundError: No module named 'ops_dcnv3'` or `No module named 'DCNv3'`
- `KeyError: InternImage is not in the backbone registry`
- `KeyError` for `CBInternImage`, `DINO`, `CBDINO`, `CBDINOHead`, `DinoTransformer`, `CBChannelMapper`, `CustomLayerDecayOptimizerConstructor`, `EfficientFFN`, or `CrowdHumanDataset`

Cause:

- The detection entrypoints import local `mmcv_custom` and `mmdet_custom` before building the model/dataset. Generic MMDetection CLIs do not do this automatically.
- Commands run from the wrong directory or without the repository root and detection directory on `PYTHONPATH` may not see local packages.
- DCNv3 has not been built/installed in the active Python environment, or the active environment is not the one used for the build.

Fix:

- Prefer commands emitted by `scripts/build_detection_command.py`; they change into `<repo-root>/detection` and set `PYTHONPATH=<repo-root>:<repo-root>/detection:...`.
- If adapting a command manually, preserve the custom imports or add equivalent `custom_imports` before config/model construction.
- Verify the active Python can import the intended OpenMMLab stack and local custom packages before launching long training or evaluation.

## DCNv3 CUDA extension failures

Symptoms:

- `NotImplementedError: Cuda is not availabel` during operator build.
- `CUDA_HOME is None`, missing `nvcc`, or PyTorch CUDA/toolkit mismatch.
- Runtime failure at the first InternImage backbone forward pass.
- DCNv4 config variant selected without a matching DCNv4 operator path.

Cause:

- The inspected `ops_dcnv3/setup.py` raises unless `torch.cuda.is_available()` is true and `CUDA_HOME` is present. A visible GPU through the driver is not enough if the CUDA toolkit/nvcc is unavailable.
- The compiled extension module is named `DCNv3` and must match the active Python, PyTorch, CUDA toolkit, and GPU driver.
- DCNv4 is optional source evidence and should not be assumed just because a config name contains `with_dcnv4`.

Fix:

- Check CUDA runtime and toolkit separately: PyTorch CUDA availability, `CUDA_HOME`, `nvcc -V`, and the PyTorch wheel CUDA tag.
- Use a compatible prebuilt DCNv3 wheel when available, or install a matching CUDA toolkit before source build.
- Route detailed operator build, TensorRT custom-op, or mmdeploy diagnosis to the deployment sub-skill.
- Do not claim full model runtime verification from command-builder checks alone.

## Test command rejected immediately

Symptoms:

- Assertion: `Please specify at least one operation ... with --out, --eval, --format-only, --show or --show-dir`.
- Error that `--eval` and `--format_only` cannot both be specified.
- Error that output file must be `.pkl` or `.pickle`.

Fix:

- Include an action: `--eval`, `--out`, `--format-only`, `--show`, or `--show-dir`.
- Use `--eval bbox segm` for COCO instance segmentation configs with mask heads.
- Use `--eval bbox` for COCO DINO/CB-DINO detection-only configs.
- Use `--eval mAP` for VOC/OpenImages-style configs when their evaluator expects mAP.
- Use `--format-only` only for submission-format outputs, and never combine it with `--eval`.
- Use `--out results.pkl` or `--out results.pickle` for pickled outputs.

## Wrong or missing evaluation output

Symptoms:

- No metric JSON appears where expected.
- Pickle output exists but metrics are absent.
- Painted images appear but metrics do not.

Explanation and fix:

- `--work-dir <dir>` controls where evaluation metric JSON is written; without evaluation there may be no metric JSON.
- `--out` dumps raw model outputs, not metric summaries.
- `--show-dir` saves visualizations and does not imply evaluation.
- `--format-only` can produce dataset-specific submission files without metrics.
- Distributed evaluation needs result collection through GPU collection or a CPU temp directory; mismatched collection options can hang or fail after inference.

## Checkpoint/config mismatch

Symptoms:

- Missing or unexpected checkpoint keys.
- Shape mismatch in bbox head, mask head, DINO class embedding, query tensors, or neck/backbone tensors.
- Classes or colors look wrong in demos.
- Evaluation metric is nonsensical for the selected dataset.

Fix:

- Match dataset, detector head, backbone size, and schedule/scale suffix. Example: use a COCO Mask R-CNN-T checkpoint with `coco/mask_rcnn_internimage_t_fpn_1x_coco`, not a classification pretrain checkpoint or DINO checkpoint.
- DINO/CB-DINO Objects365-to-dataset configs may contain `load_from` for training initialization; that is not a substitute for a local evaluation checkpoint.
- If checkpoint metadata lacks `CLASSES`, the source falls back to dataset classes from the config. Verify the selected dataset and class count explicitly.

## Dataset root or annotation layout failures

Symptoms:

- File-not-found under `data/coco`, `data/lvis_v1`, `data/OpenImages`, `data/VOCdevkit`, or `data/CrowdHuman`.
- The dataloader reports zero images or annotation parsing failures.
- CrowdHuman imports fail or annotations are still in `.odgt` form.

Fix:

- Check `references/config-catalog.md` for the selected dataset root and expected annotation/image files.
- Use `--cfg-options` only when you know the exact nested keys to override; changing just one split root may leave train/val/test inconsistent.
- For CrowdHuman, ensure annotations have been converted to `annotation_train.json` and `annotation_val.json` before using the custom dataset config.
- Do not start a full run until the data split and evaluator metric match the config family.

## Distributed launch problems

Symptoms:

- Port already in use.
- Hang at distributed initialization.
- `LOCAL_RANK` or launcher-related errors.
- Slurm flags accepted on one cluster but rejected on another.

Fix:

- For `dist-train`, change `--port` if the distilled default `63667` collides.
- For `dist-test`, change `--port` if the default `29511` collides.
- Ensure `--gpus` equals the intended per-node process count for `torch.distributed.launch --nproc_per_node`.
- Use `--launcher pytorch` only through the distributed command template; single-process commands should leave launcher as `none`.
- Slurm wrapping is site-specific. Preserve the source semantics: `--ntasks=<total GPUs>`, `--ntasks-per-node=<GPUS_PER_NODE>`, `--gres=gpu:<GPUS_PER_NODE>`, and pass `--launcher slurm` to `train.py` or `test.py`.

## Image demo issues

Symptoms:

- Output path is a directory when the user expected a file.
- Palette error for `cityscapes` or another unsupported name.
- Empty or low-quality detections.
- CPU device command fails despite being syntactically valid.

Fix:

- `image_demo.py --out` is an output directory; the result keeps the input basename inside that directory.
- Palette choices are exactly `coco`, `voc`, `citys`, and `random`. Use `citys`, not `cityscapes`, for the source parser.
- Lower `--score-thr` only if the detector/checkpoint/config pair is correct and the image is in-distribution.
- CPU execution depends on the installed OpenMMLab stack and operator behavior; GPU is the expected path for released InternImage detection models.

## SAM-specific failures

Symptoms:

- `ModuleNotFoundError: No module named 'segment_anything'`.
- SAM checkpoint load error or `sam_model_registry` key error.
- `NotImplementedError` after setting a distributed launcher.
- `NotImplementedError: WIP!` from the SAM engine path.
- `--data_type val` appears to have no effect.
- Debug marker lines print before a traceback.

Cause and fix:

- Install a compatible Segment Anything package and provide a SAM checkpoint whose family matches `--sam_type`.
- Keep SAM single-process. The inspected distributed branch raises `NotImplementedError`.
- Use a mask-capable detector config such as COCO Mask R-CNN/Cascade Mask R-CNN. The inspected SAM code checks `model.module.with_mask`; bbox-only DINO configs are risky without source changes.
- The inspected parser accepts `--data_type`, but the code does not use it to rewrite the dataloader. Use the config's intended test split or explicit `--cfg-options` with care.
- The debug marker prints are source noise; diagnose the traceback that follows.

## CUDA out of memory or very slow runs

Symptoms:

- OOM during config build, first forward pass, DINO inference, SAM image encoding, or mask visualization.
- Large H/G or CB-InternImage configs are infeasible on the available GPU memory.
- Test-time augmentation or large image scales are too slow.

Fix:

- Validate wiring with a smaller Mask R-CNN T/S/B config before running XL/H/G/CB-DINO models.
- Use smaller batch sizes or fewer workers only as deliberate config changes, and disclose that metrics are no longer directly comparable.
- For large InternImage configs, consider `with_cp=True` where the config/model supports it; expect slower runtime.
- Disable extra visualization/SAM outputs while diagnosing pure evaluation throughput.

## Export confusion

Symptoms:

- User asks to run `deploy.py`, TensorRT, ONNX, mmdeploy, custom backend conversion, or `mmdeploy::TRTDCNv3`.

Fix:

- Route to the deployment sub-skill. Detection export requires mmdeploy/TensorRT compatibility, DCNv3 custom symbolic/operator handling, deploy configs, checkpoint/model config pairing, and backend-specific runtime libraries. It is not ordinary detection evaluation.

## Source facts not runtime-verified here

The production verification for this generated sub-skill covered static source distillation and self-contained helper checks. It did not install or run full MMDetection, DCNv3 CUDA builds, dataset-scale training/evaluation, image-demo inference, SAM prompting, or TensorRT export. Treat those as optional native checks requiring a separately approved runtime environment.
