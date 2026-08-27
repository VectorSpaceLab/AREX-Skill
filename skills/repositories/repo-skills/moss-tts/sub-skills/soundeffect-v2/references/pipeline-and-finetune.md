# MOSS-SoundEffect v2 pipeline, demo, fine-tuning, and export

This reference is the operational path for MOSS-SoundEffect v2.0. It is separate from Delay-family MOSS-SoundEffect v1 and from generic MOSS-TTS voice cloning.

## What v2 is

MOSS-SoundEffect v2.0 is a text-to-audio model with:

- a Diffusion Transformer (DiT) backbone,
- Flow Matching training/inference objective,
- DAC VAE audio representation,
- Qwen3 text encoder,
- a diffusers-style `MossSoundEffectPipeline` wrapper.

The public model id is `OpenMOSS-Team/MOSS-SoundEffect-v2.0`. A local Hugging Face-style directory with the same layout can be used instead.

## Isolated environment

Use a fresh Python 3.12+ environment. This package pins dependencies that are not compatible with the top-level MOSS-TTS environment.

Core runtime pins include:

- `numpy==1.26.4`
- `transformers==4.57.1`
- `diffusers==0.37.1`
- `gradio==6.11.0`
- `soundfile==0.13.1`
- `descript-audiotools==0.7.2`

For CUDA 12.8, install the package with the PyTorch wheel index so the `torch-cu128` extra can resolve:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 \
  -e ".[torch-cu128]"
```

For fine-tuning, include the fine-tuning extra as well:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 \
  -e ".[torch-cu128,finetune]"
```

The CUDA extra pins:

- `torch==2.9.0+cu128`
- `torchaudio==2.9.0+cu128`
- `torchvision==0.24.0+cu128`
- `torchcodec==0.8.0`

Fine-tuning extras include `accelerate==1.13.0`, `peft==0.18.1`, `pandas==3.0.2`, and `torchcodec==0.8.0`.

## Minimal pipeline inference

Use the package pipeline directly:

```python
import torch
from moss_soundeffect_v2 import MossSoundEffectPipeline

pipe = MossSoundEffectPipeline.from_pretrained(
    "OpenMOSS-Team/MOSS-SoundEffect-v2.0",  # or a local HF-style directory
    torch_dtype=torch.bfloat16,
    device="cuda",
)

audio = pipe(
    prompt="The crisp, rhythmic click-clack of fast typing on a mechanical keyboard.",
    seconds=10,
    num_inference_steps=100,
    cfg_scale=4.0,
)
pipe.save_audio(audio, "out.wav")
```

Expected observations:

- `from_pretrained` accepts a Hugging Face repo id or a local directory.
- The first hub use downloads into the Hugging Face cache.
- The pipeline returns a waveform tensor shaped like `(B, C, T)`.
- The default sample rate is 48 kHz unless overridden by `model_index.json`.
- `save_audio` writes the first item/channel-normalized tensor to a WAV path through torchaudio.

## Bounded smoke-test settings

For a fast functionality check, reduce duration and solver steps:

```python
audio = pipe(
    prompt="A short wooden door knock in a quiet hallway.",
    seconds=1.0,
    num_inference_steps=10,
    cfg_scale=4.0,
    seed=0,
)
```

This is only a smoke test. Quality checks should use task-appropriate prompts and stronger settings such as 10 seconds and 100 steps when resources permit.

## TorchDynamo/Triton compile recovery

The DiT path may use `torch.compile` and Triton/CUDA Graph acceleration. First use can take minutes. If compilation fails, disable TorchDynamo before launching Python:

```bash
TORCHDYNAMO_DISABLE=1 python - <<'PY'
import torch
from moss_soundeffect_v2 import MossSoundEffectPipeline
pipe = MossSoundEffectPipeline.from_pretrained(
    "OpenMOSS-Team/MOSS-SoundEffect-v2.0",
    torch_dtype=torch.bfloat16,
    device="cuda",
)
audio = pipe("A single camera shutter click.", seconds=1.0, num_inference_steps=10)
pipe.save_audio(audio, "out.wav")
PY
```

## CLI-style inference variables

A typical shell wrapper maps environment variables to the Python inference entry point:

- `MODEL_DIR` or `SOUNDEFFECT_MODEL_DIR`: HF repo id or local model directory.
- `PROMPT`: generation prompt.
- `SECONDS_`: requested duration, default `10.0`.
- `STEPS`: diffusion steps, default `100`.
- `CFG_SCALE`: classifier-free guidance scale, default `4.0`.
- `SIGMA_SHIFT`: scheduler sigma shift, default `5.0`.
- `SEED`: integer seed, default `0`.
- `DEVICE`: device string, default `cuda`.
- `TORCH_DTYPE`: one of `float32`, `float16`, `bfloat16`; default `bfloat16`.
- `OUTPUT`: output WAV path.

Equivalent direct command pattern:

```bash
export MODEL_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0
export PROMPT="Mechanical keyboard typing in a small room."
export SECONDS_=10.0 STEPS=100 CFG_SCALE=4.0 SIGMA_SHIFT=5.0 SEED=0 DEVICE=cuda TORCH_DTYPE=bfloat16
TORCHDYNAMO_DISABLE=1 python -m moss_soundeffect_v2.infer_from_pipeline \
  --model_dir "$MODEL_DIR" \
  --prompt "$PROMPT" \
  --seconds "$SECONDS_" \
  --steps "$STEPS" \
  --cfg_scale "$CFG_SCALE" \
  --sigma_shift "$SIGMA_SHIFT" \
  --seed "$SEED" \
  --device "$DEVICE" \
  --torch_dtype "$TORCH_DTYPE" \
  --output "out.wav"
```

