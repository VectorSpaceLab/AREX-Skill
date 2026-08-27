# HRM Training and Evaluation Workflows

## Pre-flight checklist

1. Validate the converted dataset with the data-preparation sub-skill.
2. Confirm CUDA, FlashAttention, and `adam_atan2_backend`:

   ```bash
   python sub-skills/training-evaluation/scripts/check_training_env.py \
     --repo-root /path/to/HRM --require-cuda
   ```

3. Decide W&B mode. For hosted tracking, run `wandb login`; for smoke/debug,
   set `WANDB_MODE=offline`.
4. Use `DISABLE_COMPILE=true` for debugging dependency or shape issues.
5. Match `global_batch_size` to GPU count and dataset size.

## Training examples

### Sudoku quick demo

```bash
python dataset/build_sudoku_dataset.py \
  --output-dir data/sudoku-extreme-1k-aug-1000 \
  --subsample-size 1000 \
  --num-aug 1000

OMP_NUM_THREADS=8 python pretrain.py \
  data_path=data/sudoku-extreme-1k-aug-1000 \
  epochs=20000 eval_interval=2000 global_batch_size=384 \
  lr=7e-5 puzzle_emb_lr=7e-5 \
  weight_decay=1.0 puzzle_emb_weight_decay=1.0
```

The README estimates about 10 hours on an RTX 4070 laptop GPU for this demo.

### ARC-1 default training

```bash
python dataset/build_arc_dataset.py
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 pretrain.py
```

### ARC-2

```bash
python dataset/build_arc_dataset.py \
  --dataset-dirs dataset/raw-data/ARC-AGI-2/data \
  --output-dir data/arc-2-aug-1000

OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 pretrain.py data_path=data/arc-2-aug-1000
```

### Maze 30x30 hard

```bash
python dataset/build_maze_dataset.py --output-dir data/maze-30x30-hard-1k
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 pretrain.py \
  data_path=data/maze-30x30-hard-1k \
  epochs=20000 eval_interval=2000 \
  lr=1e-4 puzzle_emb_lr=1e-4
```

## Checkpoints

If `checkpoint_path` is unset, `pretrain.py` creates:

```text
checkpoints/<project_name>/<run_name>/
  all_config.yaml
  <model source snapshots>
  step_<N>
```

`checkpoint_every_eval=true` saves at every eval cycle. Otherwise only the final
state is saved.

## Evaluation

```bash
OMP_NUM_THREADS=8 torchrun --nproc-per-node 8 evaluate.py checkpoint=<CHECKPOINT_PATH>
```

The evaluator loads `all_config.yaml` from the checkpoint directory, rebuilds
the model, loads the checkpoint weights, runs the test split, prints metrics on
rank 0, and writes selected output shards named:

```text
<CHECKPOINT_PATH>_all_preds.<rank>
```

`evaluate.py --help` is not a valid help path because the script parses
OmegaConf CLI values into `EvalConfig` and requires `checkpoint`. Use static
inspection or this reference for options.

## ARC post-processing

After evaluation saved `*_all_preds.*` shards, aggregate ARC predictions:

```bash
python sub-skills/training-evaluation/scripts/arc_postprocess.py \
  --dataset-path data/arc-aug-1000 \
  --checkpoint-prefix checkpoints/Arc-aug-1000\ ACT-torch/<run>/step_<N>
```

The helper reverses ARC augmentation suffixes, crops padded 30x30 sequences,
groups answers by original puzzle/input, and reports top-K puzzle accuracy.

## Bounded debug command

For dependency/config debugging without long training:

```bash
WANDB_MODE=offline DISABLE_COMPILE=true python pretrain.py --help
```

This prints Hydra-composed config and does not launch the training loop.
