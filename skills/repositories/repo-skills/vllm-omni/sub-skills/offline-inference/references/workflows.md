# Offline inference workflows

These workflows are intentionally self-contained. They show local Python usage patterns without relying on repository example files. Full model execution still requires compatible package versions, accelerator memory, and available model weights.

## Generate a safe starter script

Use the bundled generator when you need a quick scaffold:

```bash
python scripts/build_offline_request.py --help
python scripts/build_offline_request.py \
  --task text-to-image \
  --model Tongyi-MAI/Z-Image-Turbo \
  --prompt "a cup of coffee on the table" \
  --height 1024 --width 1024 --num-inference-steps 50 --seed 42 \
  --output-file coffee.png
```

The helper prints Python code. It does not import `vllm_omni`, contact a server, download weights, or load a model.

## Synchronous text-to-image

```python
from pathlib import Path

from vllm_omni.entrypoints.omni import Omni
from vllm_omni.inputs.data import OmniDiffusionSamplingParams


def save_first_image(outputs, path: str) -> None:
    for output in outputs:
        images = getattr(output, "images", None)
        if images:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            images[0].save(path)
            return
    raise RuntimeError("generation finished but no image payload was found")


omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
try:
    prompt = {"prompt": "a cup of coffee on the table", "modalities": ["image"]}
    params = OmniDiffusionSamplingParams(
        height=1024,
        width=1024,
        num_inference_steps=50,
        guidance_scale=4.0,
        seed=42,
    )
    outputs = omni.generate(prompt, params, use_tqdm=False)
    save_first_image(outputs, "coffee.png")
finally:
    omni.close()
```

Notes:

- A bare string prompt can work for simple cases, but a dictionary with `modalities: ['image']` makes output routing explicit.
- `height` and `width` are optional. Leave them unset when the model has strict/default sizes.
- Lower resolution, frame count, and concurrent prompts before changing deployment-level offload/parallel settings.

## Batched diffusion prompts

```python
from vllm_omni.entrypoints.omni import Omni
from vllm_omni.inputs.data import OmniDiffusionSamplingParams

prompts = [
    {"prompt": "a cup of coffee on a table", "modalities": ["image"]},
    {"prompt": "a toy dinosaur on a sandy beach", "modalities": ["image"]},
    {"prompt": "a fox waking up in bed and yawning", "modalities": ["image"]},
]
params = OmniDiffusionSamplingParams(height=768, width=768, seed=123)

omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
try:
    outputs = omni.generate(prompts, params, use_tqdm=True)
    for prompt_index, output in enumerate(outputs):
        for image_index, image in enumerate(getattr(output, "images", []) or []):
            image.save(f"p{prompt_index}-img{image_index}.png")
finally:
    omni.close()
```

For synchronous diffusion batching, pass a list of prompt dictionaries to `Omni.generate`. Each prompt is an independent logical request; the runtime scheduler can batch compatible in-flight requests internally.

## Python generator flow

Use generator mode when you want to process finished request outputs incrementally while still using the synchronous entrypoint:

```python
from vllm_omni.entrypoints.omni import Omni
from vllm_omni.inputs.data import OmniDiffusionSamplingParams

omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
params = OmniDiffusionSamplingParams(seed=42)
try:
    for output in omni.generate(
        [{"prompt": "red fox", "modalities": ["image"]}, {"prompt": "blue bird", "modalities": ["image"]}],
        params,
        py_generator=True,
        use_tqdm=False,
    ):
        print(output.request_id, output.final_output_type, output.finished)
        if output.images:
            output.images[0].save(f"{output.request_id}.png")
finally:
    # Safe even if the generator already closed the engine after full consumption.
    omni.close()
```

Do not leave a generator half-consumed without closing it or the owning `Omni` instance; workers and GPU memory may stay alive.

## Image-to-image or image edit

