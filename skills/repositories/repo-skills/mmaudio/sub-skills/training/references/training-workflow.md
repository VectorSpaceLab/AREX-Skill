# MMAudio Training Workflow

This reference distills the training path from the repository docs, `train.py`, `mmaudio/runner.py`, `mmaudio/sample.py`, `config/base_config.yaml`, `config/train_config.yaml`, `config/data/base.yaml`, and `mmaudio/data/data_setup.py` into a practical lifecycle.

## What training consumes

| Input | Where it comes from | Notes |
| --- | --- | --- |
| `Example_video` | `training/example_output/memmap/vgg-example.tsv` + memmaps | Smoke fixture. Must already exist before `example_train=True` works. |
| `Example_audio` | `training/example_output/memmap/audio-example.tsv` + memmaps | Smoke fixture. Must already exist before `example_train=True` works. |
| `ExtractedVGG` | `../data/v1-16-memmap/vgg-train.tsv` + memmaps | Main video-training corpus for the 16k path. |
| `AudioCaps`, `AudioSetSL`, `BBCSound`, `FreeSound`, `Clotho` | `../data/v1-16-memmap/*.tsv` + memmaps | Audio-text corpora mixed into `MultiModalDataset`. |
| `ExtractedVGG_val` / `ExtractedVGG_test` | validation and post-training sample paths | Used by the training loop and the built-in final sample. |

Training does not create these feature stores. It expects them to already exist.

## Command catalog

| Goal | Command | Notes |
| --- | --- | --- |
| Bounded smoke template | `python scripts/build_train_command.py --mode smoke` | Prints a command only; it does not launch training. |
| Adapted one-step smoke run | `OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 train.py exp_id=debug model=small_16k compile=False debug=True example_train=True batch_size=1 eval_batch_size=1 num_workers=0 num_iterations=1 val_interval=2 eval_interval=2 save_eval_interval=2 save_weights_interval=2 save_checkpoint_interval=2` | Safe bounded shape for one GPU and the bundled example fixtures. |
| Full base run | `OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=2 train.py exp_id=exp_1 model=small_16k` | The repo docs use this as the base-model example. |
| 44k training | `OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=<N> train.py exp_id=<exp_id> model=small_44k` | Use `medium_44k` or `large_44k` as needed. The training code rejects `_v2`. |
| Resume exact checkpoint | `... train.py exp_id=<exp_id> checkpoint=/path/to/<exp_id>_ckpt_last.pth` | Loads model, optimizer, scheduler, and EMA state. |
| Initialize from weights only | `... train.py exp_id=<fresh_exp_id> weights=/path/to/<model>_last.pth` | Loads model weights only. Use a fresh `exp_id` to avoid auto-resume shadowing. |

## Batch-size and launcher semantics

- `train.py` treats `batch_size` as the **total** batch size before DDP splitting and divides it by the number of GPUs at runtime.
- `eval_batch_size` is the per-GPU size used by the validation loader.
- The post-training sample path uses per-GPU batch sizing from the evaluation config, not the training config.
- Use `torchrun`; the training script expects the distributed launcher environment even for single-GPU runs.

## Runtime phases

1. Hydra composes `train_config.yaml` plus `base_config.yaml` and the data group.
2. `train.py` patches `cfg.data_dim` from the selected model sequence configuration.
3. DDP starts with NCCL on the requested world size.
4. `Runner` loads `empty_string.pth`, the model-specific VAE and Synchformer assets, and optional resume weights.
5. `train_pass` consumes extracted feature memmaps.
6. Validation uses `ExtractedVGG_val` on the configured `val_interval`.
7. Periodic evaluation uses the av-bench-backed cached evaluation path on `eval_interval`.
8. At exit, weights and checkpoints are saved unless `debug=True`.
9. The script synthesizes a final EMA weight file and then runs the built-in sample path.

## Expected outputs

| Path | Meaning |
| --- | --- |
| `output/<exp_id>/train-*-hydra/` | Hydra config snapshot. |
| `output/<exp_id>/<exp_id>_ckpt_last.pth` | Latest checkpoint with model, optimizer, scheduler, and EMA state. |
| `output/<exp_id>/<exp_id>_last.pth` | Latest model weights. |
| `output/<exp_id>/<exp_id>_ema_final.pth` | Synthesized EMA state saved after training. |
| `output/<exp_id>/train/`, `val/` | TensorBoard audio and spectrogram debug outputs. |
| `output/<exp_id>/val-sampled-videos/` | Validation sample videos produced during training eval. |
| `output/<exp_id>/test-sampled-videos/` | Post-training sample video for the built-in test pass. |
| `output/<exp_id>/*-output_metrics.json` | Final metrics emitted by the built-in sample path. |

## Resume precedence

1. An explicit `checkpoint=` wins.
2. Otherwise, if `output/<exp_id>/<exp_id>_ckpt_last.pth` exists, training auto-resumes from it.
3. Otherwise, if `weights=` is set, only the network weights load.
4. Therefore, use a fresh `exp_id` when you want pretrained weights to initialize a new run.

## Smoke tuning notes

- Keep `example_train=True`, `debug=True`, `compile=False`, and `num_iterations=1` for a bounded smoke run.
- Set every save/eval interval above `num_iterations` so nothing inside the loop fires on the single step.
- The built-in post-training sample still runs; the smoke command is bounded for the training loop, not a pure no-eval dry run.
- The bundled example fixtures live under `training/example_output/memmap/`; they are generated artifacts, not raw media.

## Input-schema reminders

- Video memmap TSVs use `id` and `label`.
- Audio memmap TSVs use `id` and `caption`.
- The audio datasets are concatenated with `MultiModalDataset` and the video dataset can be oversampled with `vgg_oversample_rate`.
- `mini_train` is not a reliable smoke switch in the current loader logic; `example_train=True` is the supported smoke route.

## Evidence labels

`docs/TRAINING.md`, `train.py`, `mmaudio/runner.py`, `mmaudio/sample.py`, `mmaudio/data/data_setup.py`, `mmaudio/model/sequence_config.py`, `config/base_config.yaml`, `config/train_config.yaml`, `config/data/base.yaml`.
