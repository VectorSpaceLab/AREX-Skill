# Cross-Cutting Troubleshooting Router

## Purpose

Use this file to route a symptom to the nearest focused sub-skill. Then read that sub-skill's troubleshooting reference for concrete recovery steps.

| Symptom or request | Likely owner | First action |
| --- | --- | --- |
| `pip install -e .` says no `setup.py` or `pyproject.toml` | `installation-and-configuration` | Explain that the root is not installable and inspect `lib/setup.py` build path. |
| `nvcc` or `CUDAHOME` not found | `installation-and-configuration` | Run the environment checker; prepare a compatible CUDA/NVCC toolkit or narrow to source inspection. |
| `ModuleNotFoundError: nms.gpu_nms` or `nms.cpu_nms` | `installation-and-configuration` plus workflow owner | Build native extensions or explicitly choose a CPU/source-inspection limitation before demo/train/test. |
| TensorFlow import fails, `tensorflow.contrib` missing, protobuf descriptor error | `installation-and-configuration` | Use TensorFlow 1.x-compatible dependencies; do not run original repo unchanged on TensorFlow 2.x. |
| Unknown config key or type mismatch from `--set` | `installation-and-configuration` | Check `references/configuration.md` for exact keys and matching Python literal types. |
| `Unknown dataset: ...` | `dataset-and-assets` | Use exact registry keys or source-supported combined training strings. |
| VOC/COCO path assertion fails | `dataset-and-assets` | Validate `data/VOCdevkit<year>/VOC<year>` or COCO image/annotation layout. |
| Stale roidb/cache after data edits | `dataset-and-assets` | Remove relevant `data/cache/<imdb>_gt_roidb.pkl` files before rebuilding roidb. |
| Demo checkpoint `.meta` missing | `dataset-and-assets` then `inference-and-demo` | Validate model artifact layout, then build demo command. |
| OpenCV image read returns `None` | `inference-and-demo` | Check demo/custom image paths before `im_detect`. |
| Headless display or Matplotlib hang | `inference-and-demo` | Use a non-interactive backend or save figures instead of `plt.show()`. |
| ResNet101 memory pressure | `inference-and-demo` or `training-and-evaluation` | Use GPU memory growth, smaller images/models, or clearly documented CPU limitations. |
| Training starts from an old snapshot unexpectedly | `training-and-evaluation` | Check output/tag directory and snapshot `.ckpt`/`.pkl` files before deleting anything. |
| NaNs during training | `training-and-evaluation` | Check data boxes/classes, config overrides, learning rate/schedule, native backend, and README issue caveat. |
| AP numbers differ from README | `training-and-evaluation` | Confirm dataset split, checkpoint, NMS mode, thresholds, random/stochastic caveats, and native build correctness. |
| Anchor shape, bbox delta, RoI, or backbone modification confusion | `api-and-architecture` | Run the AST/source inspector and read architecture notes. |

## Stop conditions

Stop and ask for explicit user approval before:

- downloading large pretrained archives or datasets,
- launching full training/evaluation,
- installing or changing host-level CUDA/toolchains,
- mutating a user's existing environment or checkout to patch missing NMS modules,
- deleting output/checkpoint/cache directories.

## Known baseline limitation

The generated skill was verified for source-level and dry-run usability. Full native CUDA build, pretrained demo execution, training, testing, and AP reproduction remain target-host verification tasks.
