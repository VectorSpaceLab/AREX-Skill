# API reference

## Runtime signatures
- `ClearVoice(task, model_names)`
- `__call__(input_path, online_write=False, output_path=None)`
- `write(results, output_path)`

## Constructor
- `task` must be one of `speech_enhancement`, `speech_separation`, `speech_super_resolution`, or `target_speaker_extraction`.
- Pass `model_names` as a list or other sequence of valid names. Do not pass a bare string; the implementation iterates the value and would treat characters as model names.
- File-mode inference can use several models at once. Tensor-to-tensor inference can use only one model.

## Call modes
- A string `input_path` selects file, directory, or `.scp` inference.
- A `numpy.ndarray` or `torch.Tensor` selects tensor-to-tensor inference.
- `online_write=False` returns arrays or dictionaries in memory.
- `online_write=True` writes results to disk and returns nothing.
- `target_speaker_extraction` is video-driven and requires `online_write=True`.

## Returns
- A single audio file with one model may return one array.
- Multiple files or multiple models may return a dictionary keyed by model name or utterance id.
- Speech separation returns stacked speaker outputs with shape `[num_spks, batch, length]`.
- Audio-only tensor mode expects input shape `[batch, length]`.

## `write(results, output_path)`
- Use this after offline inference.
- Use a fresh file path for a single result, or a directory for batch outputs.
- The library refuses to overwrite existing targets.

## Task and model coverage
| Task | Model | Rate | File mode | Tensor mode | Notes |
| --- | --- | --- | --- | --- | --- |
| `speech_enhancement` | `FRCRN_SE_16K` | 16 kHz | yes | yes | Good default for 16 kHz denoising. |
| `speech_enhancement` | `MossFormer2_SE_48K` | 48 kHz | yes | yes | Full-band enhancement model. |
| `speech_enhancement` | `MossFormerGAN_SE_16K` | 16 kHz | yes | yes | GAN-based enhancement model. |
| `speech_separation` | `MossFormer2_SS_16K` | 16 kHz | yes | yes | Returns two separated speakers. |
| `speech_super_resolution` | `MossFormer2_SR_48K` | 48 kHz | yes | yes | Uses a paired YAML plus JSON inference config. |
| `target_speaker_extraction` | `AV_MossFormer2_TSE_16K` | 16 kHz | yes | no | Requires video input and `online_write=True`. |

## No-download validation
- The bundled inference configs for `FRCRN_SE_16K`, `MossFormer2_SE_48K`, `MossFormer2_SR_48K`, `MossFormer2_SS_16K`, and `AV_MossFormer2_TSE_16K` can be parsed without loading checkpoint weights.
- Use that parse-only path to confirm the environment before allowing checkpoint downloads.

## Version note
- The installed distribution version may differ from the source `__version__` string. Use the live API and this catalog instead of trusting the version string alone.
