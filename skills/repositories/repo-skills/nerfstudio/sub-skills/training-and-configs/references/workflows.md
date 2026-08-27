# Training workflows

## First model on processed data

```bash
ns-train nerfacto --data PROCESSED_DATA_DIR
```

Use this after data-preparation validates `PROCESSED_DATA_DIR`. The run writes outputs, checkpoints, and `config.yml` under the configured output root.

## Explicit dataparser flags

```bash
ns-train nerfacto --vis viewer nerfstudio-data --eval-mode filename --data PROCESSED_DATA_DIR
```

Use filename eval mode when the dataset contains explicit split lists and you want the dataparser to honor them.

## Resume or load weights

```bash
ns-train nerfacto --data PROCESSED_DATA_DIR --load-dir OUTPUTS/SCENE/nerfacto/RUN/nerfstudio_models
```

Do not confuse this with `ns-viewer --load-config` or `ns-eval --load-config`, which load a completed run configuration.

## Logging and viewer

Training supports `--vis viewer`, `tensorboard`, `wandb`, `comet`, or combinations such as `viewer+tensorboard`. The viewer is most useful for fast methods; for slow or remote jobs, tensorboard/W&B/Comet can reduce viewer overhead.

## Multi-GPU shape

```bash
CUDA_VISIBLE_DEVICES=0,1 ns-train nerfacto-big --machine.num-devices 2 --data PROCESSED_DATA_DIR
```

Tune `train-num-rays-per-batch`, evaluation chunk size, and model size when scaling. Throughput and memory do not scale linearly for every method.

## Reduced smoke concept

For a correctness smoke, use tiny data, a torch implementation when available, `machine.device_type=cpu` or one GPU, very few iterations, no mixed precision on CPU, and a temporary output directory. This only proves config/data/training-loop mechanics.