```python
from pathlib import Path
from PIL import Image

from vllm_omni.entrypoints.omni import Omni
from vllm_omni.inputs.data import OmniDiffusionSamplingParams

input_image = Image.open("input.png").convert("RGB")
prompt = {
    "prompt": "change the background to a classroom",
    "modalities": ["image"],
    "multi_modal_data": {"image": input_image},
    "negative_prompt": "blurry",
}
params = OmniDiffusionSamplingParams(
    height=1024,
    width=1024,
    num_inference_steps=50,
    guidance_scale=1.0,
    true_cfg_scale=4.0,
    seed=0,
)

omni = Omni(model="Qwen/Qwen-Image-Edit")
try:
    outputs = omni.generate(prompt, params, use_tqdm=False)
    images = []
    for output in outputs:
        images.extend(getattr(output, "images", []) or [])
    if not images:
        raise RuntimeError("no edited image was returned")
    Path("edited.png").parent.mkdir(parents=True, exist_ok=True)
    images[0].save("edited.png")
finally:
    omni.close()
```

For multiple input images, set `multi_modal_data: {'image': [image1, image2, ...]}` only when the target model supports multi-image edit. Some models need model-specific `extra_args`; keep those in `OmniDiffusionSamplingParams.extra_args` rather than inventing new top-level fields.

## Image/video/audio chat with Qwen3-Omni-style prompts

Qwen-style multimodal chat uses explicit placeholder tokens in the text prompt and matching media entries in `multi_modal_data`.

```python
from PIL import Image
from vllm import SamplingParams

from vllm_omni.entrypoints.omni import Omni

system = (
    "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
    "capable of perceiving auditory and visual inputs, as well as generating text and speech."
)
question = "What is the content of this image? Answer in one sentence."
chat_prompt = (
    f"<|im_start|>system\n{system}<|im_end|>\n"
    "<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>"
    f"{question}<|im_end|>\n"
    "<|im_start|>assistant\n"
)

prompt = {
    "prompt": chat_prompt,
    "multi_modal_data": {"image": Image.open("image.png").convert("RGB")},
    "modalities": ["text"],
}

sampling = SamplingParams(
    temperature=0.9,
    top_p=0.9,
    top_k=-1,
    max_tokens=512,
    seed=42,
)

omni = Omni(model="Qwen/Qwen3-Omni-30B-A3B-Instruct", output_modalities=["text"])
try:
    outputs = omni.generate(prompt, [sampling], use_tqdm=False)
    for output in outputs:
        if output.outputs:
            print(output.outputs[0].text)
finally:
    omni.close()
```

Media payload conventions:

- Image: `{'image': PIL.Image.Image}` or a supported list if the model allows multiple images.
- Audio: `{'audio': (audio_numpy_float32, sample_rate)}`.
- Video: `{'video': frames}` where frames are model/vLLM-compatible arrays.
- Audio in video: add `mm_processor_kwargs: {'use_audio_in_video': True}` only when the model supports that path.

If the same pipeline can output both text and audio, set either prompt-level `modalities` or constructor/request `output_modalities` to prevent ambiguity.

## TTS-style audio generation

Some TTS models use `additional_information` and placeholder `prompt_token_ids` rather than a natural-language `prompt` string. The exact placeholder length can be model-specific; if you cannot calculate it, start from the model's documented requirement or a conservative value and expect model-side validation.

```python
import os
import torch
import soundfile as sf

from vllm_omni.entrypoints.omni import Omni

prompt = {
    "prompt_token_ids": [0] * 2048,
    "additional_information": {
        "task_type": ["CustomVoice"],
        "text": ["She said she would be here by noon."],
        "language": ["English"],
        "speaker": ["Ryan"],
        "instruct": ["Speak warmly and clearly."],
        "max_new_tokens": [2048],
    },
}


def save_wav(mm, path: str) -> None:
    audio = mm["audio"]
    sr_raw = None
    for key in ("sr", "sample_rate", "audio_sample_rate"):
        if key in mm and mm[key] is not None:
            sr_raw = mm[key]
            break
    if sr_raw is None:
        sr_raw = 24000
    if isinstance(sr_raw, list) and sr_raw:
        sr_raw = sr_raw[-1]
    sr = sr_raw.item() if hasattr(sr_raw, "item") else int(sr_raw)
    if isinstance(audio, list):
        audio = torch.cat(audio, dim=-1)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sf.write(path, audio.float().detach().cpu().numpy().flatten(), samplerate=sr, format="WAV")


omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
try:
    for output in omni.generate([prompt], use_tqdm=False):
        mm = output.outputs[0].multimodal_output if output.outputs else output.multimodal_output
        save_wav(mm, f"output_{output.request_id}.wav")
finally:
    omni.close()
```

