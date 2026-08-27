# Train and Test Workflows

This reference distills MMSegmentation training and testing launch behavior into self-contained wrapper commands and decision checks. It documents the upstream entry-point semantics while routing runnable examples through bundled skill scripts.

## Training Entry Point Semantics

MMSegmentation training starts from a config file and builds an MMEngine runner. The bundled wrapper mirrors the public training flags and is safe by default:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG [--work-dir WORK_DIR] [--resume] [--amp] [--cfg-options KEY=VALUE ...]
```

Add `--execute` only when the user explicitly approves an actual training run:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --work-dir work_dirs/debug --max-iters 10 --execute
```

Runtime behavior confirmed from the upstream training entry point and mirrored by the wrapper:

- `CONFIG` is loaded with `mmengine.config.Config.fromfile`.
- `--cfg-options` is merged into the config before building the runner.
- `cfg.launcher` is set from `--launcher`; default is `none`.
- `--work-dir` overrides `cfg.work_dir`; if neither is set, the default is `./work_dirs/<config-basename>`.
- `--amp` changes `cfg.optim_wrapper.type` from `OptimWrapper` to `AmpOptimWrapper` and sets `loss_scale='dynamic'`; it warns if AMP is already enabled and asserts if the wrapper type is not `OptimWrapper` or `AmpOptimWrapper`.
- `--resume` sets `cfg.resume=True`.
- If `runner_type` is absent, the command builds `Runner.from_cfg(cfg)`; otherwise it builds a custom runner from `mmseg.registry.RUNNERS`.
- Training starts with `runner.train()` only after `--execute`.

## Resume, Fine-Tune, and Checkpoint Loading

Treat these as distinct workflows:

- Interrupted-run resume: use `--resume`; MMSegmentation resumes from the latest checkpoint in `work_dir` and keeps optimizer/scheduler state.
- Resume from a specific checkpoint: use both `--resume` and `--cfg-options load_from=CHECKPOINT`; this tells the runner which checkpoint to resume while preserving resume semantics.
- Fine-tune from a checkpoint: set `load_from=CHECKPOINT` without `--resume`; training starts from iteration 0 with initialized weights from the checkpoint.
- Plain test/eval: pass the checkpoint as the second positional argument to the testing workflow; the runner assigns it to `cfg.load_from` before `runner.test()`.

Before suggesting `--resume`, verify that `work_dir` points at the run with the intended `latest.pth` or checkpoint metadata. Before suggesting `load_from`, verify that the user is not trying to continue optimizer state.

## Testing Entry Point Semantics

MMSegmentation testing starts from a config file plus checkpoint. The bundled wrapper mirrors the public testing flags and is safe by default:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT [--work-dir WORK_DIR] [--out OUTPUT_DIR] [--show] [--show-dir SHOW_DIR] [--wait-time SECONDS] [--cfg-options KEY=VALUE ...] [--tta]
```

Add `--execute` only when the user explicitly approves an actual test run:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --tta --show-dir work_dirs/vis --execute
```

Runtime behavior confirmed from the upstream testing entry point and mirrored by the wrapper:

- `CONFIG` is loaded and `--cfg-options` is merged before runner construction.
- `cfg.launcher` is set from `--launcher`; default is `none`.
- `--work-dir` overrides `cfg.work_dir`; otherwise it falls back to `./work_dirs/<config-basename>` when unset.
- The positional `CHECKPOINT` is assigned to `cfg.load_from`.
- `--show` or `--show-dir` turns on the configured visualization hook by setting `default_hooks.visualization.draw=True`; `--show` also sets `show=True` and `wait_time`, while `--show-dir` sets `cfg.visualizer.save_dir`.
- `--tta` replaces `cfg.model` with `cfg.tta_model` and swaps the test pipeline to `cfg.tta_pipeline`.
- `--out OUTPUT_DIR` sets `cfg.test_evaluator.output_dir=OUTPUT_DIR` and `cfg.test_evaluator.keep_results=True` before `Runner.from_cfg(cfg)` and `runner.test()`.

## Output Formatting and Hidden-Test Submissions

Use `--out OUTPUT_DIR` when predictions need to be saved for offline evaluation or submission. For `IoUMetric`, this writes PNG masks under the evaluator output directory; `reduce_zero_label=True` predictions are shifted by one before saving. For `DepthMetric`, this writes depth PNGs after applying `depth_scale_factor`.

When test labels are unavailable, do not try to evaluate metrics. Configure the test evaluator with `format_only=True` and an `output_dir`, and remove annotation loading from the test pipeline if the dataset truly has no annotations. For Cityscapes-style submission formatting, `CityscapesMetric` additionally requires `keep_results=True` when `format_only=True`.

Bundled-wrapper override patterns:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --out work_dirs/format_results
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --out work_dirs/format_results
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --keep-results --cfg-options test_evaluator.output_dir=work_dirs/cityscapes_submit
```

Add `--execute` only after checking that the config, checkpoint, and output mode are correct.

## Visualization During Testing

Use one of:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --show-dir work_dirs/visualizations
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --show
```

The config must include `default_hooks.visualization`; otherwise the testing workflow raises a runtime error about the missing visualization hook. `--show` opens a display window and is inappropriate for headless CI or remote servers unless a display backend is configured. `--show-dir` is safer for servers because it saves rendered outputs through the visualizer.

## Test-Time Augmentation

Use `--tta` only when the config defines both `tta_pipeline` and `tta_model`. The test workflow assigns:

```python
cfg.test_dataloader.dataset.pipeline = cfg.tta_pipeline
cfg.tta_model.module = cfg.model
cfg.model = cfg.tta_model
```

If these config fields are missing, add or select a TTA-ready config instead of forcing the flag.

## Runner API Workflow

When a script or notebook needs direct runner control, mirror the CLI sequence:

```python
from mmengine.config import Config
from mmengine.runner import Runner

cfg = Config.fromfile('CONFIG.py')
cfg.work_dir = 'work_dirs/debug'
cfg.load_from = 'CHECKPOINT.pth'  # for testing/fine-tuning as appropriate
runner = Runner.from_cfg(cfg)
runner.train()  # or runner.test()
```

For training, set `cfg.resume=True` only for continuation from an interrupted run. For testing, ensure `test_dataloader`, `test_evaluator`, and `test_cfg` exist before `Runner.from_cfg(cfg)`.

## CPU, CUDA, and NPU Notes

- If no CUDA device is available, single-process CPU training/testing follows the same wrapper shape but may be very slow and can expose SyncBatchNorm or operator limitations depending on the model.
- To force CPU on a GPU machine, set `CUDA_VISIBLE_DEVICES=-1` before the wrapper command.
- NPU launch uses the same single-process or distributed wrapper shapes after the NPU-compatible MMCV/backend stack is installed.

## Safe Checks

Prefer these before long runs:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py --help
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py --help
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --max-iters 1
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --out work_dirs/format_results
```

For behavior beyond help text, use a tiny config and explicit bounds such as `--max-iters 1`, reduced dataloader workers, and a temporary work directory. Do not run full configs, distributed jobs, or benchmarks without user approval.
