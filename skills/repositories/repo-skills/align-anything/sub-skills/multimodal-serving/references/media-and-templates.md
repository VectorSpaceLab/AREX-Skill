# Media Inputs and Chat Templates

Use this reference to construct serving inputs that match align-anything's text, multimodal, and omni-modal inference paths.

## Conversation shapes

### Text-only chat

The text CLI uses plain string content:

```python
messages = [
    {"role": "user", "content": "Explain the image-to-text task."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "Continue."},
]
```

The CLI calls:

```python
model.chat(messages=messages, tokenizer=tokenizer)
```

Use this only when the model implements `chat(messages=..., tokenizer=...)` or when you are reproducing the packaged text CLI behavior.

### Multimodal image/audio/video chat

The multimodal CLI uses content lists with typed placeholders. Media files are stored separately, then passed to the processor.

Image question:

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "What is great about this image?"},
        ],
    }
]
media_files = ["example.jpg"]
```

Audio question:

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio_url": "placeholder"},
            {"type": "text", "text": "What is the emotion of this audio?"},
        ],
    }
]
media_files = ["example.wav"]
```

Video question:

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video"},
            {"type": "text", "text": "What is the video about?"},
        ],
    }
]
media_files = ["example.mp4"]
```

Text-only turns in the multimodal CLI use typed text content:

```python
[{"role": "user", "content": [{"type": "text", "text": "Hello"}]}]
```

### Omni-modal chat

The omni CLI is specialized for MiniCPM-O-style models. It builds a list beginning with the model's system prompt:

```python
system_message = model.get_sys_prompt(mode="omni", language="en")
conversation = [
    system_message,
    {"role": "user", "content": ["Describe these inputs", image_obj, audio_array]},
]
```

Video inputs become repeated chunks:

```python
["<unit>", frame_image_0, audio_chunk_0, "<unit>", frame_image_1, audio_chunk_1, ...]
```

The omni CLI calls:

```python
result = model.chat(
    msgs=conversation,
    tokenizer=tokenizer,
    sampling=True,
    temperature=0.5,
    max_new_tokens=4096,
    omni_input=True,
    use_tts_template=True,
    max_slice_nums=1,
    use_image_id=False,
    return_dict=True,
)
text = result.text
```

## Template formatting

The multimodal CLI wraps conversation formatting with `ChatTemplate(formatter=processor, custom_formatter=custom_formatter)`.

Template resolution order:

1. If the model has `apply_chat_template`, use it as the custom formatter.
2. Else if the tokenizer/processor has `apply_chat_template` and a non-empty `chat_template`, call it with `tokenize=False`, `add_special_tokens=True`, and the requested generation prompt flag.
3. Else if the formatter has `apply_sft_template_for_multi_turn_prompts` (Janus-style), call that method with `sft_format="deepseek"` and empty system prompt.
4. Else use a default plain template:
   - string content becomes `ROLE: content\n`;
   - typed list content contributes only text items as `ROLE: text\n`;
   - `add_generation_prompt=True` appends `ASSISTANT: `.

Consequences for serving:

- If a model class exposes a `chat_template`, the loader copies it onto the processor or tokenizer so downstream formatters can use it.
- Models with custom `apply_chat_template` may insert media tokens themselves. Do not add extra `<image>` or `<audio>` tokens unless the specific model documentation or class behavior requires it.
- The number and order of typed media placeholders should match the number and order of media files handed to the processor.
- For pure text tasks, the text CLI bypasses `ChatTemplate` and calls `model.chat` directly.

## Media preprocessing paths

### Images

Multimodal CLI behavior:

```python
from PIL import Image
images = [Image.open(path) for path in media_files]
inputs = processor(images=images, text=formatted_prompt, return_tensors="pt", padding=True)
```

Operational notes:

- Convert unusual modes to RGB if the target processor expects RGB.
- Keep file count aligned with image placeholders.
- Extremely wide/tall images can fail model-specific resize rules. Qwen2-VL-style utilities reject absolute aspect ratios above 200 and resize dimensions to multiples of 28.

### Audio

Multimodal CLI behavior:

```python
import librosa
audios = [librosa.load(path, sr=processor.feature_extractor.sampling_rate)[0] for path in media_files]
inputs = processor(
    audios=audios,
    text=formatted_prompt,
    return_tensors="pt",
    padding=True,
    sampling_rate=processor.feature_extractor.sampling_rate,
)
```

Omni CLI behavior:

```python
audio, _ = librosa.load(path, sr=16000, mono=True)
```

Operational notes:

- Audio formats depend on `librosa`, `soundfile`, and system codec support.
- The multimodal processor controls target sampling rate through `processor.feature_extractor.sampling_rate`.
- Omni video chunking also extracts audio at 16 kHz; videos without audio may fail this path.

### Video

Multimodal CLI behavior:

```python
import av
import numpy as np

container = av.open(path)
total_frames = container.streams.video[0].frames
indices = np.arange(0, total_frames, total_frames / 8).astype(int)
clip = read_video_pyav(container, indices)  # RGB ndarray with 8 sampled frames
inputs = processor(videos=[clip], text=formatted_prompt, return_tensors="pt", padding=True)
```

Operational notes:

- The PyAV path assumes the stream reports a positive frame count.
- Re-encode videos that have missing frame metadata, unsupported codecs, or variable-frame-rate decode issues.
- The separate Qwen2-VL-style video utility can use `decord` when installed, otherwise `torchvision`; set `FORCE_QWENVL_VIDEO_READER=decord` or `torchvision` to force one backend.
- Qwen2-VL video frame counts are rounded to a factor of 2 and default to 2 FPS, with minimum 4 and maximum 60 frames unless overridden.

### Omni video chunks

Omni video preprocessing uses MoviePy to pair one frame and one second of audio per unit:

```python
from moviepy import VideoFileClip
video = VideoFileClip(video_path)
num_units = math.ceil(video.duration)
# for each second: append "<unit>", PIL frame, audio_np[sr*i:sr*(i+1)]
```

Operational notes:

- Requires MoviePy and a working FFmpeg backend.
- Assumes the video has an audio track.
- Long videos create many unit chunks and can quickly exhaust memory or context.

## File extension dispatch for omni inputs

The omni CLI classifies files by lowercase suffix:

| Modality | Extensions |
|---|---|
| Audio | `.wav`, `.mp3`, `.flac`, `.m4a`, `.ogg`, `.aac` |
| Image | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.ico`, `.webp` |
| Video | `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm` |

Unsupported suffixes are ignored by the classifier and should be converted or renamed before serving.

## Moving tensors to the model

The multimodal CLI moves each tensor returned by the processor to `model.device`:

```python
for key, value in inputs.items():
    if isinstance(value, torch.Tensor):
        inputs[key] = value.to(model.device)
```

When the model uses `device_map="auto"`, `model.device` may represent only one of several devices. If generation fails with cross-device tensor errors, try a smaller model, single-device loading, or a Transformers-compatible device map/offload setup for that model family.

## Minimal offline formatting probe

Use this pattern to check template formatting without loading full weights:

```python
from transformers import AutoProcessor, AutoTokenizer
from align_anything.configs.template import ChatTemplate

model_name_or_path = "your-model"
processor = AutoProcessor.from_pretrained(model_name_or_path, trust_remote_code=True)
formatter = ChatTemplate(formatter=processor)
formatted, _ = formatter.format_chat_sample([
    {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "Describe this."}]}
])
print(formatted)
```

If `AutoProcessor` is unavailable for a text-only model, use `AutoTokenizer` instead and provide string or typed-text messages.
