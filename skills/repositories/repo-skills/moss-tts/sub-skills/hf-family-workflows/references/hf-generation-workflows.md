# Hugging Face generation workflows

This reference gives self-contained recipes for the MOSS-TTS family workflows that use Hugging Face remote code. The snippets are meant to be adapted into task code; they do not require opening repository examples or docs.

## Model and workflow chooser

| User need | Model ID | Architecture | Primary fields | Processor mode | Recommended audio sampling |
|---|---|---|---|---|---|
| Production single-speaker TTS, stable cloning, language tags, pause markers | `OpenMOSS-Team/MOSS-TTS-v1.5` | `MossTTSDelay`, 8B | `text`, optional `language`, `reference`, `tokens` | `generation` or `continuation` | `audio_temperature=1.7`, `audio_top_p=0.8`, `audio_top_k=25`, `audio_repetition_penalty=1.0` |
| Original MOSS-TTS 1.0 compatibility | `OpenMOSS-Team/MOSS-TTS` | `MossTTSDelay`, 8B | same as v1.5, but fewer languages and no v1.5 pause/clone improvements | `generation` or `continuation` | same as Delay v1.5 |
| Local Transformer non-streaming research/eval | `OpenMOSS-Team/MOSS-TTS-Local-Transformer` | `MossTTSLocal`, 1.7B | same high-level `text`, `reference`, `tokens`, `language` fields | `generation` or `continuation` | `audio_temperature=1.0`, `audio_top_p=0.95`, `audio_top_k=50`, `audio_repetition_penalty=1.1` |
| Local Transformer v1.5 non-streaming batch | `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5` | `MossTTSLocal`, 4B, 48 kHz stereo codec | same high-level fields; streaming details are owned by the sibling local-v1.5 skill | `generation` or `continuation` | `audio_temperature=1.7`, `audio_top_p=0.8`, `audio_top_k=25`, `audio_repetition_penalty=1.0` |
| Multi-speaker dialogue continuation | `OpenMOSS-Team/MOSS-TTSD-v1.0` | `MossTTSDelay`, 8B, TTSD-specific 16-codebook checkpoint | `text` with `[Sx]` tags, encoded per-speaker `reference`, assistant prompt audio | `continuation` when cloning; `generation` when no prompt audio | `audio_temperature=1.1`, `audio_top_p=0.9`, `audio_top_k=50`, `audio_repetition_penalty=1.1` |
| Text-described voice design, no reference audio | `OpenMOSS-Team/MOSS-VoiceGenerator` | `MossTTSDelay`, 1.7B | `text`, required `instruction` | `generation` | `audio_temperature=1.5`, `audio_top_p=0.6`, `audio_top_k=50`, `audio_repetition_penalty=1.1` |
| Sound effect v1 through Delay remote code | `OpenMOSS-Team/MOSS-SoundEffect` | `MossTTSDelay`, 8B | `ambient_sound`, optional `tokens` | `generation` | `audio_temperature=1.5`, `audio_top_p=0.6`, `audio_top_k=50`, `audio_repetition_penalty=1.2` |

Route MOSS-SoundEffect-v2.0 DiT/Flow-Matching requests to `../soundeffect-v2/SKILL.md`; it is not the Delay-family v1 workflow above.

## Common runtime setup

Install a runtime profile that includes PyTorch, Transformers, torchaudio, torchcodec, and FFmpeg. The package metadata advertises a `torch-runtime` extra pinned for CUDA 12.8, but match the PyTorch wheel index to the target backend.

```bash
python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime]"
# Optional speed path on supported CUDA GPUs:
python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime,flash-attn]"
```

FFmpeg is required by audio I/O stacks used by `torchcodec`/`torchaudio` in common deployments:

```bash
# Debian/Ubuntu
sudo apt-get install -y ffmpeg
# macOS
brew install ffmpeg
```

Use this attention/dtype resolver in generation scripts:

```python
import importlib.util
import torch

# Avoid the known-bad cuDNN SDPA path while keeping other kernels available.
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
        major, _minor = torch.cuda.get_device_capability()
        if major >= 8:
            return "flash_attention_2"
    if device == "cuda":
        return "sdpa"
    return "eager"
```

