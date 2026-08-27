# Tracking and Evaluation Workflows

## When to Read

Read this when running SiamMask inference, benchmark tests, VOT metrics, or hyperparameter searches from a checkout.

## Interactive Demo Flow

Use this when the user wants to visualize tracking on an image sequence and manually select the first-frame ROI.

1. Verify environment and build extensions from the root skill.
2. Choose an experiment. `siammask_sharp` is the default for the DAVIS/VOT pretrained checkpoints and refined masks.
3. Make sure the checkpoint and config are accessible from the experiment directory, or pass absolute paths.
4. Use the bundled helper in dry-run mode:

   ```bash
   python scripts/run_tracking.py --repo-root <siammask-checkout> demo \
     --experiment siammask_sharp \
     --config config_davis.json \
     --resume <SiamMask_DAVIS.pth> \
     --base-path data/tennis
   ```

5. Add `--run` before `demo` only after confirming a GUI/display session is available.

Expected behavior: OpenCV shows the first frame, the user selects an ROI, and subsequent frames display mask overlay/polygon tracking. This is not suitable for headless automation.

## Benchmark Test Flow

Use this when the user wants to create tracker output files for VOT, DAVIS, or YouTube-VOS style benchmarks.

1. Validate data with the data-preparation sub-skill.
2. Select a config/checkpoint/flag set:
   - VOT sharp/refine: `siammask_sharp`, VOT config, `--mask --refine`.
   - DAVIS/YouTube-VOS segmentation: `siammask_sharp`, DAVIS config, `--mask --refine`.
   - Base mask branch: `siammask_base`, base config, `--mask`.
   - SiamRPN box tracking: `siamrpn_resnet`, no mask/refine flags.
3. Compose the command:

   ```bash
   python scripts/run_tracking.py --repo-root <siammask-checkout> test \
     --experiment siammask_sharp \
     --config config_vot18.json \
     --resume <checkpoint.pth> \
     --dataset VOT2018 --mask --refine --cpu
   ```

4. Add `--run` before `test` when ready.

Outputs are checkout-local runtime result files. VOT-style tracking writes under a `test/<dataset>/<tracker-name>/baseline/<video>/` layout. VOS-style segmentation can write masks when `--save-mask` is supplied.

## VOT Result Evaluation Flow

Use this after tracking results already exist and the task is to compute VOT accuracy/robustness/EAO metrics.

```bash
python scripts/run_tracking.py --repo-root <siammask-checkout> eval \
  --dataset VOT2018 \
  --result-dir <result-root> \
  --tracker-prefix C \
  --num 4
```

The result root must contain tracker directories matching the tracker prefix. Evaluation is CPU-oriented but imports numba and compiled VOT region helpers.

## Hyperparameter Tuning Flow

Use tuning only after data/checkpoints are validated and runtime cost is acceptable.

- `tune-vot` sweeps VOT-style `penalty_k`, `window_influence`, `lr`, and `instance_size` values and can use CPU or CUDA, although CUDA is strongly preferred.
- `tune-vos` is for DAVIS/YouTube-VOS-style masks and calls CUDA APIs unconditionally.

Example VOT tuning dry-run:

```bash
python scripts/run_tracking.py --repo-root <siammask-checkout> tune-vot \
  --experiment siammask_sharp \
  --config config_vot18.json \
  --dataset VOT2018 \
  --resume <checkpoint.pth> \
  --mask --refine \
  --penalty-k 0.08,0.13,0.01 \
  --window-influence 0.38,0.44,0.01 \
  --lr 0.3,0.35,0.01 \
  --search-region 255,256,16
```

Tuning writes `result/<dataset>/...` style folders and can create many runs. Keep dry-run until the user approves runtime and disk usage.

## Validation Checklist

Before adding `--run`:

- The checkout root is correct and passes the root environment probe.
- The selected experiment directory contains the intended config and `custom.py` model definition.
- The checkpoint path resolves from the experiment directory or is absolute.
- The dataset name matches a prepared benchmark layout.
- The selected mask/refine flags match the checkpoint family.
- CUDA expectations are explicit for training-derived checkpoints, VOS tuning, or speed-sensitive evaluation.
