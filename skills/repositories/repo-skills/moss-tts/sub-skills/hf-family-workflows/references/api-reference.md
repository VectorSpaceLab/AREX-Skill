# API reference for Hugging Face family workflows

This reference distills the public remote-code processor/model contract used by MOSS-TTS Delay, Local, TTSD, VoiceGenerator, and SoundEffect v1 workflows.

## Load pattern

```python
from transformers import AutoModel, AutoProcessor

processor = AutoProcessor.from_pretrained(
    "OpenMOSS-Team/MOSS-TTS-v1.5",
    trust_remote_code=True,
)
model = AutoModel.from_pretrained(
    "OpenMOSS-Team/MOSS-TTS-v1.5",
    trust_remote_code=True,
    attn_implementation="sdpa",  # or flash_attention_2/eager/omitted
    torch_dtype=dtype,
)
```

Always use `trust_remote_code=True`; the family relies on model-specific configuration, processor, and generation code.

`processor.audio_tokenizer` is a model object. Move it to the same device used for audio encoding/decoding:

```python
processor.audio_tokenizer = processor.audio_tokenizer.to(device)
processor.audio_tokenizer.eval()
```

For TTSD or any workflow where the codec path must be controlled explicitly:

```python
processor = AutoProcessor.from_pretrained(
    "OpenMOSS-Team/MOSS-TTSD-v1.0",
    trust_remote_code=True,
    codec_path="OpenMOSS-Team/MOSS-Audio-Tokenizer",
)
```

If `codec_path` is omitted, the processor first checks the model's processor config for an audio tokenizer path and otherwise falls back to the standard MOSS audio tokenizer.

## Message schema

### `processor.build_user_message(...)`

```python
processor.build_user_message(
    text: str | None = None,
    reference: list[str | torch.Tensor | None] | str | torch.Tensor | None = None,
    instruction: str | None = None,
    tokens: int | None = None,
    quality: str | None = None,
    sound_event: str | None = None,
    ambient_sound: str | None = None,
    language: str | None = None,
) -> dict
```

| Field | Used by | Meaning | Notes |
|---|---|---|---|
| `text` | TTS, TTSD, VoiceGenerator | Text content to synthesize | Delay-family processor normalizes this text; Local 1.0 processor leaves it unchanged. |
| `reference` | TTS cloning, TTSD cloning | Audio references as file paths/URLs or pre-encoded audio-code tensors | Non-list references are converted to one-item lists. TTSD needs speaker-aligned lists. |
| `instruction` | VoiceGenerator | Voice/style description | Required for VoiceGenerator; combine emotion, timbre, age, accent, speaking rate, and style. |
| `tokens` | TTS and SoundEffect duration control | Expected audio-token count | Approximate duration rule: `1s ≈ 12.5 tokens`. |
| `quality` | Reserved template field | Quality hint | Present in the prompt template but not a primary documented user control. |
| `sound_event` | Reserved / sound workflows | Sound event text | Prefer `ambient_sound` for SoundEffect v1 examples. |
| `ambient_sound` | SoundEffect v1 | Sound-effect/environment description | Use instead of `text` for Delay-family SoundEffect. |
| `language` | MOSS-TTS v1.5 and Local v1.5 | Language label | Use labels such as `French`, `English`, `Chinese`; recommended when known. |

The user prompt template contains all fields, even when values are `None`:

```text
<user_inst>
- Reference(s):
{reference}
- Instruction:
{instruction}
- Tokens:
{tokens}
- Quality:
{quality}
- Sound Event:
{sound_event}
- Ambient Sound:
{ambient_sound}
- Language:
{language}
- Text:
{text}
</user_inst>
```

References are represented in the text stream using `<|audio|>` placeholders. For a reference list with non-`None` entries, the processor labels them `[S1]`, `[S2]`, ... in order.

### `processor.build_assistant_message(...)`

```python
processor.build_assistant_message(
    audio_codes_list: list[str | torch.Tensor],
    content: str = "<|audio|>",
) -> dict
```

Use assistant messages only when providing prefix audio for continuation. `audio_codes_list` can contain paths/URLs or already encoded code tensors.

## Conversation shape and processor modes

```python
batch = processor(conversations, mode="generation")
```

| Mode | Conversation shape | Last role | Use |
|---|---|---|---|
| `generation` | odd number of messages | `user` | Direct TTS, voice cloning via user `reference`, VoiceGenerator, SoundEffect v1, TTSD with no prompt audio. |
| `continuation` | even number of messages | `assistant` | Continue from prefix audio or TTSD multi-speaker prompt audio. |
| `computing_loss` | training/eval internals | task-specific | Do not use for ordinary inference; route training/data prep to the fine-tuning sub-skill. |

The processor accepts one conversation or a list of conversations. It returns a `BatchFeature` with:

```python
{
    "input_ids": LongTensor[batch, sequence, 1 + n_vq],
    "attention_mask": BoolTensor[batch, sequence],
}
```

Other kwargs:

| Kwarg | Default | Meaning |
|---|---:|---|
| `apply_chat_template` | `True` | Wraps each role/content pair through the tokenizer chat template. Keep enabled unless debugging raw prompt text. |
| `n_vq` | `None` | Checks/prepares audio codebook count for provided audio-code tensors. Set only when you must enforce a known codebook count. |
| `return_tensors`, `padding`, `truncation` | ignored | Processor always returns torch tensors and handles its own padding/truncation. |

## Audio encoding contract

### Encode from waveforms

