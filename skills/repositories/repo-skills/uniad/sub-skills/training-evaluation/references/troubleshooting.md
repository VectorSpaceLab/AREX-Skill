# Training/evaluation troubleshooting

## Source evidence

This reference is distilled from `README.md`, `docs/INSTALL.md`, `docs/DATA_PREP.md`, `docs/TRAIN_EVAL.md`, `tools/train.py`, `tools/test.py`, the bundled launcher scripts, and the environment report for this checkout.

## Symptom map

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `FileNotFoundError` for a `.pth` checkpoint | The checkpoint is not in `ckpts/` or the path in the config / CLI is wrong | Put the file under `ckpts/` or pass the correct absolute path. For stage1 train, the expected parent checkpoint is `ckpts/bevformer_r101_dcn_24ep.pth`; for stage2 train, it is `ckpts/uniad_base_track_map.pth`. |
| Dataset or ann-file errors for `data/infos/...` or motion anchors | The dataset layout is incomplete | Route the layout problem to the data-preparation sub-skill. Training/eval here assumes the nuScenes info PKLs and motion-anchor file already exist. |
| `AssertionError` or immediate failure from `tools/test.py` without a distributed launcher | Non-distributed evaluation is disabled in the script | Use `torchrun`, `srun`, or the bundled distributed/SLURM launcher. Do not try `--launcher none` for evaluation. |
| `--gpus` or `--gpu-ids` seem ignored | The run is distributed | Those flags only affect the non-distributed branch of `tools/train.py`. The launcher wrappers use `torchrun` or `srun`, so the launcher is controlled elsewhere. |
| `--work-dir` appears to be ignored when using a shell wrapper | The wrapper appends its own `--work-dir` later | The bundled wrappers hard-code their own derived work dir after user extras, so wrapper-owned values win. Edit the wrapper or call `tools/train.py` / `tools/test.py` directly if you need a different work dir. |
| `--eval bbox` or `--show-dir` appears to be ignored when using a shell wrapper | The wrapper appends its own defaults later | The bundled evaluation wrappers pin those values after user extras. Use `tools/test.py` directly if you want different evaluation or output behavior. |
| Shell parsing errors for `--cfg-options` | List or tuple values were not quoted | Quote the whole assignment, for example `--cfg-options model.queue_length=3` or `--cfg-options something="[(a,b),(c,d)]"`. Avoid spaces inside the value string. |
| Training starts from the wrong checkpoint | `load_from` and `resume-from` were confused | Use `load_from` for initialization and `--resume-from` only when resuming optimizer/scheduler state from an existing checkpoint file. |
| Work dir / log file cannot be found | The config-derived work dir differs from where you looked | The wrappers write under `projects/work_dirs/<config-path-with-configs-replaced-by-work_dirs>/logs/`. Direct `train.py` defaults to `./work_dirs/<config-basename>` only when the config and CLI leave `work_dir` unset. |
| Metrics differ slightly from the README table | Different GPU count or launch topology | The docs explicitly warn that evaluation with a GPU count other than 8 can shift results slightly. Recheck the checkpoint, data, and launch size before assuming a regression. |
| Import or CUDA-op failures around MMCV / PyTorch | Torch, CUDA, or MMCV wheel mismatch | Compare the installed stack against the public v2.0 versions in `references/runtime-and-gpu.md`. The known inspection-only stack in the environment report is not the published target. |
| `pip check` reports a `networkx` conflict | Known metadata mismatch between `mmdet3d` and the repo requirements pin | Treat it as a packaging caveat for this checkout, not as evidence that the training/eval command builder is wrong. |
| Stage1 uses too much memory | Queue length is too high for the card | Stage1 can be reduced from `queue_length=5` to `queue_length=3` for a memory-saving compromise, with a small tracking-performance drop. |
| Need a run on fewer than 8 GPUs | The docs recommend 8 but do not require it | Use the bundled launcher with the smaller GPU count, expect longer runtime, and do not demand the exact 8-GPU metric target. |

## Common recovery sequence

1. Confirm the checkpoint file exists where the config or wrapper expects it.
2. Confirm the dataset info PKLs and motion-anchor file exist if the run needs them.
3. Confirm the launcher is distributed for evaluation.
4. Confirm the command line quoting for `--cfg-options`.
5. Confirm the installed Torch/MMCV/OpenMMLab stack matches the public target or an explicitly documented inspection stack.
6. Re-run the command from the repo root so the relative `projects/` and `ckpts/` paths resolve as intended.

## What not to do

- Do not interpret the evaluation wrapper's defaults as user-overridable unless you modify the wrapper itself.
- Do not use `tools/test.py --launcher none` as a normal evaluation path; it is intentionally blocked.
- Do not call a metric mismatch a failure until you have checked the GPU count and the checkpoint path.
