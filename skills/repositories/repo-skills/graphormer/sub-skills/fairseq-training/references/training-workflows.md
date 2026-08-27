# Training workflows

Graphormer training is built on `fairseq-train` with Graphormer loaded as a
user-dir plugin. The main job of this sub-skill is to help a future agent build
or sanity-check a command without having to reopen the source examples.

## Common shape

A Graphormer training command usually combines:

- `fairseq-train`
- `--user-dir <graphormer-package-dir>`
- a graph dataset name and source
- a task (`graph_prediction`, `graph_prediction_with_flag`, or `is2re`)
- a criterion matched to the task
- a Graphormer architecture (`graphormer_slim`, `graphormer_base`, or
  `graphormer3d_base`)
- optimizer, learning-rate schedule, batch size, and save directory

Keep those four pieces aligned before thinking about tuning.

## Property prediction workflows

### ZINC

Best use:
- graph regression on the PyG ZINC dataset
- a lightweight command that exercises the standard graph prediction path

Typical command shape:

```bash
CUDA_VISIBLE_DEVICES=0 fairseq-train \
  --user-dir <graphormer-package-dir> \
  --num-workers 16 \
  --ddp-backend=legacy_ddp \
  --dataset-name zinc \
  --dataset-source pyg \
  --task graph_prediction \
  --criterion l1_loss \
  --arch graphormer_slim \
  --num-classes 1 \
  --attention-dropout 0.1 --act-dropout 0.1 --dropout 0.0 \
  --optimizer adam --adam-betas '(0.9, 0.999)' --adam-eps 1e-8 --clip-norm 5.0 --weight-decay 0.01 \
  --lr-scheduler polynomial_decay --power 1 --warmup-updates 60000 --total-num-update 400000 \
  --lr 2e-4 --end-learning-rate 1e-9 \
  --batch-size 64 \
  --fp16 \
  --data-buffer-size 20 \
  --encoder-layers 12 \
  --encoder-embed-dim 80 \
  --encoder-ffn-embed-dim 80 \
  --encoder-attention-heads 8 \
  --max-epoch 10000 \
  --save-dir ./ckpts
```

Assumptions:
- PyG ZINC is available or can be downloaded
- the task is scalar regression, so `--num-classes 1` is correct
- fp16 and the batch size assume a CUDA-capable GPU

### PCQM4M v1

Best use:
- OGB regression on the original PCQM4M benchmark
- the canonical Graphormer base recipe

Typical command shape:

```bash
fairseq-train \
  --user-dir <graphormer-package-dir> \
  --num-workers 16 \
  --ddp-backend=legacy_ddp \
  --dataset-name pcqm4m \
  --dataset-source ogb \
  --task graph_prediction \
  --criterion l1_loss \
  --arch graphormer_base \
  --num-classes 1 \
  --attention-dropout 0.1 --act-dropout 0.1 --dropout 0.0 \
  --optimizer adam --adam-betas '(0.9, 0.999)' --adam-eps 1e-8 --clip-norm 5.0 --weight-decay 0.0 \
  --lr-scheduler polynomial_decay --power 1 --warmup-updates 60000 --total-num-update 1000000 \
  --lr 2e-4 --end-learning-rate 1e-9 \
  --batch-size 64 \
  --fp16 \
  --data-buffer-size 20 \
  --encoder-layers 12 \
  --encoder-embed-dim 768 \
  --encoder-ffn-embed-dim 768 \
  --encoder-attention-heads 32 \
  --max-epoch 300 \
  --save-dir ./ckpts
```

### PCQM4M v2

Best use:
- OGB LSC regression on PCQM4Mv2
- a larger batch size than the v1 recipe

Typical command shape:

```bash
fairseq-train \
  --user-dir <graphormer-package-dir> \
  --num-workers 16 \
  --ddp-backend=legacy_ddp \
  --dataset-name pcqm4mv2 \
  --dataset-source ogb \
  --task graph_prediction \
  --criterion l1_loss \
  --arch graphormer_base \
  --num-classes 1 \
  --attention-dropout 0.1 --act-dropout 0.1 --dropout 0.0 \
  --optimizer adam --adam-betas '(0.9, 0.999)' --adam-eps 1e-8 --clip-norm 5.0 --weight-decay 0.0 \
  --lr-scheduler polynomial_decay --power 1 --warmup-updates 60000 --total-num-update 1000000 \
  --lr 2e-4 --end-learning-rate 1e-9 \
  --batch-size 256 \
  --fp16 \
  --data-buffer-size 20 \
  --save-dir ./ckpts
```