```python
codes_list = processor.encode_audios_from_wav(
    wav_list=[wav1, wav2],
    sampling_rate=target_sr,
    n_vq=None,
)
```

- Accepts one waveform tensor or a list of tensors.
- Delay/Local 1.0 processors convert multi-channel waveforms to mono before encoding.
- If the input sample rate differs from `processor.model_config.sampling_rate`, audio is resampled.
- Waveforms are loudness-normalized with a small gain range before encoding.
- Output is a list of tensors shaped `[T, NQ]` on CPU, where `NQ` is the number of quantizers/codebooks.

### Encode from paths

```python
codes_list = processor.encode_audios_from_path(["speaker1.wav", "speaker2.wav"], n_vq=None)
```

- Uses torchaudio to load local paths and URLs supported by the backend.
- Resamples each item independently to the model sampling rate.
- Raises on an empty path list.

### Decode generated codes

```python
messages = processor.decode(outputs)
message = messages[0]
audio_waveform = message.audio_codes_list[0]
```

For Delay models, generated audio codes are de-delayed before audio-tokenizer decode. For continuation, the first decoded segment is trimmed so that the returned waveform contains generated continuation audio rather than the full prefix.

## Architecture differences that affect API use

| Architecture | Codebook behavior | Typical sampling rate | API impact |
|---|---|---:|---|
| `MossTTSDelay` | Delay-pattern scheduling over multiple RVQ codebooks | 24 kHz for TTS 1.0/v1.5, TTSD, VoiceGenerator, SoundEffect v1 | Assistant/user audio placeholders expand into gen and delay slot tokens; TTSD-v1.0 uses 16 codebooks. |
| `MossTTSLocal` 1.0 | Time-synchronous local-transformer token blocks, no delay shift | 24 kHz mono | Same high-level message fields; generation appends an audio-start position token internally. |
| `MossTTSLocal` v1.5 | Local Transformer with MOSS-Audio-Tokenizer-v2 | 48 kHz stereo, 12 codebooks | Use same non-streaming prompt concepts; route streaming decode/app details to `../local-v15-streaming/SKILL.md`. |

Do not pass audio codes from one `n_vq` family into another. Typical mismatches:

- MOSS-TTS Delay 1.0/v1.5: 32 codebooks.
- MOSS-TTSD-v1.0: 16 codebooks.
- MOSS-TTS-Local-Transformer-v1.5: 12 codebooks.

## Generation hyperparameters

All family models use the same `model.generate(...)` shape but have different recommended audio sampling values.

```python
outputs = model.generate(
    input_ids=input_ids,
    attention_mask=attention_mask,
    max_new_tokens=4096,
    audio_temperature=1.7,
    audio_top_p=0.8,
    audio_top_k=25,
    audio_repetition_penalty=1.0,
)
```

| Parameter | Meaning | Practical guidance |
|---|---|---|
| `max_new_tokens` | Hard cap on generated audio-token steps | Increase for long output; too low truncates audio. |
| `audio_temperature` | Sampling variation | Lower if output is unstable; use model-card defaults first. |
| `audio_top_p` | Nucleus sampling cutoff | Lower is more conservative; too low may sound flat. |
| `audio_top_k` | Top-k sampling cutoff | Lower narrows choices; too high can increase artifacts. |
| `audio_repetition_penalty` | Penalizes repeated patterns | Use >1.0 for TTSD/VoiceGenerator/SoundEffect defaults. |
| `tokens` in user message | Soft expected duration | Use for direct generation duration control, not continuation UI modes. |

## Prompt construction examples by task

### Multilingual v1.5 with pronunciation and pause control

```python
text = "Bonjour, je voudrais essayer une voix française naturelle et stable. [pause 1.0s] Merci."
conversation = [[processor.build_user_message(text=text, language="French")]]
```

### Pinyin / IPA pronunciation control

```python
pinyin = "nin2 hao3，qing3 wen4 nin2 lai2 zi4 na3 zuo4 cheng2 shi4？"
ipa = "/həloʊ, meɪ aɪ æsk wɪtʃ sɪti juː ɑːr frʌm?/"
conversation = [[processor.build_user_message(text=pinyin)]]
conversation_ipa = [[processor.build_user_message(text=ipa, language="English")]]
```

### Direct clone with expected duration

```python
conversation = [[
    processor.build_user_message(
        text="This announcement should take about twenty seconds.",
        reference=["clean_reference.wav"],
        language="English",
        tokens=250,
    )
]]
```

### TTSD without references

```python
dialogue = "[S1] Welcome back. [S2] Thanks, I'm excited to discuss the update."
conversation = [[processor.build_user_message(text=dialogue)]]
batch = processor(conversation, mode="generation")
```

### VoiceGenerator

```python
conversation = [[
    processor.build_user_message(
        text="The quick brown fox jumps over the lazy dog.",
        instruction="Clear neutral voice for phonetic practice, even tempo, standard American English.",
    )
]]
```

### SoundEffect v1

```python
conversation = [[processor.build_user_message(ambient_sound="Thunder rumbling with light rain in the distance.", tokens=125)]]
```

## Text normalization helper

The bundled helper is stdlib-only and safe to use in prompt-preparation pipelines:

```bash
# From this sub-skill directory, or replace <this sub-skill> with its installed path.
python scripts/normalize_tts_text.py \
  --text "# 标题\n请求接入 -> 域服务处理......" \
  --output-file normalized.txt
```

It intentionally does **not** expand numbers, dates, units, currencies, or phonemes. It only performs robustness cleanup and preserves control brackets.
