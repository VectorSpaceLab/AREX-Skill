# Target Speaker Extraction

Use this reference for offline and online target speaker extraction (TSE) training and evaluation-only runs. TSE training is multi-modal for most configs and should not be launched until audio lists, reference modality directories, GPUs, and checkpoint settings are verified.

## Workflow families

| Family | Directory role | Causality | Main cues/models |
| --- | --- | --- | --- |
| Offline TSE | non-causal target speaker extraction | mostly non-causal | reference speech with SpEx+, lip with AV-ConvTasNet/AV-DPRNN/AV-TFGridNet/AV-MossFormer2, gesture with SEG, EEG with NeuroHeed |
| Online TSE | causal/streaming-oriented audio-visual extraction | online/causal variants | lip with AV-SkiM and AV-SkiM autoregressive-style configs |

The launchers for both families use the same structure: edit GPU IDs, process count, checkpoint directory, and config path; create or reuse a checkpoint directory; copy the config into it; launch `train.py` with distributed PyTorch.

## Offline TSE train pattern

```bash
cd train/target_speaker_extraction
export CUDA_VISIBLE_DEVICES=0,1
python -W ignore -m torch.distributed.launch \
  --nproc_per_node=2 \
  --master_port=8899 \
  train.py \
  --config config/<CONFIG>.yaml \
  --checkpoint_dir checkpoints/<EXPERIMENT> \
  --train_from_last_checkpoint 0
```

For a fresh run, `checkpoint_dir` should be a new directory and `init_from` in the YAML should usually be `None`. For fine-tuning from an existing model, set `init_from` to the source checkpoint directory containing `last_best_checkpoint.pt`, use a new checkpoint directory, and keep `train_from_last_checkpoint=0`.

## Online TSE train pattern

```bash
cd train/target_speaker_extraction_online
export CUDA_VISIBLE_DEVICES=0
python -W ignore -m torch.distributed.launch \
  --nproc_per_node=1 \
  --master_port=8899 \
  train.py \
  --config config/<CONFIG>.yaml \
  --checkpoint_dir checkpoints/<EXPERIMENT> \
  --train_from_last_checkpoint 0
```

Online TSE configs are lip/video based. Verify image size, `ref_sr`, and availability of the video tree before launch.

## Evaluation-only pattern

Evaluation-only launchers set `train_from_last_checkpoint=1`, read `config.yaml` from an existing checkpoint directory, and pass `--evaluate_only 1` to `train.py`.

Template:

```bash
cd train/<tse-directory>
export CUDA_VISIBLE_DEVICES=0
python -W ignore -m torch.distributed.launch \
  --nproc_per_node=1 \
  --master_port=8899 \
  train.py \
  --evaluate_only 1 \
  --config checkpoints/<EXPERIMENT>/config.yaml \
  --checkpoint_dir checkpoints/<EXPERIMENT> \
  --train_from_last_checkpoint 1
```

Do not use evaluation-only as an objective metric workflow. It can validate model loss and generate/evaluate internal outputs, but standalone objective metrics should be routed to `speechscore-metrics`.

## TSE config essentials

Top-level required fields:

```yaml
seed: 20
use_cuda: 1
speaker_no: 2
mix_lst_path: data/<DATASET>/mixture_data_list_2mix.csv
audio_direc: DATA_ROOT/audio_clean/
reference_direc: DATA_ROOT/reference_modality/
audio_sr: 16000
ref_sr: 25
num_workers: 4
batch_size: 2
accu_grad: 1
effec_batch_size: 4
max_length: 4
init_from: None
causal: 0
network_reference:
  cue: lip
  backbone: resnet18
network_audio:
  backbone: av_mossformer2
loss_type: sisnr
init_learning_rate: 0.00015
max_epoch: 150
clip_grad_norm: 5
```

Cue-specific checks:

- `lip`: reference files must be `.mp4` and path reconstruction uses `set/speaker/utterance.mp4` from the mixture CSV. Offline lip converts frames to grayscale ROI; online lip reads RGB frames and resizes to the configured image size.
- `gesture`: reference files must be `.npy` gesture arrays and are reshaped to 30-dimensional features.
- `eeg`: reference directory must contain the subject/trial arrays expected by the EEG dataloader, and CSV starts must align with `ref_sr`.
- `speech`: `mix_lst_path` is a directory with partition scp files, not a single mixture CSV; it also needs a speaker-id list for training speaker labels.

## CSV/list validation before launch

For lip/gesture/offline and online CSVs:

1. Confirm all requested partitions exist in the first CSV column.
2. Confirm the number of speaker groups matches `speaker_no`.
3. Confirm the last column is a positive duration in seconds.
4. Confirm audio paths reconstructed from the row exist under `audio_direc`.
5. Confirm reference modality paths reconstructed from the row exist under `reference_direc`.
6. Confirm `ref_sr` matches the modality frame/feature rate.

For speech-reference TSE:

1. Confirm each partition directory has `mix_with_length.scp`, `ref.scp`, and `aux.scp`.
2. Confirm rows align by index across those files.
3. Confirm `audio_direc` prefixes mixture and target paths, and `reference_direc` prefixes auxiliary/reference paths.
4. Confirm the speaker-id list exists for training partitions.

## Handling missing modality/reference directories

If a request says “train TSE” but only provides audio paths, do not assume lip/gesture/EEG data can be derived. Ask for one of these concrete resolutions:

- Provide the matching `reference_direc` for the selected cue and dataset.
- Switch to audio-only reference speech TSE and provide the partition scp directory.
- Use an existing checkpoint only for inference/evaluation that does not require training data, if the specific command supports it.
- Narrow the task to data/list preparation until reference modality assets are available.

For the difficult case where a TSE training request lacks visual/reference modality directories, the safe response is to inspect the chosen config, identify `network_reference.cue`, list the expected directory/file pattern, and stop before launch.

## Fine-tune and checkpoint notes

- Fresh TSE launchers create a timestamped checkpoint directory when `checkpoint_dir` is empty; for reproducibility, prefer a stable experiment name.
- Resuming uses the checkpoint directory's `config.yaml` and `last_checkpoint.pt`.
- Fine-tuning uses YAML `init_from` to load `last_best_checkpoint.pt` from a previous checkpoint directory and starts a new run.
- Do not set `init_from` to a checkpoint file; it is expected to be a directory in the included solver code.
- Multi-GPU TSE initializes an NCCL process group, uses SyncBatchNorm, and wraps the model for distributed training. CPU-only runs are not representative.
