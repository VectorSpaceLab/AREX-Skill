# OmniLive Workflow Reference

This reference distills OmniLive operating facts into self-contained planning recipes. Treat every command as a user-edited plan: the bundled skill does not download checkpoints, import torch, launch services, or require the original repository checkout.

## Model root layout

A downloaded OmniLive model root is conventionally named `internlm-xcomposer2d5-ol-7b/` and is expected to contain:

| Component | Purpose | Required for |
| --- | --- | --- |
| `audio/` | Qwen2-Audio-compatible checkpoint used through ModelScope Swift for ASR and audio classification. | audio quickstarts, service ASR, audio benchmarks |
| `base/` | InternLM-XComposer2.5 VLM checkpoint/code used for image/video understanding and as the LoRA merge base. | base VLM checks, video benchmarks, LoRA merge input |
| `adapter/` | PEFT LoRA adapter that must be merged with `base/` before memory-backed LLM inference. | creating `merge_lora/` |
| `memory/` | Grounding/video-memory model and tokenizer/code for selecting global and question-related video memories. | memory video QA, online video memory service |
| `merge_lora/` | Output directory produced by merging `base/` + `adapter/`; used as the MLLM for memory video QA and online services. | memory video QA, service MLLM |

Run a safe structural check before planning:

```bash
python scripts/check_omnilive_layout.py /path/to/internlm-xcomposer2d5-ol-7b --workflow all
```

Use `--workflow memory` when the task is only memory-backed video QA; use `--workflow benchmark-video` for video benchmark planning that loads only `base/`.

For approved local execution, use the self-contained bundle `entrypoints/omnilive-examples/`. It contains runnable scripts and wrappers for audio ASR/classification, base VLM image QA, LoRA merge into `merge_lora/`, and memory-backed video QA. It still requires the user-provided model root and CUDA/model dependencies.

## Audio ASR and audio classification

OmniLive audio uses ModelScope Swift with `ModelType.qwen2_audio_7b_instruct`. The bundled runnable entrypoint is:

```bash
cd entrypoints/omnilive-examples
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_audio_asr.sh --audio /data/sample.wav --task asr
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_audio_asr.sh --audio /data/sample.wav --task classify
```

The core source-equivalent recipe is:

```python
import torch
from swift.llm import (
    get_model_tokenizer, get_template, ModelType,
    get_default_template_type, inference,
)
from swift.utils import seed_everything

model_type = ModelType.qwen2_audio_7b_instruct
model_root = "/models/internlm-xcomposer2d5-ol-7b"
model_id_or_path = f"{model_root}/audio"  # local layout; hosted layouts may use model_dir="audio"
template_type = get_default_template_type(model_type)

model, tokenizer = get_model_tokenizer(
    model_type,
    torch.float16,
    model_id_or_path=model_id_or_path,
    model_kwargs={"device_map": "cuda:0"},
)
model.generation_config.max_new_tokens = 256
template = get_template(template_type, tokenizer)
seed_everything(42)

query = "<audio>Detect the language and recognize the speech."
response, _ = inference(model, template, query, audios="sample.wav")

cls_query = "<audio>Classify the audio."
cls_response, _ = inference(model, template, cls_query, audios="sample.wav")
```

Planning notes:

- Use `audio/` directly for a local downloaded layout. For a hosted model id, the quickstart can pass the root model id plus `model_dir="audio"` if the loader supports subfolder selection.
- The audio query text matters: ASR uses `Detect the language and recognize the speech.`; classification uses `Classify the audio.`
- Keep `max_new_tokens=256` unless the user needs long transcription. Higher values increase latency in live services.
- Audio examples assume CUDA and Swift. A CPU-only plan is a dependency/import check, not proof of real-time audio behavior.

## OmniLive base VLM checks

The OmniLive `base/` component exposes the InternLM-XComposer2.5 VLM API. Use it only as OmniLive context here; route generic XComposer inference tasks to `model-inference`.

Bundled runnable entrypoint:

```bash
cd entrypoints/omnilive-examples
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_base_vlm.sh --image /data/dubai.png --question "Analyze the image."
```

```python
import torch
from transformers import AutoModel, AutoTokenizer

torch.set_grad_enabled(False)
model_path = "/models/internlm-xcomposer2d5-ol-7b/base"
model = AutoModel.from_pretrained(model_path, trust_remote_code=True).eval()
model.half().cuda()  # or keep fp32 only if the host can afford it
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model.tokenizer = tokenizer

question = "Analyze the given image in a detailed manner"
image = ["/data/dubai.png"]
with torch.autocast(device_type="cuda", dtype=torch.float16):
    response, history = model.chat(
        tokenizer,
        question,
        image,
        do_sample=False,
        num_beams=3,
        use_meta=True,
    )
```

