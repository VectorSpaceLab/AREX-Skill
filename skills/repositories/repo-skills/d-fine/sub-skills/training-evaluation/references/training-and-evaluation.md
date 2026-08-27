# Training and Evaluation Reference

This reference condenses the D-FINE `train.py` workflow into a command-building guide. It is scoped to training, evaluation, resume, tuning, distributed launch, AMP/EMA, output handling, and safe overrides.

## Evidence distilled
- `README.md` Usage sections for COCO2017, Objects365 to COCO2017, Custom Dataset, Customizing Batch Size, Customizing Input Size, and Others.
- `train.py` CLI and mode checks.
- `src/solver/_solver.py`, `src/solver/det_solver.py`, `src/solver/det_engine.py` for checkpoint loading and output behavior.
- `configs/runtime.yml` and `configs/dfine/include/optimizer.yml` for runtime defaults.
- `reference/safe_training.sh` for the legacy interactive launch pattern.

## Fast decision tree
1. **Train from scratch**: use `--mode train` with a config for the dataset and model size.
2. **Evaluate a checkpoint**: use `--mode test` with `--checkpoint ...` and `--test-only` is added automatically.
3. **Continue the same run**: use `--mode resume` with a full training checkpoint such as `last.pth`.
4. **Fine-tune on a new dataset or class set**: use `--mode tune` with a pretrained checkpoint.

Never try to combine resume and tuning in one run.

## Helper script
Use the bundled generator instead of hand-writing launch strings every time:

```bash
python ../scripts/dfine_train_command.py --help
python ../scripts/dfine_train_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --mode train \
  --devices 0,1,2,3 \
  --use-amp \
  --seed 0
```

The helper prints a shell-quoted command only. It never launches training.

## Mode to CLI mapping

| Mode | Printed train.py flags | What it does |
|---|---|---|
| `train` | `-c CONFIG` | Starts a fresh fit run.
| `test` | `-c CONFIG --test-only -r CHECKPOINT` | Runs evaluation only.
| `resume` | `-c CONFIG -r CHECKPOINT` | Restores the full solver state and continues training.
| `tune` | `-c CONFIG -t CHECKPOINT` | Loads model weights for fine-tuning and tolerates head-size differences where possible.

## Launch topology

### Single process
Use this when you want one Python process, usually for quick checks or CPU runs.

```bash
python train.py -c configs/dfine/dfine_hgnetv2_n_coco.yml --test-only -r model.pth
```

Typical direct flags:
- `--device cpu` for CPU-only evaluation or debugging.
- `--device cuda:0` for one-GPU runs when you do not want `torchrun`.
- `--print-method builtin|rich` to control rank-local printing.
- `--print-rank N` to keep logs from a chosen rank.

### Distributed single node
Use `torchrun` for multi-GPU training or validation.

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --master_port=7777 --nproc_per_node=4 \
  train.py -c configs/dfine/dfine_hgnetv2_l_coco.yml --use-amp --seed=0