## Gradio demo

The demo preloads one backend and serves a queued UI. Configure it with environment variables or equivalent CLI arguments:

```bash
SOUNDEFFECT_MODEL_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0 \
SOUNDEFFECT_DEVICE=cuda \
TORCHDYNAMO_DISABLE=1 \
python -m clis.moss_sound_effect_app --host 0.0.0.0 --port 7861
```

Operational facts:

- `SOUNDEFFECT_MODEL_DIR` defaults the model path/repo id.
- `SOUNDEFFECT_DEVICE` defaults the requested device; the backend falls back to CPU if CUDA is unavailable.
- `--model_dir` and `--device` override the defaults.
- `--root_path` can be supplied directly or through `GRADIO_ROOT_PATH` for reverse-proxy deployments.
- `--share` enables Gradio sharing.
- The UI constrains duration to 1-30 seconds, steps to 10-150, `cfg_scale` to 1.0-8.0, and `sigma_shift` to 0.0-10.0.
- Queue concurrency is one generation at a time; long generations block later requests.

## Fine-tuning metadata

Fine-tuning consumes JSON Lines where every row has at least:

```jsonl
{"audio": "wavs/birdsong.wav", "prompt": "清晨小鸟叽叽喳喳地叫着，叫声清脆悦耳。"}
{"audio": "wavs/brushing_teeth.wav", "prompt": "刷牙的声音，牙刷毛摩擦牙齿的那种沙沙声。"}
{"audio": "wavs/pouring_water.wav", "prompt": "Pouring water into a glass, clear liquid flowing sound, pitch rising as the glass fills up, refreshing."}
```

Rules:

- `audio` must be a non-empty string pointing to an audio file the training process can open.
- `prompt` must be a non-empty English or Chinese caption string.
- Relative audio paths should be interpreted relative to the dataset base used by the training launch or resolved to absolute paths before training.
- Optional segment fields `start_time` and `end_time` can be present when the dataset loader should read a bounded clip.
- Optional `audio_latent` can be present for precomputed latent workflows, but ordinary audio-file fine-tuning uses `audio`.

Before training, validate JSONL structure and paths with the bundled validator:

```bash
# From this sub-skill directory, or replace <this sub-skill> with its installed path.
python scripts/validate_soundeffect_metadata.py \
  --metadata captions.jsonl \
  --dataset-base ./soundeffects \
  --check-audio-exists \
  --json
```

## Fine-tuning launch

A full-parameter DiT fine-tune starts from an existing HF model directory or repo id:

```bash
HF_MODEL_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0 \
METADATA_PATH=./soundeffects/captions.jsonl \
OUTPUT_PATH=./output/my_finetune \
TORCHDYNAMO_DISABLE=1 \
<run the SoundEffect v2 fine-tuning launcher in the user's training checkout>
```

Important defaults and knobs:

- Mixed precision: `accelerate launch --mixed_precision bf16`.
- Dataset audio length: 48 kHz, 30 seconds (`NUM_AUDIO_SAMPLES=1440000`).
- Minimum/maximum audio samples: `960` / `1440000`.
- Mono conversion is enabled by the shell launch.
- `BATCH_SIZE=1`, `GRADIENT_ACCUMULATION_STEPS=1`, `NUM_EPOCHS=5` by default.
- Optimizer defaults: `LEARNING_RATE=1e-5`, `WEIGHT_DECAY=0.01`, `CLIP_GRAD_NORM=0.1`.
- Trainable component defaults to `TRAINABLE_MODELS=dit`.
- Checkpoint key prefix removal defaults to `REMOVE_PREFIX_IN_CKPT=pipe.dit.`.
- A one-shot VAE + text-encoder cache is enabled unless `NO_CACHE=1` is set.
- Training auto-exports the latest `.safetensors` checkpoint to `hf_format` under the output directory unless HF export is disabled in the Python arguments.

For manual Python launches, preserve the required model/data/output arguments:

```bash
accelerate launch --mixed_precision bf16 finetuning/finetuning.py \
  --hf_model_dir "$HF_MODEL_DIR" \
  --dataset_base_path "$DATASET_BASE" \
  --dataset_metadata_path "$METADATA_PATH" \
  --sample_rate 48000 \
  --num_audio_samples 1440000 \
  --min_num_audio_samples 960 \
  --max_num_audio_samples 1440000 \
  --mono \
  --data_file_keys audio \
  --append_duration_suffix \
  --duration_precision 1 \
  --trainable_models dit \
  --remove_prefix_in_ckpt pipe.dit. \
  --output_path "$OUTPUT_PATH"
```

## Export a fine-tuned checkpoint

Use export when you need to package an intermediate or manually selected DiT `.safetensors` checkpoint into a directory loadable by `MossSoundEffectPipeline.from_pretrained`:

```bash
CKPT_PATH=./output/my_finetune/epoch-0.safetensors \
SOURCE_HF_DIR=OpenMOSS-Team/MOSS-SoundEffect-v2.0 \
OUTPUT_DIR=./output/finetune/hf_format_epoch0 \
<run the SoundEffect v2 export helper in the user's training checkout>
```

Export behavior:

- Replaces only the DiT transformer weights using converted key names.
- Copies `transformer/config.json` from the source model when present.
- Copies frozen `vae`, `text_encoder`, `tokenizer`, and `scheduler` subdirectories from `SOURCE_HF_DIR` unchanged.
- Copies `model_index.json` from `SOURCE_HF_DIR` when present.
- Accepts a local source directory or a Hugging Face repo id; a repo id is resolved through the Hugging Face cache.
- The exported directory is then usable as `MossSoundEffectPipeline.from_pretrained(OUTPUT_DIR)`.