Observed API facts from the OmniLive base code:

- `chat(tokenizer, query, image=None, hd_num=24, history=[], max_new_tokens=1024, do_sample=True, num_beams=1, temperature=1.0, top_p=0.8, repetition_penalty=1.005, infer_mode="base", use_meta=False, ...)` returns `(response, history)`.
- `encode_img` accepts image files and video files, converts videos to a contact sheet, and uses `hd_num` to bound high-definition image tiling.
- Source quickstarts use `torch.float16` autocast and `trust_remote_code=True`; bfloat16 or fp16 choice should be matched to GPU support.
- Multi-GPU dispatch is cross-cutting XComposer inference guidance; plan it through the sibling `model-inference` sub-skill unless the request is explicitly OmniLive service/memory related.

## Merge LoRA before memory video QA

Memory video QA loads the MLLM from `merge_lora/`, not directly from `base/` with `adapter/`. The repaired skill includes a runnable merge entrypoint:

```bash
cd entrypoints/omnilive-examples
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_merge_lora.sh
```

The merge operation is conceptually:

```python
import torch
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

model_root = "/models/internlm-xcomposer2d5-ol-7b"
base_dir = f"{model_root}/base"
adapter_dir = f"{model_root}/adapter"
out_dir = f"{model_root}/merge_lora"

peft_config = PeftConfig.from_pretrained(adapter_dir)
model = AutoModelForCausalLM.from_pretrained(
    base_dir,
    return_dict=True,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(base_dir, trust_remote_code=True)
model = PeftModel.from_pretrained(model, adapter_dir).eval()
model = model.merge_and_unload()
model.save_pretrained(out_dir)
tokenizer.save_pretrained(out_dir)
```

Before planning memory QA or a service backend, confirm:

```bash
python scripts/check_omnilive_layout.py /models/internlm-xcomposer2d5-ol-7b --workflow memory --require-weights
```

If `merge_lora/` is missing, stop at a merge plan. Do not silently fall back to `base/`; it lacks the merged MLLM weights expected by the memory pipeline.

## Memory-backed video QA

The bundled runnable memory QA entrypoint is:

```bash
cd entrypoints/omnilive-examples
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_memory_qa.sh --video-path /data/needle_32.mp4 --question "What does the hand do?" --max-frame 16 --vs-thresh 0.35
```

Memory video QA combines:

1. `merge_lora/` loaded with `AutoModelForCausalLM` as the answer-generating MLLM.
2. `memory/` loaded as `GroundQwenForCausalLM` to compute global (`glb`) and question-related local (`lol`) video memories.
3. Video frame sampling through Decord: 16 frames per clip, at least 5 clips, at most `max_clip` clips.
4. A rendered image/contact sheet from selected frames, passed with projected memory tokens into the MLLM.

Primary arguments:

| Argument | Default | Effect |
| --- | ---: | --- |
| `--ixc-model-path` | `internlm-xcomposer2d5-ol-7b` | Model root containing `merge_lora/` and `memory/`. |
| `--max-frame` | `32` | Caps selected frames after memory grounding; if more frames are selected, they are evenly downsampled. Higher values improve visual coverage but increase image resolution/VRAM/latency. |
| `--vs-thresh` | `0.2` | Similarity threshold for choosing local memory clips. Higher values select fewer clips and can miss evidence; lower values include more clips and can add noise. If no clip passes, the pipeline falls back to all sampled frames and reports grounding failure. |

Memory prompt facts:

- The MLLM receives a global prefix equivalent to `This is video overview memory:`.
- If local memories are selected, they are prefixed by `This is question related video memory:`.
- The answer prompt follows the chat-token pattern `user ... assistant\nThe answer is` for multiple-choice video QA.
- The example path uses `hd_num=36`, `beam=1`, `max_new_token=1024` for the final memory answer.

Planning guidance:

- Treat missing `decord`, `torchvision`, `PIL`, or `accelerate` as environment blockers for memory workflows.
- Treat missing `merge_lora/` as a model-layout blocker, even if `base/` loads.
- For long videos, prefer lowering `--max-frame` before lowering `num_frm`; the memory selection stage still needs temporal coverage.