## AsyncOmni request loop

Use `AsyncOmni` for async generator output and stage-level overlap. Submit diffusion prompts as independent tasks instead of one list prompt when a diffusion stage is present.

```python
import asyncio
import os
import torch
import soundfile as sf

from vllm_omni.entrypoints.async_omni import AsyncOmni


def mm_to_dict(mm):
    if hasattr(mm, "to_dict") and callable(mm.to_dict):
        return mm.to_dict()
    return dict(mm) if hasattr(mm, "items") else {}


async def run_one(async_omni, prompt, request_id: str, output_dir: str):
    text_parts = []
    audio_chunks = []
    sample_rate = 24000
    async for output in async_omni.generate(prompt=prompt, request_id=request_id, output_modalities=["text", "audio"]):
        if output.final_output_type == "text" and output.outputs:
            text_parts.append(output.outputs[0].text)
        elif output.final_output_type == "audio":
            mm = mm_to_dict(output.outputs[0].multimodal_output if output.outputs else output.multimodal_output)
            audio = mm.get("audio")
            if "sr" in mm:
                sr = mm["sr"]
                sample_rate = sr.item() if hasattr(sr, "item") else int(sr)
            if isinstance(audio, list):
                audio_chunks.extend(audio)
            elif audio is not None:
                audio_chunks.append(audio)

    os.makedirs(output_dir, exist_ok=True)
    if text_parts:
        with open(os.path.join(output_dir, f"{request_id}.txt"), "w", encoding="utf-8") as f:
            f.write("".join(text_parts))
    if audio_chunks:
        audio_tensor = torch.cat(audio_chunks, dim=-1) if len(audio_chunks) > 1 else audio_chunks[0]
        sf.write(
            os.path.join(output_dir, f"{request_id}.wav"),
            audio_tensor.float().detach().cpu().numpy().flatten(),
            samplerate=sample_rate,
            format="WAV",
        )


async def main():
    async_omni = AsyncOmni(model="Qwen/Qwen3-Omni-30B-A3B-Instruct", output_modalities=["text", "audio"])
    try:
        prompt = {"prompt": "<|im_start|>user\nSay hello.<|im_end|>\n<|im_start|>assistant\n"}
        await run_one(async_omni, prompt, "req-0", "outputs")
    finally:
        async_omni.shutdown()


asyncio.run(main())
```

Concurrency pattern:

```python
semaphore = asyncio.Semaphore(max_in_flight)

async def guarded(i, prompt):
    async with semaphore:
        return await run_one(async_omni, prompt, f"req-{i}", "outputs")

await asyncio.gather(*(guarded(i, p) for i, p in enumerate(prompts)))
```

Use a semaphore to avoid launching more in-flight requests than the model, memory, and stage configuration can handle.

## Latents, trajectory, and custom outputs

For diffusion pipelines that support trajectory data:

```python
params = OmniDiffusionSamplingParams(
    num_inference_steps=20,
    return_trajectory_latents=True,
    return_trajectory_decoded=True,
)
outputs = omni.generate({"prompt": "a robot sketch", "modalities": ["image"]}, params)
for output in outputs:
    latents = output.latents if output.latents is not None else output.trajectory_latents
    timesteps = output.trajectory_timesteps
    decoded = output.trajectory_decoded
    custom = output.custom_output
```

These fields are optional and model-dependent. Always guard reads with `getattr` or truthiness checks, and keep tensor-to-CPU conversion explicit before serialization.
