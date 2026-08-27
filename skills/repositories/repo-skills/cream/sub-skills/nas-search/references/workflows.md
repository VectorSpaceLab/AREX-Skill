# NAS Search Workflows

## Purpose

Read this when you need the exact command shape for the monorepo's architecture-search projects.
It summarizes the safe launcher templates, the config files they expect, and the role of sampled datasets.

## AutoFormer

### Supernet training

Use the supernet config under `AutoFormer/experiments/supernet/` with the main training script:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --use_env supernet_train.py \
  --data-path <imagenet-root> --gp --change_qk --relative_position \
  --mode super --dist-eval --cfg <supernet-yaml> --epochs 500 \
  --warmup-epochs 20 --output <output-dir> --batch-size 128
```

### Evolution search

```bash
python -m torch.distributed.launch --nproc_per_node=8 --use_env evolution.py \
  --data-path <imagenet-root> --gp --change_qk --relative_position \
  --dist-eval --cfg <supernet-yaml> --resume <checkpoint> \
  --min-param-limits <value> --param-limits <value> --data-set EVO_IMNET
```

### Test / retrain evaluation

```bash
python -m torch.distributed.launch --nproc_per_node=8 --use_env supernet_train.py \
  --data-path <imagenet-root> --gp --change_qk --relative_position \
  --mode retrain --dist-eval --cfg <subnet-yaml> --resume <checkpoint> --eval
```

### Sampled ImageNet helper

The original sampled-ImageNet scripts copy files into `data/subImageNet/`. In the generated skill, use `../../../scripts/check_dataset_layout.py --kind subimagenet` to validate the layout and then adapt the command builder output instead of replaying the mutating copy script.

## AutoFormerV2 / S3

S3 uses `AutoFormerV2/evaluation.py` plus the config files under `AutoFormerV2/configs/`:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --use_env evaluation.py \
  --data-path <imagenet-root> --dist-eval --cfg <S3-yaml> --resume <checkpoint> --eval
```

## Cream

Cream uses a top-level dispatcher that accepts a mode and config path:

```bash
python tools/main.py train <train-config>
python tools/main.py retrain <retrain-config>
python tools/main.py test <test-config>
```

The dispatcher writes the chosen config into the dated workspace and launches the corresponding distributed script.
Use the configs under `Cream/experiments/configs/train`, `retrain`, and `test`.

## CDARTS

### Search / retrain / test

The main config object comes from `CDARTS/lib/config.py` and requires `--name`.
The project scripts are:

```bash
python search.py --name <run-name> [other args]
python retrain.py --name <run-name> [other args]
python test.py --name <run-name> [other args]
```

Use the CIFAR/ImageNet cell genotype files under `CDARTS/CDARTS/cells/` and the experiment logs under `CDARTS/experiments/` as the canonical evidence for model naming.

### Benchmark201

`CDARTS/benchmark201/search.py` is a more advanced path for NAS-Bench-201.
It expects Apex and the benchmark API path, so treat it as an optional accelerator/legacy workflow rather than the default route.

### Detection and segmentation branches

The downstream detection and segmentation trees are separate workflows with heavier dependency stacks.
Use the repository references only when the user explicitly asks for object detection or segmentation variants.

## Command selection tips

- Use the AutoFormer / Cream / CDARTS launcher that matches the requested mode.
- Keep the sampled-dataset helpers read-only in the skill tree; they are evidence, not runtime dependencies.
- If the user only needs a command string, run `../scripts/build_nas_command.py` instead of reconstructing the launcher by hand.
