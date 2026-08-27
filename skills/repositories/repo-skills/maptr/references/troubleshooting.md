# MapTR cross-cutting troubleshooting

Use this reference after identifying the route-specific symptom. Stop rather
than silently downgrading a backend, changing an evaluator, or mixing an
unrelated OpenMMLab release.

| Symptom | Likely cause | Recovery | Stop condition |
|---|---|---|---|
| `MMCV==... is used but incompatible` | MapTR's pinned MMDetection/MMCV family is old and its version assertions are strict. | Recreate an isolated environment from the documented compatibility target; inspect all three versions together. Do not fix one package in-place by guessing. | The target cannot provide a compatible legacy stack and no user-approved port is defined. |
| `No module named mmcv._ext`, `..._cuda`, or `GeometricKernelAttention` | Compiled MMCV/MMDetection3D or MapTR custom extension is absent, built for a different torch/CUDA ABI, or not on the import path. | Verify torch/CUDA, `CUDA_HOME`/`nvcc`, compiler ABI, and extension import separately. Rebuild only in an isolated environment following the model-configuration compatibility route. | Do not claim model execution from a Python-only import or visible GPU. |
| `FileNotFoundError` for temporal info, maps, images, CAN bus, or checkpoint | Dataset conversion/layout or checkpoint placement is incomplete. | Run the bundled dataset layout checker; compare the expected generated names and config `data_root`/`ann_file`; obtain the checkpoint through the user's approved source. | Do not fabricate annotations, download private data, or start a long job while paths are unresolved. |
| Config loads but plugin classes are unknown | `plugin=True`, `plugin_dir`, `PYTHONPATH`, or registry import order is wrong. | Use the static config checker, confirm the plugin path is part of the target checkout's import path, then check the legacy framework versions. | A static config pass is not proof that compiled plugin imports work. |
| MapTR evaluation rejects `bbox` | Map-vector evaluation is not generic 3D box evaluation. | Use the MapTR vector metric contract, normally `chamfer`; inspect the dataset evaluator before selecting another metric. | If the task truly needs 3D boxes, route to a different dataset/config rather than coercing MapTR output. |
| Multi-GPU job hangs or oversubscribes devices | Requested process count, visible devices, launcher, port, or distributed environment is inconsistent. | Use the bundled dry-run launcher; make `--gpus`, visible-device count, port, and one-node assumptions explicit. Check logs before retrying. | Do not run eight processes on one device or reuse a busy port without review. |
| FPS or memory does not match README tables | Tables use particular GPUs, batch sizes, six-view inputs, image sizes, and model/config variants. | Record GPU model, torch/CUDA, batch size, view count, config, warm-up, measurement window, and whether data loading is included. | Do not compare values across variants as a model-quality claim. |
| Video helper emits no frames or codec errors | Visualization directories lack the expected camera/map images, names are mixed, or OpenCV has no MP4 writer. | Run the bundled video helper self-check, then validate a small fixture and output path. | Stop on real user data if images are missing or an output would overwrite artifacts without approval. |
| `Config.pretty_text` raises `FormatCode() got an unexpected keyword argument 'verify'` | The legacy MMCV config formatter is paired with a newer/incompatible YAPF release. | Prefer the bundled static checker for structural validation, or pin the formatter version from the documented legacy environment before using the pretty-printer. | Do not treat a formatter failure as a model/config semantic failure. |
| `No module named pycocotools` while asking for CLI help | The training/test modules import broad MMDetection dataset dependencies before parsing arguments. | Install the selected legacy dataset/runtime requirements or use the bundled dry-run/config helpers for parser-independent preflight. | Do not broaden installation to all optional extras merely to run help. |
| `av2` or `nuscenes` import fails | Optional dataset SDK is absent or incompatible with the legacy environment. | Install only the SDK for the selected dataset in an isolated environment and rerun a parser/import probe. | Do not run a full converter without the dataset license, data root, and resource budget. |

## Evidence discipline

Record exact package versions, config identity, dataset release, checkpoint
identity, visible devices, command, output directory, and failure fragment. Keep
`documented`, `inspected`, `native-passed`, `native-skipped`, and
`backend-blocked` labels separate. Full CUDA model execution remains blocked
until compiled MMCV and Geometric Kernel Attention are proven in the same ABI.
