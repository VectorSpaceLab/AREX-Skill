# Troubleshooting training and evaluation

Use the smallest diagnostic that distinguishes an environment, path/config,
data, backend, or experiment failure. Keep the command and first traceback.
Do not repeatedly retry an unresolved required-backend failure.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named torch`, `mmcv`, `mmdet`, or `pycocotools` | wrong environment or incomplete legacy install | Activate the approved environment; check `python -c "import torch, mmcv, mmdet"`; verify the documented PyTorch 1.1+ / `mmcv==0.2.16` compatibility contract and package versions. |
| Import fails in a custom op or shared object | package was not built for the active PyTorch/CUDA ABI | Reinstall/rebuild the repository package in the same environment, inspect the first linker/ABI error, and confirm CUDA toolkit/compiler availability. CPU import does not prove CUDA kernels work. |
| `torch.cuda.is_available()` is false | CPU-only PyTorch, driver/runtime mismatch, hidden GPU, or bad `CUDA_VISIBLE_DEVICES` | Check device visibility and PyTorch CUDA build; use a compatible CUDA environment. Do not claim full workflow support from a CPU fallback. |
| `mmcv` API/config error | modern MMCV/MMDetection installed against v1-era code | Pin/use the documented legacy family or explicitly port the config/script; do not mix versions silently. |
| `imagecorruptions` or `robustness_eval` missing | optional robustness dependency omitted | Install only with approval in the target environment, or omit robustness rather than replacing it. |
| model/data install or artifact download times out | network, mirror, or permission failure | Do not retry indefinitely or download implicitly. Use an approved local cache/mirror or user-supplied artifact, verify its checksum/size, and record the network failure as an unresolved prerequisite if none is available. |
| Matplotlib/seaborn import failure | optional log plotting dependency missing | Use bundled `scripts/analyze_log.py` for summary/CSV; install plotting dependencies only when plotting is required. |

Required version evidence is the installation documentation: Linux,
Python 3.5+, PyTorch 1.1+, CUDA 9.0+, NCCL 2, GCC 4.9+, and mmcv 0.2.16.
The project states PyTorch >=1.5 was not tested. Treat newer combinations as
uncertain until import and focused behavior checks pass.

## Data and config validation

| Symptom | Likely cause | Recovery |
|---|---|---|
| config file not found or syntax/import error | wrong local path, missing parent, or unsupported config code | Use an absolute user-supplied config path; inspect parent/inheritance files and parse in the target environment. |
| annotation/image `FileNotFoundError` | `data_root`, `ann_file`, or `img_prefix` still points at the example layout | Rewrite to the user's local dataset root; verify every split path and filename before launching. |
| empty dataset or zero iterations | annotation split mismatch, bad image prefix, or filtering removed all samples | Check annotation ids, image existence, class ids, and dataset length with a bounded local inspection. |
| `KeyError` for `gt_masks`, `gt_bboxes`, or `img` | pipeline `Collect`/annotation flags do not match model task | For SOLO training, include image plus bbox/label/mask targets; for test, use the model's expected test pipeline. |
| class index/shape mismatch | config `num_classes` or dataset classes differ from checkpoint/data | Align class order and count; do not rely only on old-checkpoint metadata fallback. |
| config works in a newer project but not here | v1-era API and config syntax mismatch | Use a config proven against this legacy package, or port it explicitly and record the changes. |
| inherited config appears ignored | loader does not support the assumed `_base_` semantics | Resolve the full effective config and use explicit local overrides. |

The documented COCO layout expects `annotations`, `train2017`, `val2017`, and
optionally `test2017` under the configured dataset root. Cityscapes requires a
separate conversion to COCO format. Never download or convert data as an
implicit recovery action.

## CLI and API misuse

| Symptom | Likely cause | Recovery |
|---|---|---|
| evaluator asserts no output operation | `tools/test.py`/`test_ins.py` requires `--out`, `--show`, or JSON output | In headless reproducible runs, pass a writable `.pkl` via `--out`; add `--eval` for metrics. |
| output extension rejected | legacy evaluator accepts `.pkl`/`.pickle` | Rename/use a path with one of those extensions. |
| invalid `--eval` value | metric is not in the parser choices or incompatible with task | Use `proposal`, `proposal_fast`, `bbox`, `segm`, or `keypoints` only when the dataset/model supports it. |
| `--show` cannot connect to X server | no GUI/display | Remove `--show` and save results; use a separate reviewed visualization workflow. |
| `--json_out` behaves unexpectedly in `tools/test_ins.py` | source-era parser/implementation inconsistency | Prefer `--out`; inspect the exact script before relying on JSON output. |
| help command fails during import | dependencies load before argparse exits | Fix/import-check the environment; help is not a dependency-free parser test. |
| `get_flops.py` says no `forward_dummy` | model family has no supported dummy forward | Stop FLOPs measurement or use a separately validated complexity method; do not approximate silently. |
| output exists but metrics are absent | `--eval` omitted, wrong output type, or dataset evaluator unavailable | Re-run only after confirming output format and evaluator support. |

## Training and checkpoint failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA out-of-memory | image size, model, workers, or per-GPU batch too large | Stop; reduce `imgs_per_gpu`/shape/workers or choose a smaller model, then restart in a new work directory. Do not assume partial optimizer state is safe. |
| loss is NaN/Inf or explodes | bad annotations, invalid augmentation, FP16 scale, LR/batch mismatch, or custom-op failure | Stop at first persistent non-finite signal; inspect data/config and run a bounded non-FP16 or lower-LR diagnostic only with approval. |
| resume starts at wrong epoch or optimizer state is absent | `load_from` used instead of `resume_from`, or checkpoint is incomplete | Check checkpoint metadata and use the correct semantic; do not append epochs manually without recording it. |
| checkpoint loads but inference shape/class errors | config/checkpoint architecture or class mapping mismatch | Pair the original model/head and preprocessing; inspect metadata and class order. |
| no checkpoints/logs | unwritable `work_dir`, early crash, or wrong rank output assumption | Check permissions and rank-0 logs; use a fresh writable directory and preserve the failing trace. |
| validation hangs or fails after training step | bad val data/evaluator, distributed barrier mismatch, or unsupported metric | Disable validation only for a diagnostic run, then fix the val path/protocol before accepting training. |

Training is expensive and usually CUDA/data dependent. Do not start a complete
1x/3x schedule as an installation test.

## Distributed, FP16, robustness, and FLOPs failures

- **NCCL/process hang**: verify one process per visible GPU, consistent
  `CUDA_VISIBLE_DEVICES`, unique port per concurrent job, shared paths, and
  matching launcher/backend. Kill the failed process group before retrying.
- **Temporary collection failure**: ensure `--tmpdir` is shared/writable and
  has enough space; choose CPU temporary collection or GPU collection according
  to the environment. Only rank 0 should finalize output.
- **FP16 instability**: configs under `configs/fp16/` use an `fp16` block and
  evaluation wraps the model when present. FP16 can change overflow behavior;
  compare against a full-precision bounded run and stop on NaN/Inf. It does not
  remove the need for a compatible CUDA/custom-op environment.
- **Robustness missing transform/dependency**: verify optional packages,
  corruption name, integer severity 0–5, and pipeline insertion after image
  loading. First prove clean evaluation, then one corruption/severity.
- **Robustness too slow**: reduce corruptions/severities and dataset scope
  under an explicit experiment plan. The documented workflow is single-GPU;
  do not assume distributed aggregation is correct.
- **FLOPs OOM or implausible count**: reduce input shape, check
  `forward_dummy`, report unsupported GN/custom operators and proposal
  dependence, and compare only like-for-like configurations.

## Recovery stop conditions

Stop and report a blocked/partial result when any of these remains unresolved:
missing required CUDA/custom-op support; unreadable or mismatched checkpoint;
missing annotation/image split; class mapping uncertainty; distributed ranks
cannot form a stable process group; repeated non-finite loss; output/metric
protocol cannot be reconstructed; or the optional robustness dependency/data
cannot be supplied. A CPU config parse or tiny log parse may still be reported
as a partial check, never as proof of end-to-end capability.
