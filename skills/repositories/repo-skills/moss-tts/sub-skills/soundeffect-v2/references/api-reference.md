# MOSS-SoundEffect v2 API reference

## Package identity and dependency contract

- Package name: `moss-soundeffect-v2`.
- Import package: `moss_soundeffect_v2`.
- Runtime class: `MossSoundEffectPipeline`.
- Output container: `MossSoundEffectPipelineOutput`.
- Python requirement: `>=3.12`.
- The package is intentionally separate from the top-level MOSS-TTS dependency set.

Core pinned dependencies:

| Dependency | Pin |
|---|---:|
| `numpy` | `1.26.4` |
| `einops` | `0.8.2` |
| `pillow` | `12.2.0` |
| `tqdm` | `4.67.3` |
| `safetensors` | `0.7.0` |
| `transformers` | `4.57.1` |
| `diffusers` | `0.37.1` |
| `ftfy` | `6.3.1` |
| `regex` | `2026.4.4` |
| `soundfile` | `0.13.1` |
| `imageio` | `2.37.3` |
| `descript-audiotools` | `0.7.2` |
| `gradio` | `6.11.0` |

Optional extras:

| Extra | Adds |
|---|---|
| `torch-cu128` | `torch==2.9.0+cu128`, `torchaudio==2.9.0+cu128`, `torchvision==0.24.0+cu128`, `torchcodec==0.8.0` |
| `finetune` | `accelerate==1.13.0`, `peft==0.18.1`, `pandas==3.0.2`, `torchcodec==0.8.0` |

