# MOSS-TTS Local v1.5 batch and streaming workflows

This reference is self-contained operating guidance for MOSS-TTS-Local-Transformer-v1.5. It covers local batch decode and the realtime streaming app for the v1.5 checkpoint with MOSS-Audio-Tokenizer-v2.

## Model and audio contract

| Item | Value |
|---|---|
| TTS checkpoint | `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5` |
| Codec/tokenizer | `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2` |
| Audio | 48 kHz stereo |
| Frame rate | 12.5 frames/sec; 125 frames is about 10 sec |
| RVQ depth | 12 layers, fixed by the model config |
| Backbone | Qwen3-4B-derived local-transformer release |
| Generation topology | Time-synchronous autoregressive frames: one frame row contains all 12 RVQ layer values |

Decoded v1.5 audio is already channel-first stereo (`[2, samples]`). Save it directly with the runtime sample rate; do not add an extra channel dimension as older mono examples might do.

## Batch inference pattern

Use the processor to build conversations and the model to generate audio frames. Keep the codec on the same device as the processor unless you deliberately split devices in the streaming runtime.

```python
from pathlib import Path
import importlib.util

import torch
import torchaudio
from transformers import AutoModel, AutoProcessor

MODEL_ID = "OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5"

torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32

def resolve_attn_implementation() -> str:
    if (
        device == "cuda"
        and importlib.util.find_spec("flash_attn") is not None
        and dtype in {torch.float16, torch.bfloat16}
    ):
        major, _ = torch.cuda.get_device_capability()
        if major >= 8:
            return "flash_attention_2"
    return "sdpa" if device == "cuda" else "eager"

processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
processor.audio_tokenizer = processor.audio_tokenizer.to(device)

model = AutoModel.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    attn_implementation=resolve_attn_implementation(),
    torch_dtype=dtype,
).to(device)
model.eval()

conversations = [
    # Direct TTS with a known language tag.
    [processor.build_user_message(text="亲爱的你，愿你的每一天都值得被记住。", language="Chinese")],
    # Voice clone: add one or more reference audio paths/URLs.
    [processor.build_user_message(text="This is a cloned voice test.", reference=["reference.wav"], language="English")],
    # Duration control: tokens are expected audio frames. 125 frames ≈ 10 sec at 12.5 Hz.
    [processor.build_user_message(text="A ten second English sample.", tokens=125, language="English")],
    # Pause control inside text.
    [processor.build_user_message(text="第一句。[pause 3.2s]第二句。", language="Chinese")],
]

save_dir = Path("chosen_output")
save_dir.mkdir(parents=True, exist_ok=True)

with torch.no_grad():
    for sample_idx, conversation in enumerate(conversations):
        batch = processor([conversation], mode="generation")
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=4096,
            do_sample=True,
            audio_temperature=1.7,
            audio_top_p=0.8,
            audio_top_k=25,
            audio_repetition_penalty=1.0,
        )
        for message in processor.decode(outputs):
            if message is None or not message.audio_codes_list:
                continue
            audio = message.audio_codes_list[0]  # [2, samples]
            torchaudio.save(str(save_dir / f"sample{sample_idx}.wav"), audio, processor.model_config.sampling_rate)
```

### Continuation with prefix audio

Continuation is not the same as voice cloning. It conditions on a prompt audio prefix and the transcript of that prefix, then generates only the continuation after the prefix.

```python
reference_transcript = "太阳系八大行星之一。"
continuation_text = "亲爱的你，你好呀。今天我想用最温柔的声音说一些话。"
reference_audio = "reference_zh.wav"

conversation = [
    processor.build_user_message(text=reference_transcript + continuation_text, language="Chinese"),
    processor.build_assistant_message(audio_codes_list=[reference_audio]),
]

batch = processor([conversation], mode="continuation")
outputs = model.generate(
    input_ids=batch["input_ids"].to(device),
    attention_mask=batch["attention_mask"].to(device),
    max_new_tokens=4096,
    do_sample=True,
    audio_temperature=1.7,
    audio_top_p=0.8,
    audio_top_k=25,
    audio_repetition_penalty=1.0,
)
```