```

Rules:
- `CUDA_VISIBLE_DEVICES` should list the GPUs you want to expose.
- `--nproc_per_node` should usually match the number of visible GPUs.
- Pick a free `--master_port` for each job.
- The helper infers `torchrun` when `--devices` or `--nproc` implies more than one process.

## Flag semantics

### Core command flags
- `-c/--config`: required YAML config file.
- `-r/--resume`: resume from a full solver checkpoint.
- `-t/--tuning`: load weights for fine-tuning.
- `--test-only`: skip training and run evaluation.
- `--use-amp`: enable mixed precision when CUDA is available.
- `--seed`: reproducibility seed.
- `--output-dir`: directory for checkpoints, logs, evaluation dumps, and sample images.
- `--summary-dir`: explicit TensorBoard directory.
- `-u/--update`: YAML-style overrides parsed before the config object is built.

### Override syntax
`-u` accepts dotted keys and YAML values. Use it for runtime tweaks, not for the dedicated launch flags.

Examples:
```bash
-u train_dataloader.total_batch_size=64
-u val_dataloader.total_batch_size=128
-u use_ema=False
-u HGNetv2.pretrained=False
-u optimizer.lr=0.0005
```

Values are YAML parsed, so booleans, lists, and numbers should use YAML syntax.

### Reserved flags vs overrides
The helper rejects `--update` tokens that try to replace the command-level flags it already owns, such as `resume`, `tuning`, `test_only`, `config`, `use_amp`, `seed`, `output_dir`, `summary_dir`, `device`, `print_method`, and `print_rank`.

## Checkpoint behavior

### Resume
`--resume` restores the full training state:
- model
- optimizer
- learning-rate schedulers
- warmup scheduler
- EMA state
- GradScaler state when present
- `last_epoch`

Use it for interrupted jobs and continue from the saved epoch.

### Tuning
`--tuning` loads model weights only and is the right choice when the dataset or class count changes.

Important details:
- The code prefers `state["ema"]["module"]` when it exists, otherwise `state["model"]`.
- D-FINE tries to adjust head parameters when shapes differ across datasets.
- The backbone pretrained flag is disabled automatically for resume/tuning runs when HGNetv2 is present.

### Test-only evaluation
`--test-only -r CHECKPOINT` runs `solver.val()` instead of `solver.fit()`.

Use a training checkpoint, not a metrics-only dump. For a normal evaluation run, the checkpoint should usually be `last.pth`, `checkpoint*.pth`, or a best-state file produced by training.

## Output, summary, and evaluation files

### Output directory
`--output-dir` overrides the config default. The solver creates the directory if needed.

Typical outputs during training:
- `last.pth`
- `checkpointXXXX.pth`
- `best_stg1.pth`
- `best_stg2.pth`
- `log.txt`
- `eval/` dumps when evaluation is available
- `train_samples/` and `val_samples/` image snapshots when enabled by the engine

Typical outputs during validation:
- `eval.pth`

### Summary directory
If `--summary-dir` is set, TensorBoard writes there. Otherwise it falls back to `<output-dir>/summary`.

### Runtime defaults
`configs/runtime.yml` and the optimizer include provide the usual defaults:
- `use_amp`
- `use_ema`
- `ema.decay`
- `ema.warmups`
- `output_dir`
- `checkpoint_freq`

## Recommended command patterns

### COCO2017 training
```bash
python ../scripts/dfine_train_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --mode train \
  --devices 0,1,2,3 \
  --use-amp \
  --seed 0 \
  --output-dir output/dfine_l_coco
```

### COCO2017 test-only evaluation
```bash
python ../scripts/dfine_train_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --mode test \
  --checkpoint output/dfine_l_coco/best_stg2.pth \
  --devices 0,1,2,3 \
  --output-dir output/dfine_l_coco_eval
```

### Objects365 to COCO fine-tuning
```bash
python ../scripts/dfine_train_command.py \
  --config configs/dfine/objects365/dfine_hgnetv2_l_obj2coco.yml \
  --mode tune \
  --checkpoint output/dfine_l_obj365/best_stg2.pth \
  --devices 0,1,2,3 \
  --use-amp \
  --seed 0 \
  --output-dir output/dfine_l_obj2coco
```

### Custom dataset fine-tuning
```bash
python ../scripts/dfine_train_command.py \
  --config configs/dfine/custom/dfine_hgnetv2_l_custom.yml \
  --mode train \
  --devices 0,1,2,3 \
  --use-amp \
  --seed 0
```

### Custom dataset evaluation
```bash
python ../scripts/dfine_train_command.py \
  --config configs/dfine/custom/dfine_hgnetv2_l_custom.yml \
  --mode test \
  --checkpoint output/dfine_hgnetv2_l_custom/best_stg2.pth \
  --devices 0,1,2,3
```

## Safe preflight checklist
- Confirm the config matches the dataset family and class count.
- Choose exactly one of train, test, resume, or tune.
- Ensure the checkpoint exists before using `resume`, `test`, or `tune`.
- For multi-GPU jobs, verify `total_batch_size` is divisible by world size.
- Keep `output_dir` unique per experiment, or reuse it only when resuming.
- Use `--summary-dir` if you want TensorBoard somewhere other than the default summary folder.
- Leave dataset schema edits and class-count changes to `../data-and-configs/SKILL.md`.

## When to route elsewhere
- Dataset layout, remapping, or `num_classes` changes: `../data-and-configs/SKILL.md`
- Backbone / decoder / criterion internals: `../architecture-api/SKILL.md`
- ONNX, TensorRT, OpenVINO, or benchmark commands: `../inference-export/SKILL.md`
