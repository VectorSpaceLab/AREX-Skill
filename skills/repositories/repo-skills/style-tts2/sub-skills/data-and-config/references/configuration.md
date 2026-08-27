# Configuration guide

## High-impact fields

### Paths and checkpoints
- `log_dir`: output directory for checkpoints, logs, and copied configs.
- `first_stage_path`: stage-1 checkpoint name or path. In stage-2 / fine-tune flows it is commonly resolved under `log_dir` when a direct pretrained checkpoint is not supplied.
- `pretrained_model`: direct checkpoint path for initialization or resuming.
- `second_stage_load_pretrained`: when true, the stage-2 / fine-tune scripts load `pretrained_model` directly.
- `load_only_params`: when true, only model weights are restored; optimizer state and epoch counters are skipped.
- `F0_path`, `ASR_config`, `ASR_path`, `PLBERT_dir`: helper asset paths used while building the model.

### Data and preprocessing
- `data_params.train_data`: training list file.
- `data_params.val_data`: validation list file.
- `data_params.root_path`: wav root joined to the first column of every row.
- `data_params.OOD_data`: OOD text file.
- `data_params.min_length`: OOD resampling threshold in characters.
- `preprocess_params.sr`: expected audio sample rate; the shipped configs use `24000`.
- `preprocess_params.spect_params`: mel/STFT settings coupled to the 24 kHz assumption.

### Model and schedule
- `model_params.multispeaker`: switches the model between single-speaker and multispeaker behavior.
- `model_params.decoder.type`: `istftnet` or `hifigan`; the checkpoint family must match the decoder layout.
- `loss_params.TMA_epoch`: when stage-1 alignment losses begin.
- `loss_params.diff_epoch`: when diffusion-style training begins.
- `loss_params.joint_epoch`: when joint training begins and the decoder starts being tuned.
- `batch_size`: primary memory knob.
- `max_len`: maximum mel length in frames for training batches.
- `slmadv_params.min_len` / `max_len`: SLM-adversarial sample-length bounds.
- `slmadv_params.batch_percentage`: fraction of the batch kept for SLM-adversarial work to reduce OOM risk.
- `slmadv_params.iter`: discriminator update interval.
- `slmadv_params.thresh`, `scale`, `sig`: gradient scaling and differentiable duration controls.

### Optimizer knobs
- `optimizer_params.lr`: main learning rate.
- `optimizer_params.bert_lr`: PLBERT learning rate.
- `optimizer_params.ft_lr`: acoustic-module learning rate.

## Shipped config profiles

| Config | Intended use | Speaker mode | Decoder | Main schedule | Memory defaults | Checkpoint behavior |
| --- | --- | --- | --- | --- | --- | --- |
| `Configs/config.yml` | LJSpeech-style scratch training | single | `istftnet` | `epochs_1st=200`, `epochs_2nd=100`, `TMA_epoch=50`, `diff_epoch=20`, `joint_epoch=50` | `batch_size=16`, `max_len=400` | `first_stage_path=first_stage.pth`, `pretrained_model=""`, `load_only_params=false` |
| `Configs/config_libritts.yml` | LibriTTS-style multispeaker scratch training | multi | `hifigan` | `epochs_1st=50`, `epochs_2nd=30`, `TMA_epoch=5`, `diff_epoch=10`, `joint_epoch=15` | `batch_size=16`, `max_len=300` | `first_stage_path=first_stage.pth`, `pretrained_model=""`, `root_path=""` |
| `Configs/config_ft.yml` | Fine-tune from a pretrained multispeaker checkpoint | multi | `hifigan` | `epochs=50`, `diff_epoch=10`, `joint_epoch=30` | `batch_size=8`, `max_len=400` | `pretrained_model=Models/LibriTTS/epochs_2nd_00020.pth`, `second_stage_load_pretrained=true`, `load_only_params=true` |

## LJSpeech vs LibriTTS vs fine-tune deltas

### LJSpeech scratch config
- Single-speaker data.
- `decoder.type=istftnet` in the shipped config.
- Uses a concrete wav root under `data_params.root_path`.
- Longer stage-1 and stage-2 schedules.

### LibriTTS scratch config
- Multispeaker data.
- `decoder.type=hifigan` in the shipped config.
- Shorter stage-1 / stage-2 schedules.
- `root_path` is left empty in the shipped config because the row paths are expected to already carry the needed dataset prefix.

### Fine-tune config
- Starts from a pretrained multispeaker checkpoint.
- Keeps `model_params.multispeaker=true`.
- Uses a smaller `batch_size` and a higher acoustic learning rate.
- Sets `load_only_params=true` so transfer starts from weights only rather than restoring optimizer state.

## Memory-tuning notes

- Lower `batch_size` first when VRAM is tight.
- Then lower `max_len`.
- If SLM-adversarial training is the pressure point, lower `slmadv_params.batch_percentage`.
- `data_params.min_length` and `slmadv_params.min_len` are unrelated; one is text length for OOD sampling, the other is a frame-length bound for adversarial batches.
- `max_len` also appears in `slmadv_params`; that value belongs to the SLM-adversarial path, not the top-level batch clip.

## Checkpoint-path rules

- If `pretrained_model` is set and `second_stage_load_pretrained` is true, the stage-2 / fine-tune scripts load it directly.
- If `pretrained_model` is empty, the stage-2 / fine-tune scripts fall back to `first_stage_path` under `log_dir`.
- `load_only_params=true` is the safer choice for transfer or fine-tuning.
- `load_only_params=false` is only appropriate when you want to continue the exact optimizer / epoch state.
- Changing `multispeaker` or `decoder.type` after a checkpoint has been created can make checkpoint reuse fail or become partially incompatible.

## Sanity rules

- Keep `preprocess_params.sr` aligned with the audio data.
- Keep the list file format consistent with the selected speaker mode.
- Keep `root_path` and list paths consistent with one another.
- Keep `decoder.type` and checkpoint family aligned.
- Keep `pretrained_model` / `first_stage_path` semantics clear before starting a run.