## FLAG fine-tuning workflow

### MolHIV with FLAG

Best use:
- finetuning Graphormer on `ogbg-molhiv`
- the `graph_prediction_with_flag` task and `_with_flag` criterion path

The source recipe uses a pretrained MolHIV-oriented checkpoint, FLAG
perturbation parameters, and `--pre-layernorm`.

Typical command shape:

```bash
CUDA_VISIBLE_DEVICES=3 fairseq-train \
  --user-dir <graphormer-package-dir> \
  --num-workers 16 \
  --ddp-backend=legacy_ddp \
  --dataset-name ogbg-molhiv \
  --dataset-source ogb \
  --task graph_prediction_with_flag \
  --criterion binary_logloss_with_flag \
  --arch graphormer_base \
  --num-classes 1 \
  --attention-dropout 0.1 --act-dropout 0.1 --dropout 0.0 \
  --optimizer adam --adam-betas '(0.9, 0.999)' --adam-eps 1e-8 --clip-norm 5.0 --weight-decay 0.0 \
  --lr-scheduler polynomial_decay --power 1 --warmup-updates <derived-from-epoch> --total-num-update <derived-from-epoch> \
  --lr 2e-4 --end-learning-rate 1e-5 \
  --batch-size 128 \
  --fp16 \
  --data-buffer-size 20 \
  --encoder-layers 12 \
  --encoder-embed-dim 768 \
  --encoder-ffn-embed-dim 768 \
  --encoder-attention-heads 32 \
  --max-epoch <epoch-plus-one> \
  --save-dir ./ckpts \
  --pretrained-model-name pcqm4mv1_graphormer_base_for_molhiv \
  --seed 1 \
  --flag-m 3 \
  --flag-step-size 0.01 \
  --flag-mag 0 \
  --pre-layernorm
```

## Graphormer3D / OC20 workflow

### IS2RE

Best use:
- Graphormer3D on the OC20 IS2RE task
- large-scale 3D structure and force/energy learning

Typical command shape:

```bash
fairseq-train \
  --user-dir <graphormer-package-dir> \
  ./data/is2re_train_val_test_lmdbs/data/is2re/all \
  --valid-subset val_id,val_ood_ads,val_ood_cat,val_ood_both \
  --best-checkpoint-metric loss \
  --num-workers 0 \
  --ddp-backend=c10d \
  --task is2re \
  --criterion mae_deltapos \
  --arch graphormer3d_base \
  --optimizer adam --adam-betas '(0.9, 0.98)' --adam-eps 1e-6 --clip-norm 5.0 \
  --lr-scheduler polynomial_decay --lr 3e-4 --warmup-updates 10000 --total-num-update 1000000 --batch-size 4 \
  --dropout 0.0 --attention-dropout 0.1 --weight-decay 0.001 --update-freq 1 --seed 1 \
  --fp16 --fp16-init-scale 4 --fp16-scale-window 256 --tensorboard-logdir ./tsbs \
  --embed-dim 768 --ffn-embed-dim 768 --attention-heads 48 \
  --max-update 1000000 --log-interval 100 --log-format simple \
  --save-interval-updates 5000 --validate-interval-updates 2500 --keep-interval-updates 30 --no-epoch-checkpoints \
  --save-dir ./ckpt --layers 12 --blocks 4 --required-batch-size-multiple 1 --node-loss-weight 15
```

Operational notes:
- the source docs warn that `--batch-size 4` needs at least 32 GB of GPU memory
- if memory is tight, lower the batch size and compensate with update
  frequency or additional GPUs
- the data path must point to the OC20 LMDB layout expected by the task

## When to use the command builder

Use the bundled command builder when you need a reviewable command without
opening the original shell scripts. It renders the maintained recipe family,
lets you change a few common knobs, and never starts training.
