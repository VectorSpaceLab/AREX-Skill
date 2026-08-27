# Model/config troubleshooting

Use this matrix to classify failures before changing a model. Keep the original
error, config summary, package versions, device, and whether compiled extensions
were imported in the handoff.

## Install and import

| Symptom | Likely cause | Action |
|---|---|---|
| `mmcv` import or API attribute failure | wrong MMCV generation | use the pinned legacy contract: PyTorch 1.1+ and `mmcv==0.2.16`; modern MMCV APIs are not drop-in replacements |
| `ModuleNotFoundError: torch`, `mmcv`, `pycocotools`, or `Cython` | incomplete runtime/build/test dependency set | install into an isolated approved environment; distinguish runtime, build, optional, and test dependencies |
| missing `mmdet.ops.*.so` / `ImportError` for `nms_cpu`, `nms_cuda`, `deform_conv_cuda`, `roi_align_cuda`, `roi_pool_cuda`, `sigmoid_focal_loss_cuda`, or `masked_conv2d_cuda` | extensions were not built, or were built for another torch/CUDA/ABI/toolchain | rebuild the package against the active compatible PyTorch/CUDA/compiler; do not copy `.so` files into the skill |
| setup aborts with `CUDA is required to compile MMDetection!` | this setup snapshot makes CUDA extensions mandatory during installation | use a compatible CUDA build environment or treat the model/op path as blocked; a CPU-only package install is not implied by the Python code |
| `undefined symbol`, illegal instruction, or kernel launch failure | binary ABI, CUDA, compiler, or GPU architecture mismatch | cleanly rebuild against the active stack; do not infer that a CPU import proves CUDA works |
| `pycocotools` failure during detector import | COCO mask support is imported by `BaseDetector` and inference utilities | install a compatible pycocotools build; this is separate from model registry correctness |

The repository documents Linux, Python 3.5+, CUDA 9+, NCCL 2, GCC 4.9+, PyTorch
1.1+, and legacy MMCV 0.2.16. It notes that newer PyTorch versions were not tested
in the historical install guide. Treat these as compatibility constraints, not a
current installation recommendation.

## Optional dependencies

- `albumentations` and `imagecorruptions` are optional and only needed for the
  corresponding pipeline/features. Their absence should not be misdiagnosed as a
  registry failure unless the selected config names one.
- `xdoctest`, `pytest`, `kwarray`, and formatting tools are test extras. A native
  test can be blocked by test-only dependencies even when model construction is
  available.
- `torchvision` supplies the historical `torchvision://resnet*` pretrained
  convention, but offline construction should set `model.pretrained=None`.
- Visualization paths additionally use OpenCV/matplotlib and mask decoding. Keep
  them out of a minimal model-build check.

## Config and data validation

| Symptom | Check |
|---|---|
| unknown registry type | class is registered and imported by the package initializer; the `type` spelling is exact |
| constructor got unexpected keyword | inspect the target class signature; legacy `build_from_cfg` passes remaining keys directly |
| list index/channel/shape errors | compare backbone `out_indices` and emitted channels with neck `in_channels`, neck `num_outs`, and head `in_channels` |
| SOLO loss lacks masks or keys | training pipeline must load masks and collect `gt_masks` in addition to boxes/labels |
| SOLOv2 kernel/mask shape error | align `bbox_head.ins_out_channels` with `MaskFeatHead` output/kernel width and feature resolution |
| empty or nonsensical results | check `num_classes` label convention, test score/mask thresholds, image metadata, and checkpoint/class names |
| data files not found | `data_root`, annotation file, and image prefix are config-specific environment inputs; validate them without embedding local paths |
| config parses but build fails | parsing Python is weaker than construction; use a compatible `mmcv.Config` plus `build_detector` smoke test |

The safe inspector intentionally does not resolve `_base_` composition or execute
expressions/imports. If the summary reports an unresolved expression, load the
config only in a sandboxed, compatible environment and inspect the resulting
`mmcv.Config` without checkpoints or data downloads.

## API and CLI misuse

- `init_detector` accepts a filename or `mmcv.Config`, not an arbitrary dict.
  It sets `pretrained=None` before building and uses `test_cfg`; checkpoint load
  is optional but required for meaningful inference.
- `inference_detector` requires a model initialized with its `cfg` and accepts a
  path or image array. It follows the configured normalization/resize pipeline.
- `BaseDetector.forward(return_loss=True)` uses training nesting; with
  `return_loss=False`, `img` and `img_meta` must be augmentation-nested lists.
  Passing a single tensor to test mode triggers the explicit type checks.
- Non-distributed `train_detector(..., validate=True)` raises
  `NotImplementedError` in this snapshot. Use the distributed validation path or
  the separate test/eval tools when authorized.
- Historical training CLI defaults to one GPU, but many released configs encode an
  8-GPU learning-rate/batch-size assumption. `--autoscale-lr` scales the config
  learning rate by `gpus / 8`; make this an explicit choice.
- `resume_from` restores optimizer state/epoch; `load_from` loads weights and
  starts the epoch count from zero. Do not confuse fine-tuning with resuming.
- `--eval` choices include `proposal`, `proposal_fast`, `bbox`, `segm`, and
  `keypoints`; instance segmentation configs generally need `segm`.

## Workflow-specific failures

| Failure | Interpretation and next step |
|---|---|
| CPU NMS test passes but DCN forward fails | expected separation: CPU NMS does not validate custom CUDA kernels; classify DCN as blocked until CUDA forward is run |
| NMS import fails before a CPU test | setup builds even NMS CPU/CUDA extension modules in this snapshot; rebuild or block, rather than replacing compiled code casually |
| DCN config builds only after removing `dcn` | the modified config no longer tests the intended architecture; record it as a non-DCN fallback, not a successful DCN verification |
| FP16 run produces NaN or dtype error | verify FP16 hook, scaling, normalization patch, and each custom module's dtype boundary; test with decorators only on module methods |
| SOLOv2 scores collapse after changing `kernel` | only `gaussian` and `linear` matrix-NMS kernels are supported; `sigma` affects Gaussian decay and `update_thr` filters updated scores |
| `aug_test` is unavailable for SOLO/SOLOv2 | `SingleStageInsDetector.aug_test` explicitly raises `NotImplementedError` in this snapshot; use single-scale inference or implement and verify an augmentation contract |
| full training exhausts memory or never finishes | outside this sub-skill's native acceptance; use a bounded forward/build candidate and report training unverified |
| config construction passes but inference is wrong | construction proves registry/constructor compatibility only; verify pipeline metadata, checkpoint class names, output post-processing, and a real checkpoint separately |

## Safety exclusions

Do not adapt distributed training launchers, data-download scripts, dataset
conversion, visualization, checkpoint publishing, or source-mutating setup code
into this runtime skill. They can be consulted for interface facts but require
network, credentials, GPUs, long runtimes, or write access. Do not copy compiled
C++/CUDA/Cython sources or binaries. Rebuilding extensions is an environment
operation and must be performed by approved setup tooling outside this subtree.