Rules for continuation:

- Provide exactly one prompt audio item for the continuation prefix.
- The user text should include the reference transcript followed by the new text to continue.
- The transcript must match the reference audio closely; missing or mismatched transcripts cause unstable timing and speaker continuation.
- Use `mode="continuation"`; use `mode="generation"` for direct generation and voice clone.

## Realtime streaming app

The web app wraps a FastAPI server and browser Web Audio playback. Generation produces frames while a codec worker decodes chunks to PCM. This skill does not bundle the full web app; when operating a user's MOSS-TTS checkout, launch the Local v1.5 streaming app or equivalent service with the v1.5 model, v2 codec IDs, and explicit device choices:

```bash
MODEL_DIR=OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5 \
CODEC_DIR=OpenMOSS-Team/MOSS-Audio-Tokenizer-v2 \
TTS_DEVICE=cuda:0 \
CODEC_DEVICE=cuda:1 \
CODEC_WEIGHT_DTYPE=fp32 \
<run the Local v1.5 streaming app launcher in the user's checkout>
```

Equivalent direct app option contract:

```bash
python <local-v15-web-app-entrypoint> \
  --model-dir OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5 \
  --codec-dir OpenMOSS-Team/MOSS-Audio-Tokenizer-v2 \
  --tts-device cuda:0 \
  --codec-device cuda:1 \
  --codec-weight-dtype fp32
```

Important app knobs:

| Knob | Meaning | Default behavior |
|---|---|---|
| `TTS_DEVICE`, `--tts-device` | Device for Qwen3-4B-derived TTS model | GPU is expected for realtime use |
| `CODEC_DEVICE`, `--codec-device` | Device for codec v2 encoder/decoder | Can share TTS GPU or use a second GPU |
| `TTS_DTYPE`, `--dtype` | TTS model weight dtype | `bfloat16` on CUDA-oriented runs |
| `ATTN_IMPLEMENTATION`, `--attn-implementation` | Requested attention backend | Request `flash_attention_2`; runtime falls back if unsupported |
| `CODEC_WEIGHT_DTYPE`, `--codec-weight-dtype` | Codec encoder/decoder parameter dtype | `fp32` is stable; `bf16` lowers memory |
| `CODEC_COMPUTE_DTYPE`, `--codec-compute-dtype` | Codec non-quantizer compute dtype | `bf16` by default |
| `HOST`, `PORT` | Web app bind address | configurable |
| `OUTPUT_DIR`, `UPLOAD_DIR` | Where final runs and uploaded references are stored | `OUTPUT_DIR` defaults to `outputs/moss_tts_local_v1_5_streaming`; both are configurable |

### App modes

- **Direct Generation**: no reference audio is supplied; the app automatically generates from text only.
- **Clone**: reference audio is supplied and mode is clone; the reference is inserted as user-side speaker/style conditioning.
- **Continuation**: reference audio plus Reference Audio Transcript are supplied; the model continues after the reference prefix.
- **Continuation + Clone**: app-level mode with the same hard requirement as continuation: reference audio plus matching transcript.

The app validates continuation modes before job creation: if reference audio is present and the mode is continuation-like, the Reference Audio Transcript field must be non-empty.

### Streaming chunks and progress

- `max_new_tokens` in the browser UI is the hard frame limit passed internally as `max_new_frames`.
- `codec_chunk_frames` controls how many generated frames are decoded per codec call. `0` enables adaptive scheduling. UI range is 0-32; the app default is 8.
- Initial playback delay defaults to 0.08 sec in the browser.
- The streaming response is raw 16-bit little-endian PCM with 2 channels and 48 kHz sample rate.
- Final result includes a WAV, a tensor file of generated audio-frame IDs, and a metadata JSON. The launcher default is `outputs/moss_tts_local_v1_5_streaming`; change it with `OUTPUT_DIR` or `--output-dir`.

Use `scripts/estimate_local_v15_tokens.py` when deciding a duration-control value or a `max_new_frames`/UI `max_new_tokens` cap without importing torch or loading a model.