Install the CUDA extra with the PyTorch CUDA 12.8 wheel index:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-cu128]"
```

## Public model

Default public model id:

```text
OpenMOSS-Team/MOSS-SoundEffect-v2.0
```

Any local directory with the same Hugging Face-style layout may be used in place of the repo id.

## `MossSoundEffectPipeline.from_pretrained`

Signature:

```python
MossSoundEffectPipeline.from_pretrained(
    pretrained_model_name_or_path,
    torch_dtype=torch.bfloat16,
    device="cuda",
    **kwargs,
)
```

Arguments and behavior:

| Argument | Meaning |
|---|---|
| `pretrained_model_name_or_path` | Local model directory or Hugging Face repo id. |
| `torch_dtype` | Torch dtype for model loading; typical value is `torch.bfloat16`. |
| `device` | Device string or torch device. `"auto"` chooses CUDA if available, else CPU. A requested CUDA device falls back to CPU if CUDA is unavailable. |
| `cache_dir` | Optional Hugging Face cache directory passed to snapshot download. |
| `revision` | Optional Hugging Face revision passed to snapshot download. |
| `token` | Optional Hugging Face token passed to snapshot download. |
| `local_files_only` | If true, only use already-cached/local files. |

Model directory layout expectations:

- `model_index.json` may define `sample_rate` and `max_inference_seconds`.
- Missing `sample_rate` defaults to `48000`.
- Missing `max_inference_seconds` defaults to `30`.
- The underlying engine expects `transformer`, `vae`, `text_encoder`, `tokenizer`, and `scheduler` components.

## Pipeline properties

| Property | Meaning |
|---|---|
| `pipe.transformer` | DiT transformer object. |
| `pipe.vae` | DAC VAE object. |
| `pipe.text_encoder` | Qwen3 text encoder object. |
| `pipe.tokenizer` | Underlying tokenizer object. |
| `pipe.prompter` | Prompt encoder/prompter wrapper. |
| `pipe.scheduler` | Flow matching scheduler. |
| `pipe.device` | `torch.device` for the engine. |
| `pipe.dtype` | Torch dtype for the engine. |
| `pipe.sample_rate` | Output sample rate, normally `48000`. |
| `pipe.max_inference_seconds` | Maximum generated/cropped duration, normally `30`. |

`pipe.to(...)` forwards to the underlying engine and returns the pipeline.

## `MossSoundEffectPipeline.__call__`

Signature:

```python
pipe(
    prompt,
    seconds=10.0,
    num_inference_steps=100,
    cfg_scale=4.0,
    sigma_shift=5.0,
    seed=0,
    negative_prompt="",
    append_duration_suffix=True,
    num_channels=1,
    max_inference_seconds=None,
    return_dict=False,
    progress_bar_cmd=tqdm,
)
```

Argument contract:

| Argument | Meaning | Default |
|---|---|---:|
| `prompt` | String or list/tuple of strings. | required |
| `seconds` | Requested output duration, rounded to one decimal place. Must be `> 0` and no more than `max_inference_seconds`. | `10.0` |
| `num_inference_steps` | Number of diffusion solver steps. More steps cost more time/memory. | `100` |
| `cfg_scale` | Classifier-free guidance weight. | `4.0` |
| `sigma_shift` | Flow-match scheduler shift override. | `5.0` |
| `seed` | Integer RNG seed. | `0` |
| `negative_prompt` | Negative prompt used by CFG. | empty string |
| `append_duration_suffix` | If true, appends `duration: <seconds>s` to every prompt before encoding. | `True` |
| `num_channels` | Requested output channels; DAC path is normally mono. | `1` |
| `max_inference_seconds` | Optional override of the model maximum. | model value |
| `return_dict` | If true, return `MossSoundEffectPipelineOutput`. Otherwise return tensor. | `False` |
| `progress_bar_cmd` | Progress bar class/function; defaults to `tqdm`. | `tqdm` |

Output behavior:

- The engine denoises a full latent for `max_inference_seconds`, then crops the waveform to `seconds`.
- Tensor output shape is `(B, C, T)`.
- `T = int(pipe.sample_rate * seconds)` after cropping.
- With `return_dict=True`, output fields are `audios`, `sample_rate`, and formatted `prompts`.

Validation behavior:

- `seconds <= 0` raises `ValueError`.
- `seconds > max_inference_seconds` raises `ValueError`.

## `save_audio`

Signature:

```python
pipe.save_audio(audio, output_path, sample_rate=None)
```

Behavior:

- Detaches and moves audio to CPU.
- Converts 3D `(B, C, T)` audio to the first batch item.
- Converts 1D audio to one channel.
- Writes `float32` audio through torchaudio.
- Creates parent directories.
- Returns the resolved output path string.

## Inference entry point arguments

The inference entry point accepts:

| CLI argument | Environment-style counterpart | Default |
|---|---|---:|
| `--model_dir` | `MODEL_DIR` or `SOUNDEFFECT_MODEL_DIR` | required by Python entry point |
| `--prompt` | `PROMPT` | mechanical-keyboard example |
| `--seconds` | `SECONDS_` | `10.0` |
| `--steps` | `STEPS` | `100` |
| `--cfg_scale` | `CFG_SCALE` | `4.0` |
| `--sigma_shift` | `SIGMA_SHIFT` | `5.0` |
| `--seed` | `SEED` | `0` |
| `--device` | `DEVICE` | `cuda` |
| `--torch_dtype` | `TORCH_DTYPE` | `bfloat16` |
| `--output` | `OUTPUT` | `output_pipeline.wav` or wrapper-defined output path |

`--torch_dtype` choices are `float32`, `float16`, and `bfloat16`.

## Gradio API surface

Environment variables:

| Variable | Meaning | Default |
|---|---|---:|
| `SOUNDEFFECT_MODEL_DIR` | Model repo id or local directory. | placeholder path in code; override it |
| `SOUNDEFFECT_DEVICE` | Requested device. | `cuda` |
| `GRADIO_ROOT_PATH` | Optional reverse-proxy mount path. | unset |

CLI arguments:

| Argument | Default |
|---|---:|
| `--model_dir` | `SOUNDEFFECT_MODEL_DIR` |
| `--device` | `SOUNDEFFECT_DEVICE` |
| `--host` | `0.0.0.0` |
| `--port` | `7861` |
| `--root_path` | `GRADIO_ROOT_PATH` |
| `--share` | false |

UI constraints:

| Parameter | Range/default |
|---|---|
| duration | 1 to 30 seconds, step 0.1, default 10 |
| steps | 10 to 150, default 100 |
| `cfg_scale` | 1.0 to 8.0, default 4.0 |
| `sigma_shift` | 0.0 to 10.0, default 5.0 |
| seed | integer, default 0 |

## Fine-tuning metadata schema

Required JSONL fields:

| Field | Type | Requirement |
|---|---|---|
| `audio` | string | Non-empty path to an audio file readable by the dataset loader. |
| `prompt` | string | Non-empty caption text. English and Chinese prompts are both supported. |

Useful optional fields:

| Field | Type | Meaning |
|---|---|---|
| `start_time` | number/string | Optional segment start in seconds. |
| `end_time` | number/string | Optional segment end in seconds. |
| `audio_latent` | string | Optional precomputed latent path for latent workflows. |

Audio loader behavior:

- Recognized audio extensions include `wav`, `mp3`, `flac`, `ogg`, `m4a`, `aac`, `wma`, `mp4`, `aiff`, and `wv`.
- SoundFile decoding is attempted first; ffmpeg-to-WAV fallback is used for formats SoundFile cannot read.
- Audio can be resampled, made mono, cropped, and padded according to training arguments.
- With append-duration enabled, the loader can append `duration: <seconds>s` to prompts using computed audio duration.

## Fine-tuning Python arguments

Required core arguments:

| Argument | Meaning |
|---|---|
| `--hf_model_dir` | Source HF directory or repo id to fine-tune from. |
| `--dataset_base_path` | Dataset base path used by metadata/path handling. |
| `--dataset_metadata_path` | JSON, JSONL, or CSV metadata path. |
| `--output_path` | Training output directory. |

Common data arguments:

| Argument | Default | Meaning |
|---|---:|---|
| `--sample_rate` | `48000` | Target audio sample rate. |
| `--num_audio_samples` | `1440000` | Fixed audio length, 30s at 48 kHz. |
| `--min_num_audio_samples` | `960` | Minimum sample count. |
| `--max_num_audio_samples` | `1440000` | Maximum sample count. |
| `--mono` | false unless flag set | Convert to mono. |
| `--data_file_keys` | `audio` in the shell launch | Metadata file fields to load as data. |
| `--dataset_repeat` | `1` | Dataset repeat count. |
| `--dataset_num_workers` | `4` | Loader/cache workers. |
| `--drop_prompt_prob` | `0.1` | Randomly replace prompt with empty prompt for CFG training. |
| `--append_duration_suffix` | false unless flag set | Append duration suffix from audio duration. |
| `--append_duration_suffix_prob` | `0.5` | Probability of appending duration suffix. |
| `--duration_precision` | `1` | Decimal places for duration suffix. |

Common training arguments:

| Argument | Default |
|---|---:|
| `--learning_rate` | `1e-5` |
| `--weight_decay` | `0.01` |
| `--batch_size` | `1` |
| `--gradient_accumulation_steps` | `1` |
| `--num_epochs` | `5` |
| `--save_steps` | `None` |
| `--clip_grad_norm` | `0.1` |
| `--trainable_models` | `dit` |
| `--remove_prefix_in_ckpt` | `pipe.dit.` |
| `--use_gradient_checkpointing_offload` | false unless flag set |
| `--find_unused_parameters` | false unless flag set |
| `--max_timestep_boundary` | `1.0` |
| `--min_timestep_boundary` | `0.0` |
| `--extra_inputs` | `None` |
| `--log_dir` | `None` |
| `--resume_from` | `None` |

Cache/export arguments:

| Argument | Default | Meaning |
|---|---:|---|
| `--cache_folder` | `None` | VAE/text-context cache location. |
| `--cache_first` | false unless flag set | Build cache before training. Requires `--cache_folder`. |
| `--cache_num_shards` | `64` | Number of cache shards. |
| `--skip_first_batches` | `0` | Cache-generation skip. |
| `--no_export_hf` | false unless flag set | Disable automatic HF-format export after training. |
| `--export_hf_dir` | `None` | Override default HF export directory. |

Training creates `.safetensors` DiT checkpoints in the output directory. If export is enabled, the latest checkpoint is exported into `hf_format` or `--export_hf_dir`.

## Export API

Python function:

```python
from moss_soundeffect_v2.hf_export import export_finetuned_to_hf

export_finetuned_to_hf(
    ckpt_path="epoch-0.safetensors",
    source_hf_dir="OpenMOSS-Team/MOSS-SoundEffect-v2.0",
    dst_dir="hf_format_epoch0",
)
```

Export CLI arguments:

| Argument | Meaning |
|---|---|
| `--ckpt_path` | Fine-tuned DiT `.safetensors` checkpoint. |
| `--source_hf_dir` | Source HF directory or repo id containing frozen modules. |
| `--output_dir` | Destination HF-style model directory. |

Output layout:

```text
output_dir/
  model_index.json                  # copied when present
  transformer/
    config.json                     # copied when present
    diffusion_pytorch_model.safetensors
  vae/
  text_encoder/
  tokenizer/
  scheduler/
```

The export converts DiT checkpoint key names, writes the transformer safetensors file, and copies the frozen non-DiT modules from the source model unchanged.