For Transformers versions that warn about `torch_dtype`, use the equivalent `dtype=dtype` keyword when loading the model.

## Direct MOSS-TTS generation

Use direct generation when there is no prefix audio and no continuation transcript.

```python
from pathlib import Path
import torch
import torchaudio
from transformers import AutoModel, AutoProcessor

model_id = "OpenMOSS-Team/MOSS-TTS-v1.5"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
processor.audio_tokenizer = processor.audio_tokenizer.to(device)

conversation = [[
    processor.build_user_message(
        text="Bonjour, je voudrais essayer une voix française naturelle et stable.",
        language="French",       # strongly recommended for known v1.5 non-ZH/EN language
        tokens=None,              # optional expected duration tokens; see below
    )
]]

model = AutoModel.from_pretrained(
    model_id,
    trust_remote_code=True,
    attn_implementation=resolve_attn_implementation(),
    torch_dtype=dtype,
).to(device).eval()

batch = processor(conversation, mode="generation")
with torch.no_grad():
    outputs = model.generate(
        input_ids=batch["input_ids"].to(device),
        attention_mask=batch["attention_mask"].to(device),
        max_new_tokens=4096,
        audio_temperature=1.7,
        audio_top_p=0.8,
        audio_top_k=25,
        audio_repetition_penalty=1.0,
    )

message = processor.decode(outputs)[0]
audio = message.audio_codes_list[0]
if audio.ndim == 1:
    audio = audio.unsqueeze(0)
Path("outputs").mkdir(exist_ok=True)
torchaudio.save("outputs/moss_tts.wav", audio.detach().cpu().to(torch.float32), processor.model_config.sampling_rate)
```

### Prompt controls

- **Language tags:** v1.5 supports 31 language labels. Use the natural language label accepted by the demo/API, for example `language="French"`, not a BCP-47 code. If unsure, omit the field rather than inventing a tag.
- **Pinyin:** MOSS-TTS accepts tone-numbered Pinyin directly, e.g. `nin2 hao3，qing3 wen4 nin2 lai2 zi4 na3 zuo4 cheng2 shi4？`.
- **IPA:** wrap IPA in slashes, e.g. `/həloʊ, meɪ aɪ æsk wɪtʃ sɪti juː ɑːr frʌm?/`.
- **Mixed text/Pinyin/IPA:** mixing is allowed when you need targeted pronunciation control, e.g. `您好，请问您来自哪 zuo4 cheng2 shi4？`.
- **Explicit pauses:** v1.5 supports inline pause markers such as `[pause 3.2s]`: `我今天学习了一首中国的古诗，它的名字是[pause 3.2s]静夜思！`.
- **Duration tokens:** pass `tokens=<int>` to `build_user_message`; approximately `1 second ≈ 12.5 audio tokens`. Do not combine duration control with continuation modes in the Gradio-style workflow.

Use `scripts/normalize_tts_text.py` before generation when the input is noisy Markdown/social text. It preserves bracketed controls such as `[S1]`, `[pause 3.2s]`, and `{whisper}` rather than deleting them.

## Voice cloning

Use direct generation plus a one-item `reference` list when you want the target text spoken in the reference speaker's timbre.

```python
reference_audio = "speaker_reference.wav"  # local path or URL accepted by the processor
conversation = [[
    processor.build_user_message(
        text="We stand on the threshold of the AI era.",
        reference=[reference_audio],
        language="English",
    )
]]
batch = processor(conversation, mode="generation")
```

Operational rules:

- For current single-speaker MOSS-TTS, use one reference item in the list.
- Reference audio should be clear, speech-dominant, and representative of the desired identity. Short clips around several seconds are safer than long noisy clips.
- The processor converts path/URL references into audio codes and resamples to the model sampling rate.

## Continuation and continuation + clone

Continuation provides prefix audio in the assistant message. The **prefix transcript must be prepended to the user text**, because the model continues from that transcript and audio.

