# Model catalog

Use this catalog to choose a ClearVoice model before calling the helper scripts or the runtime API. Pass one model in tensor-to-tensor mode. File-mode inference may chain several models.

| Task | Model | Input rate | Input mode | Output shape | Checkpoint family | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `speech_enhancement` | `FRCRN_SE_16K` | 16 kHz | file, directory, `.scp`, NumPy/Tensor | audio array | `FRCRN_SE_16K` | Safe default for classic denoising. |
| `speech_enhancement` | `MossFormer2_SE_48K` | 48 kHz | file, directory, `.scp`, NumPy/Tensor | audio array | `MossFormer2_SE_48K` | Full-band enhancement model. |
| `speech_enhancement` | `MossFormerGAN_SE_16K` | 16 kHz | file, directory, `.scp`, NumPy/Tensor | audio array | `MossFormerGAN_SE_16K` | GAN-based enhancement path. |
| `speech_separation` | `MossFormer2_SS_16K` | 16 kHz | file, directory, `.scp`, NumPy/Tensor | `[num_spks, batch, length]` | `MossFormer2_SS_16K` | Two-speaker separation only. |
| `speech_super_resolution` | `MossFormer2_SR_48K` | 48 kHz | file, directory, `.scp`, NumPy/Tensor | audio array | `MossFormer2_SR_48K` | Uses the paired YAML and JSON inference config. |
| `target_speaker_extraction` | `AV_MossFormer2_TSE_16K` | 16 kHz | file, directory, `.scp` of videos | video-driven output | `AV_MossFormer2_TSE_16K` | AV lip-based extraction; requires `online_write=True`. |

## Input format notes
- Audio file mode accepts common audio extensions such as wav, aac, ac3, aiff, flac, m4a, mp3, ogg, opus, wma, and webm.
- AV TSE file mode accepts video inputs such as avi, mp4, mov, and webm.
- Non-WAV audio and all video paths depend on FFmpeg through the audio/video loaders.

## Selection notes
- Pick the model that matches the source sample rate before you try to run it.
- Use a single model for tensor input.
- Use several models only in file-mode inference.
