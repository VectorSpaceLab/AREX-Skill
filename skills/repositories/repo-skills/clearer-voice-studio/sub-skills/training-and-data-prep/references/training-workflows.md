# Training Workflows

This reference summarizes the training-side workflows for ClearerVoice-Studio. It is intentionally a planning and launch guide, not a request to start expensive jobs.

## Common launcher pattern

The SE, SS, and SR training launchers follow the same pattern:

1. Select visible GPUs and process count.
2. Select a network name.
3. Point `config_pth` at a train YAML for that network.
4. Set `checkpoint_dir` to the experiment directory.
5. Decide whether this is a resume or a new/fine-tune run.
6. Copy the config into the checkpoint directory.
7. Launch distributed PyTorch training against `train.py`.

Template:

```bash
cd train/<task-directory>
export CUDA_VISIBLE_DEVICES=0,1
python -W ignore -m torch.distributed.launch \
  --nproc_per_node=2 \
  --master_port=8899 \
  train.py \
  --config config/train/<NETWORK>.yaml \
  --checkpoint_dir checkpoints/<EXPERIMENT> \
  --train_from_last_checkpoint 0 \
  --init_checkpoint_path None \
  --print_freq 10 \
  --checkpoint_save_freq 1000
```

If `torch.distributed.launch` is removed in the installed PyTorch, use an equivalent `torchrun --nproc_per_node=<N> --master_port=<PORT> train.py ...` command. Keep the same argument values and still verify the training script accepts `local_rank` or reads distributed environment variables.

## Speech enhancement (SE)

Supported training-side networks:

| Network | Intended sample rate | Notes |
| --- | ---: | --- |
| `FRCRN_SE_16K` | 16000 | Complex single-channel enhancement; waveform list rows contain noisy and clean target paths. |
| `MossFormerGAN_SE_16K` | 16000 | GAN-style SE; batch sizes are often smaller and discriminator checkpoint state is involved. |
| `MossFormer2_SE_48K` | 48000 | Full-band 48 kHz enhancement; check list sample rates carefully because example lists may be inherited from 16 kHz material. |

Training config essentials:

- `mode: train`
- `network`
- `sampling_rate`
- `tr_list` and `cv_list`
- optimizer settings such as `init_learning_rate`, `finetune_learning_rate`, `max_epoch`, `batch_size`, `effec_batch_size`, `accu_grad`, and `max_length`
- feature settings such as STFT window/FFT fields and, for MossFormer2 full-band SE, mel/fbank-related fields

SE training-side inference pattern:

```bash
cd train/speech_enhancement
export CUDA_VISIBLE_DEVICES=0
python -u inference.py --config config/inference/<NETWORK>.yaml
```

Use it to decode with a checkpoint directory created by training or fine-tuning. For packaged pretrained inference through the ClearVoice API, route to `clearvoice-inference` instead.

## Speech separation (SS)

Supported training-side networks:

| Network | Intended sample rate | Notes |
| --- | ---: | --- |
| `MossFormer2_SS_8K` | 8000 | Two-speaker separation at 8 kHz. |
| `MossFormer2_SS_16K` | 16000 | Two-speaker separation at 16 kHz. |

SS-specific config and list points:

- `num_spks` must match the number of target source paths per row.
- `load_type` controls how the dataloader interprets each row. Use `one_input_multi_outputs` for one mixture path followed by multiple source-reference paths.
- `sampling_rate` must match the dataset variant or be a deliberate resampling choice.
- Inference outputs are separated waveforms under `output_dir`; objective metrics should be routed to `speechscore-metrics`.

Training-side inference pattern:

```bash
cd train/speech_separation
export CUDA_VISIBLE_DEVICES=0
python -u inference.py --config config/inference/<NETWORK>.yaml
```

## Speech super-resolution (SR)

Supported training-side network:

| Network | Target sample rate | Notes |
| --- | ---: | --- |
| `MossFormer2_SR_48K` | 48000 | Upsamples lower-rate speech to 48 kHz. Train YAML points to an auxiliary JSON architecture/training config. |

SR has two config layers:

- YAML: launch-level fields (`mode`, `network`, `config_json`, `checkpoint_dir`, `tr_list`, `cv_list`, `tt_list`, checkpoint and batch settings).
- JSON: generator/feature/distributed settings (`sampling_rate`, `supported_sampling_rates`, `num_gpus`, `batch_size`, upsample rates/kernel sizes, FFT/mel fields, `dist_config`).

The SR training launcher passes `--init_checkpoint_path`, but the current SR train parser does not define that argument. If strict argument parsing fails with an unrecognized `--init_checkpoint_path`, remove that launcher argument or add it deliberately before launch.

Training-side inference pattern:

```bash
cd train/speech_super_resolution
export CUDA_VISIBLE_DEVICES=0
python -u inference.py --config config/inference/MossFormer2_SR_48K.yaml
```

SR inference can accept a single audio file, an audio directory, or a one-path-per-line list. For packaged pretrained ClearVoice API use, route to `clearvoice-inference`.

## Resume versus fine-tune

| Intent | SE/SS knobs | SR knobs | TSE knobs | Effect |
| --- | --- | --- | --- | --- |
| Fresh run | `train_from_last_checkpoint=0`, `init_checkpoint_path=None` | `train_from_last_checkpoint=0` | empty/new `checkpoint_dir`, `init_from: None` | New checkpoint directory and optimizer state. |
| Resume interrupted run | `train_from_last_checkpoint=1`, same `checkpoint_dir` | `train_from_last_checkpoint=1`, same `checkpoint_dir` | non-empty existing `checkpoint_dir`, `train_from_last_checkpoint=1` | Loads last checkpoint and optimizer/training counters when available. |
| Fine-tune from weights | `train_from_last_checkpoint=0`, `init_checkpoint_path=<checkpoint file>` | use an existing checkpoint directory only if the SR code path supports it; inspect first | `init_from: <checkpoint directory>` with new `checkpoint_dir` | Initializes model weights from a best/last checkpoint and starts a new run. |

Do not set resume and init/fine-tune simultaneously unless the code explicitly defines precedence. In SE/SS, resume takes precedence and init is ignored when `train_from_last_checkpoint` is true.

## GPU and distributed assumptions

- Source launchers contain fixed `gpu_id` values, `n_gpu`, and a dynamic `master_port`. Replace them with host-appropriate values.
- `n_gpu` or `--nproc_per_node` must match the number of IDs in `CUDA_VISIBLE_DEVICES`.
- The training code assumes CUDA/NCCL for distributed multi-GPU runs; CPU training is not a practical substitute for the included large models.
- For single-GPU checks, use one visible GPU and `--nproc_per_node=1` rather than leaving stale multi-GPU IDs.
- If another job occupies the generated port, choose a stable unused port instead of relying on time-derived values.

## Cheap pre-launch checklist

- Run the bundled config inspector with `--expect-task` and `--check-paths` on the selected config.
- Confirm every list path points to user data, not example placeholders.
- Confirm row formats and sample rates match the selected network.
- Confirm checkpoint directory, init checkpoint, and resume flag describe one unambiguous intent.
- Confirm the output directory is new or intentionally reused.