```python
ref_text = "But I really can't complain about not having a normal college experience to you."
new_text = " We stand on the threshold of the AI era."
reference_audio = "speaker_reference.m4a"

# Continuation only: continue the prefix audio style.
conversation = [[
    processor.build_user_message(text=ref_text + new_text, language="English"),
    processor.build_assistant_message(audio_codes_list=[reference_audio]),
]]
batch = processor(conversation, mode="continuation")

# Continuation + clone: also place the same reference in the user message.
conversation_with_clone = [[
    processor.build_user_message(text=ref_text + new_text, reference=[reference_audio], language="English"),
    processor.build_assistant_message(audio_codes_list=[reference_audio]),
]]
batch = processor(conversation_with_clone, mode="continuation")
```

Conversation shape is strict: generation mode expects an odd-length conversation ending with `user`; continuation expects an even-length conversation ending with `assistant`.

## MOSS-TTSD multi-speaker dialogue

TTSD generates long dialogue with explicit speaker tags. It can run without reference audio in `generation` mode, but the strongest voice-control workflow is continuation with one reference and prompt transcript per cloned speaker.

```python
import torch
import torchaudio
from transformers import AutoModel, AutoProcessor

model_id = "OpenMOSS-Team/MOSS-TTSD-v1.0"
codec_id = "OpenMOSS-Team/MOSS-Audio-Tokenizer"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True, codec_path=codec_id)
processor.audio_tokenizer = processor.audio_tokenizer.to(device).eval()
model = AutoModel.from_pretrained(
    model_id,
    trust_remote_code=True,
    attn_implementation=resolve_attn_implementation(),
    torch_dtype=dtype,
).to(device).eval()

target_sr = int(processor.model_config.sampling_rate)

def load_mono(path: str):
    wav, sr = torchaudio.load(path)
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if int(sr) != target_sr:
        wav = torchaudio.functional.resample(wav, int(sr), target_sr)
    return wav

wav_s1 = load_mono("speaker1.wav")
wav_s2 = load_mono("speaker2.wav")
ref_codes = processor.encode_audios_from_wav([wav_s1, wav_s2], sampling_rate=target_sr)
prompt_audio = processor.encode_audios_from_wav([torch.cat([wav_s1, wav_s2], dim=-1)], sampling_rate=target_sr)[0]

prompt_s1 = "[S1] In short, we embarked on a mission to make America great again for all Americans."
prompt_s2 = "[S2] NVIDIA reinvented computing for the first time after 60 years."
dialogue = (
    "[S1] Listen, let's talk business. China. What's the real scoop? "
    "[S2] The pace of innovation there is extraordinary, honestly. "
    "[S1] Are they winning? [S2] I would say they are very determined."
)
full_text = f"{prompt_s1} {prompt_s2} {dialogue}"

conversation = [[
    processor.build_user_message(text=full_text, reference=ref_codes),
    processor.build_assistant_message(audio_codes_list=[prompt_audio]),
]]
batch = processor(conversation, mode="continuation")
with torch.no_grad():
    outputs = model.generate(
        input_ids=batch["input_ids"].to(device),
        attention_mask=batch["attention_mask"].to(device),
        max_new_tokens=2000,
        audio_temperature=1.1,
        audio_top_p=0.9,
        audio_top_k=50,
        audio_repetition_penalty=1.1,
    )
```

TTSD rules:

- Supported speaker tags are `[S1]`, `[S2]`, ... up to the intended speaker count; the Gradio-style UI supports 1 to 5 speakers.
- If a speaker has reference audio, it must also have a prompt transcript with the same `[Sx]` tag.
- `reference` should be a list aligned to speakers. Use `None` for non-cloned speakers only when constructing partial reference lists manually.
- Concatenate prompt audio in the same speaker order used by the prompt transcript.
- TTSD-v1.0 uses a 16-codebook checkpoint. Do not reuse 32-codebook TTS audio codes or Local checkpoint code with TTSD.

## MOSS-VoiceGenerator

VoiceGenerator does not use reference audio. It requires a voice/style instruction plus the content text.

