# Inference Workflows

## Purpose

Read this when the user wants to transcribe audio with a pretrained Distil-Whisper checkpoint.

## Recommended checkpoints

- `distil-whisper/distil-large-v3` for most tasks.
- `distil-whisper/distil-small.en` when memory is tight.
- `distil-whisper/distil-medium.en` or `distil-whisper/distil-large-v2` for comparison work.

## Short-form transcription

Use this when audio clips are shorter than 30 seconds.

```python
import torch
from datasets import load_dataset
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

model_id = "distil-whisper/distil-large-v3"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
)
model.to(device)
processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    torch_dtype=torch_dtype,
    device=device,
)

sample = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")[0]["audio"]
print(pipe(sample)["text"])
```

## Sequential long-form transcription

Use this when accuracy matters more than latency.

- Load the same model and processor as above.
- Call the ASR pipeline on a long sample.
- Keep `return_timestamps` available if you want segment-level timing.

## Chunked long-form transcription

Use this when a single long file needs throughput.

- Set `chunk_length_s=25` for `distil-large-v3` unless the user needs a different segment size.
- Increase `batch_size` when the GPU or CPU memory budget allows it.
- Use `max_new_tokens` to cap redundant generations at the chunk border.

## Speculative decoding

Use this when the user wants Whisper-compatible outputs with lower latency.

```python
from transformers import AutoModelForCausalLM, AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch

teacher_id = "openai/whisper-large-v3"
assistant_id = "distil-whisper/distil-large-v2"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

teacher = AutoModelForSpeechSeq2Seq.from_pretrained(teacher_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True)
teacher.to(device)
assistant = AutoModelForCausalLM.from_pretrained(assistant_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True)
assistant.to(device)
processor = AutoProcessor.from_pretrained(teacher_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=teacher,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    generate_kwargs={"assistant_model": assistant},
    torch_dtype=torch_dtype,
    device=device,
)
```

## Speed and memory knobs

- Use `use_flash_attention_2=True` only on supported NVIDIA GPUs with the matching wheel.
- Use `model.to_bettertransformer()` when SDPA / BetterTransformer is the safer GPU path.
- Keep CPU fallbacks in mind when the user only needs correctness, not speed.
