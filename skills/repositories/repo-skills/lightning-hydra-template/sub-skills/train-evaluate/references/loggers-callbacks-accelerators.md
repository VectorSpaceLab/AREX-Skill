# Loggers, Callbacks, and Accelerators

## Callback defaults

`callbacks=default` composes:

| Callback | Target | Default override highlights |
| --- | --- | --- |
| `model_checkpoint` | `lightning.pytorch.callbacks.ModelCheckpoint` | `dirpath=${paths.output_dir}/checkpoints`, `filename=epoch_{epoch:03d}`, `monitor=val/acc`, `mode=max`, `save_last=True`, `auto_insert_metric_name=False`. |
| `early_stopping` | `lightning.pytorch.callbacks.EarlyStopping` | `monitor=val/acc`, `patience=100`, `mode=max`. |
| `model_summary` | `lightning.pytorch.callbacks.RichModelSummary` | `max_depth=-1` in the default group override. |
| `rich_progress_bar` | `lightning.pytorch.callbacks.RichProgressBar` | Rich CLI progress output. |

Use `callbacks=null` for smoke/debug runs when checkpointing and early stopping are not needed.

## Logger configs

| Logger config | Target | Requirements and cautions |
| --- | --- | --- |
| `logger=csv` | Lightning `CSVLogger` | Best default for smoke runs and local logs. |
| `logger=tensorboard` | `TensorBoardLogger` | Requires TensorBoard/TensorBoardX if the environment does not include it. |
| `logger=wandb` | `WandbLogger` | Requires `wandb`, project/entity setup, and login or offline mode. |
| `logger=neptune` | `NeptuneLogger` | Requires `neptune-client` and `NEPTUNE_API_TOKEN`. |
| `logger=comet` | `CometLogger` | Requires `comet-ml` and `COMET_API_TOKEN`. |
| `logger=mlflow` | `MLFlowLogger` | Requires `mlflow`; default tracking URI points under the template logs directory. |
| `logger=aim` | `AimLogger` | Requires `aim>=3.16.2`; config disables terminal log capture to avoid a known loop issue. |
| `logger=many_loggers` | multiple | Default many-loggers config combines CSV, TensorBoard, and W&B; enable only when dependencies/credentials are ready. |

Use `logger=null` or `logger=csv` when testing in CI, no-network, no-credential, or non-interactive environments.

## Trainer groups and backend scope

| Trainer group | Meaning | Verification/operating notes |
| --- | --- | --- |
| `trainer=default` | CPU, 1 device, min 1 epoch, max 10 epochs. | Portable config/API baseline. |
| `trainer=cpu` | Overrides accelerator CPU and 1 device. | Best smoke/default path. |
| `trainer=gpu` | GPU accelerator, 1 device. | Requires CUDA-capable PyTorch and visible GPU. Config composition alone is not GPU verification. |
| `trainer=ddp` | `strategy=ddp`, GPU accelerator, 4 devices, `sync_batchnorm=True`. | Requires multi-GPU hardware and data/cache readiness; README warns DDP can be problematic. |
| `trainer=ddp_sim` | CPU, 2 devices, `strategy=ddp_spawn`. | Useful to test multiprocessing mechanics, but slower and can expose pickling/Hydra issues. |
| `trainer=mps` | Apple MPS accelerator. | Requires macOS Apple Silicon and MPS-capable PyTorch. |

The README also shows TPU as `+trainer.tpu_cores=8`, but no dedicated TPU config is included.

## Mixed precision and Trainer flags

Trainer flags can be overridden from CLI:

```bash
python src/train.py trainer=gpu +trainer.precision=16
python src/train.py +trainer.gradient_clip_val=0.5
python src/train.py +trainer.val_check_interval=0.25
python src/train.py +trainer.accumulate_grad_batches=10
python src/train.py +trainer.max_time="00:12:00:00"
```

Validate that the installed Lightning version accepts the flag and that the hardware/backend supports it.