```python
model_id = "OpenMOSS-Team/MOSS-VoiceGenerator"
processor = AutoProcessor.from_pretrained(
    model_id,
    trust_remote_code=True,
    normalize_inputs=True,  # normalize both text and instruction input
)
processor.audio_tokenizer = processor.audio_tokenizer.to(device)
conversation = [[
    processor.build_user_message(
        text="Hey there, stranger! What brings you to our humble town?",
        instruction=(
            "Hearty, jovial tavern owner's voice, loud and welcoming with a slightly "
            "gruff friendly tone in American English."
        ),
    )
]]
batch = processor(conversation, mode="generation")
```

Instruction-writing tips:

- Include age/gender only when needed; avoid contradictory descriptors.
- Specify emotion, energy, accent/language variety, speaking rate, pitch, and vocal texture.
- Keep text and instruction in the same broad language family when possible; VoiceGenerator is primarily Chinese/English.

## MOSS-SoundEffect v1 through the Delay API

This is the v1 Delay-family SoundEffect model, not SoundEffect v2. Use `ambient_sound` instead of `text`.

```python
model_id = "OpenMOSS-Team/MOSS-SoundEffect"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
conversation = [[processor.build_user_message(ambient_sound="清晰脚步声在水泥地面回响，节奏稳定。", tokens=125)]]
batch = processor(conversation, mode="generation")
```

`tokens` still follows the approximate `1 second ≈ 12.5 tokens` rule.

## Gradio-style launch flags

The family UI launchers preload the processor/model at startup, then call the same API patterns above. If operating a checkout or wrapper that provides these Gradio apps, these are the distilled flag contracts; do not inspect app source just to recover defaults.

| UI | Default model | Default port | Important flags | Queue behavior |
|---|---|---:|---|---|
| MOSS-TTS v1.5 | `OpenMOSS-Team/MOSS-TTS-v1.5` | `7860` | `--model_path`, `--device`, `--attn_implementation`, `--host`, `--port`, `--share` | max queue 16, concurrency 1 |
| MOSS-TTSD | `OpenMOSS-Team/MOSS-TTSD-v1.0` | `7863` | `--model_path`, `--codec_path`, `--device`, `--attn_implementation`, `--host`, `--port`, `--share` | concurrency 2 |
| MOSS-VoiceGenerator | `OpenMOSS-Team/MOSS-VoiceGenerator` | `7862` | `--model_path`, `--device`, `--attn_implementation`, `--host`, `--port`, `--share` | max queue 16, concurrency 1 |

Command templates:

```bash
# MOSS-TTS v1.5 UI wrapper
python <moss-tts-gradio-launcher> \
  --model_path OpenMOSS-Team/MOSS-TTS-v1.5 \
  --device cuda:0 --attn_implementation auto \
  --host 127.0.0.1 --port 7860

# MOSS-TTSD UI wrapper
python <moss-ttsd-gradio-launcher> \
  --model_path OpenMOSS-Team/MOSS-TTSD-v1.0 \
  --codec_path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device cuda:0 --attn_implementation auto \
  --host 127.0.0.1 --port 7863

# MOSS-VoiceGenerator UI wrapper
python <moss-voice-generator-gradio-launcher> \
  --model_path OpenMOSS-Team/MOSS-VoiceGenerator \
  --device cuda:0 --attn_implementation auto \
  --host 127.0.0.1 --port 7862
```

`--attn_implementation auto` resolves to FlashAttention 2 when the package, CUDA device, and dtype support it; otherwise to SDPA on CUDA or eager on CPU. Use `--attn_implementation none` only in wrappers that intentionally avoid passing the keyword to `from_pretrained`.

## Output handling

`processor.decode(outputs)` returns assistant messages. The first audio waveform is normally `message.audio_codes_list[0]`. For saving:

```python
messages = processor.decode(outputs)
if not messages or messages[0] is None:
    raise RuntimeError("The model did not return a decodable audio result.")
audio = messages[0].audio_codes_list[0]
if isinstance(audio, torch.Tensor):
    audio = audio.detach().cpu().to(torch.float32)
if audio.ndim == 1:
    audio = audio.unsqueeze(0)
torchaudio.save("sample.wav", audio, int(processor.model_config.sampling_rate))
```

If the output is stereo from a v1.5 Local path, do not flatten it before saving unless the user explicitly requests mono.
