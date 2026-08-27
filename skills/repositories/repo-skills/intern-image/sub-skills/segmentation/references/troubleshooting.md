# Segmentation Troubleshooting

Use this for MMSegmentation 0.x InternImage segmentation failures. It distills source evidence from `segmentation/train.py`, `segmentation/test.py`, `segmentation/image_demo.py`, `segmentation/mmcv_custom`, `segmentation/mmseg_custom`, and `segmentation/ops_dcnv3`.

## Version and dependency mismatches

Symptoms:

- `ImportError` or registry errors after installing newer OpenMMLab packages.
- Configs fail with missing MMSeg/MMCV APIs, deprecated runner behavior, or incompatible data pipeline fields.
- `pip check` or import errors involving numpy, pydantic, mmcv, mmdet, or mmseg.

Likely cause and fix:

- This segmentation stack targets MMSegmentation `0.27.0`, `mmcv-full==1.5.0`, `mmdet==2.28.1`, PyTorch with CUDA, `timm==0.6.11`, `numpy<2.0`, and `pydantic==1.10.13` according to source evidence.
- Do not silently move these configs to MMSegmentation 1.x/2.x. If a user is on a modern stack, tell them this is a migration task rather than an ordinary InternImage run.
- Use a fresh environment if the current environment already has incompatible OpenMMLab packages.

## Custom module and registry failures

Symptoms:

- `ModuleNotFoundError: No module named 'mmcv_custom'`
- `ModuleNotFoundError: No module named 'mmseg_custom'`
- `ModuleNotFoundError: No module named 'ops_dcnv3'` or `No module named 'DCNv3'`
- `KeyError: InternImage is not in the backbone registry`
- `KeyError` for `CustomLayerDecayOptimizerConstructor`, `EncoderDecoderMask2Former`, `Mask2FormerHead`, `MapillaryDataset`, or `NYUDepthV2Dataset`

Likely cause:

- The segmentation entrypoints import `mmcv_custom` and `mmseg_custom` before building configs. Generic MMSeg tools will not register InternImage components unless equivalent imports are preserved.
- Commands run from the wrong directory or without the repo root on `PYTHONPATH` may not see local custom modules.
- DCNv3 has not been built/installed for the active Python environment.

Fix:

- Prefer commands emitted by `scripts/build_segmentation_command.py`; they change into `<repo-root>/segmentation` and set `PYTHONPATH=<repo-root>:...`.
- If adapting a custom command, preserve the imports or add equivalent MMSeg `custom_imports` before model/dataset construction.
- Verify the active Python environment can import the OpenMMLab stack and local custom packages before launching a long run.

## DCNv3 CUDA extension failures

Symptoms:

- `NotImplementedError: Cuda is not availabel` during operator build.
- `CUDA_HOME is None`, `nvcc` missing, or a PyTorch CUDA/toolkit version mismatch.
- Runtime failures when constructing the InternImage backbone or running the first forward pass.

Likely cause:

- The source `ops_dcnv3/setup.py` raises when `torch.cuda.is_available()` is false or `CUDA_HOME` is missing. A visible GPU is not sufficient if the CUDA toolkit/nvcc is unavailable.
- The operator build must match the Python environment, PyTorch version, CUDA toolkit, and GPU driver.

Fix:

- Check CUDA runtime and toolkit separately: PyTorch CUDA availability, `CUDA_HOME`, `nvcc -V`, and the PyTorch wheel CUDA tag.
- Use a compatible prebuilt DCNv3 wheel when available for the target environment, or install a matching CUDA toolkit before building.
- Do not claim CPU runtime verification for DCNv3-heavy model execution unless the specific installed operator path was actually tested. Command-builder checks are parser/static checks only.

## Evaluation command rejected immediately

Symptoms:

- Assertion: `Please specify at least one operation ... with --out, --eval, --format-only, --show or --show-dir`.
- Error that `--eval` and `--format_only` cannot both be specified.
- Error that output file must be `.pkl` or `.pickle`.

Fix:

- For metric evaluation, include `--eval mIoU` for ADE20K, COCO-Stuff, Mapillary, NYU, Pascal-Context, or ordinary Cityscapes mIoU reporting.
- For Cityscapes official-style formatting/evaluation, use `--eval cityscapes` alone and pass an `imgfile_prefix` through `--eval-options` if you need to control the formatted directory.
- Use `--format-only` only when preparing server-format output without metrics.
- Use `--out results.pkl` or `--out results.pickle` for pickled outputs.
- The bundled builder defaults test modes to `--eval mIoU` only when no output/eval/show/format action is provided.

## Wrong or missing evaluation output

Symptoms:

- No JSON appears where expected.
- Pickle exists but does not contain a simple class-map array.
- Cityscapes temp directory appears unexpectedly.

Explanation and fix:

- `test.py --work-dir <dir>` writes evaluation metric JSON there. Without `--work-dir`, it writes below `./work_dirs/<config-stem>` from the segmentation working directory.
- `--out` behavior follows MMSeg 0.x and may dump segmentation maps, pre-eval tuples, or file paths from `dataset.format_results()` depending on the metric and format mode.
- Cityscapes evaluation through formatted results uses `.format_cityscapes` by default unless `--eval-options imgfile_prefix=<dir>` is supplied; the source removes the temp directory after Cityscapes eval.

## Image demo palette or output looks wrong

Symptoms:

- Demo runs but colors look unrelated to the dataset.
- A directory demo silently skips some files.
- Output is a directory even when the user expected a file.
- Error for unsupported palette such as `mapillary`, `nyu`, or `pascal`.

Cause and fix:

- The native demo parser allows only `ade20k`, `cityscapes`, and `cocostuff` palettes.
- The demo always writes to an output directory, default `demo`, preserving each input image basename.
- Directory mode only processes file names ending in `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, or `.gif` and skips other entries.
- If checkpoint metadata lacks `CLASSES`, classes fall back to `get_classes(--palette)`; colors are always `get_palette(--palette)`. Use ADE20K/Cityscapes/COCO-Stuff demo cases unless the user intentionally adapts the demo for Mapillary/NYU/Pascal palettes.
- Keep `--opacity` in `(0, 1]`; low opacity hides masks, high opacity hides the original image.

## Checkpoint/config mismatch

Symptoms:

- Missing or unexpected keys during checkpoint load.
- Shape mismatch in decode head, auxiliary head, class embedding, or Mask2Former query/head tensors.
- Nonsensical classes or colors.

Fix:

- Match dataset, head family, resolution, and backbone size: e.g. `upernet_internimage_t_512_160k_ade20k.py` with the corresponding ADE20K UperNet-T checkpoint.
- Remember ADE20K Mask2Former `_ss` and `_ms` configs share the release checkpoint name without `_ss`/`_ms` in source evidence.
- Do not use an ImageNet classification checkpoint as an evaluation checkpoint for `test.py`; classification pretraining belongs in config `init_cfg` or training initialization, not segmentation evaluation output.

## Dataset root or annotation layout failures

Symptoms:

- File-not-found under `data/ADEChallengeData2016`, `data/cityscapes`, `data/coco_stuff164k`, `data/coco_stuff10k`, `data/Mapillary`, `data/nyu_depth_v2`, or `data/VOCdevkit/VOC2010`.
- Train/eval starts but reports zero images or annotation suffix mismatches.

Fix:

- Check the dataset base table in `references/config-catalog.md` and either arrange the dataset under the expected relative data root or use careful `--cfg-options` overrides for the nested `data.*.data_root` fields.
- For custom datasets such as Mapillary and NYU-Depth-V2, ensure `mmseg_custom` registration happens before config build.
- Do not start a full run until the dataset split and annotation suffix are known to match the selected config.

## Distributed launch problems

Symptoms:

- Port already in use.
- Hang at distributed initialization.
- `LOCAL_RANK` or launcher-related errors.
- Slurm flags accepted on one cluster but rejected on another.

Fix:

- For `dist-train`, set `--port` if the default `29300` collides. For `dist-test`, set `--port` if the default `29510` collides.
- Ensure `--gpus` equals the intended per-node process count for the generated `torch.distributed.launch --nproc_per_node` command.
- Use `--launcher pytorch` only through the distributed command; single-process commands should leave launcher as `none`.
- Slurm launchers are not bundled because partition/quota flags are site-specific. When using Slurm, preserve the source semantics: `--ntasks=<total GPUs>`, `--ntasks-per-node=<GPUS_PER_NODE>`, `--gres=gpu:<GPUS_PER_NODE>`, and pass `--launcher slurm` into `train.py` or `test.py`.

## CUDA out of memory or very slow runs

Symptoms:

- OOM during build, forward, or test-time augmentation.
- InternImage-H/G or Mask2Former configs are infeasible on the available GPU memory.
- Evaluation succeeds single-scale but OOMs with `--aug-test`.

Fix:

- First validate the workflow with a smaller UperNet T/S/B config.
- Disable `--aug-test` for memory-limited evaluation.
- Prefer distributed training for configs written for SyncBN/DDP.
- Use or set `with_cp=True` only when the config and model variant support it; expect extra compute time.
- Reduce crop size or batch-size fields only as an intentional config change and disclose that reported metrics are no longer directly comparable to released numbers.

## Source facts not runtime-verified here

The production environment prepared for this skill supports CPU-safe inspection and helper-script checks. It did not install the full torch/mmcv/mmseg/DCNv3/mmdeploy/TensorRT GPU runtime for segmentation. Treat full training, evaluation, image-demo inference, and DCNv3 numerical tests as optional native checks that require a separately approved GPU/OpenMMLab environment.
