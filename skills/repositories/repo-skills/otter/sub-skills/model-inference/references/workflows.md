# Inference workflows

Use these workflows with an installed `otter-ai` package and user-provided checkpoints/media. They avoid dependency on repository demo files while preserving the package's prompt, YAML, and tensor contracts.

## Choose the workflow

| User request | Use |
|---|---|
| "Load Otter/Flamingo and answer one image question" | [Direct Otter/Flamingo generation](#direct-otterflamingo-generation) |
| "Run a list of prompts/images from YAML" | [YAML batch inference](#yaml-batch-inference) |
| "Run OtterHD/Fuyu style inference" | [OtterHD/Fuyu-style inference](#otterhd-fuyu-style-inference) |
| "Convert or downcast a checkpoint" | [conversion](conversion.md) |
| "Expose a worker/API/UI" | [serving](../../serving/SKILL.md) |

## Direct Otter/Flamingo generation

1. Load the checkpoint with `device_map="auto"` and a memory-appropriate dtype, usually `torch.bfloat16` on modern GPUs.
2. Set `model.eval()` and use `model.text_tokenizer`.
3. Build a 6-D `vision_x` tensor: `(batch, num_images_or_chunks, frames, channels, height, width)`.
4. Format the prompt. For Otter image prompts, use `<image>User:{question} GPT:<answer>`.
5. Tokenize to `lang_x` and `attention_mask`.
6. Call `model.generate(...)` and decode tokens after `<answer>` for Otter.

Minimal Otter image pattern:

```python
import torch
from PIL import Image
from transformers import CLIPImageProcessor
from otter_ai import OtterForConditionalGeneration

checkpoint = "USER_ORG/otter-checkpoint"
question = "Describe the image."
image_path = "input.jpg"

model = OtterForConditionalGeneration.from_pretrained(
    checkpoint,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
model.eval()
tokenizer = model.text_tokenizer
tokenizer.padding_side = "left"

image = Image.open(image_path).convert("RGB")
image_processor = CLIPImageProcessor()
vision_x = image_processor.preprocess([image], return_tensors="pt")["pixel_values"]
vision_x = vision_x.unsqueeze(1).unsqueeze(0).to(dtype=next(model.parameters()).dtype)

prompt = f"<image>User:{question} GPT:<answer>"
lang_x = tokenizer([prompt], return_tensors="pt")

generated = model.generate(
    vision_x=vision_x.to(model.device),
    lang_x=lang_x["input_ids"].to(model.device),
    attention_mask=lang_x["attention_mask"].to(model.device),
    max_new_tokens=512,
    temperature=0.2,
    do_sample=True,
    pad_token_id=tokenizer.pad_token_id,
)
answer = tokenizer.decode(generated[0]).split("<answer>")[-1].strip()
answer = answer.replace("<|endofchunk|>", "")
print(answer)
```

For no-image Otter prompts, use `User:{question} GPT:<answer>` and a zero image tensor shaped `(1, 1, 1, 3, 224, 224)`. Do not drop `vision_x`; the model asserts that either `vision_x` is provided or cached vision conditioning is already active.

## YAML batch inference

The distilled batch schema is a top-level YAML list. Each item is a mapping with:

- `question`: required non-empty string.
- `image_path`: optional string. Blank or omitted means no-image mode.
- `answer`, `expected_answer`, or `id`: optional metadata for user-side evaluation; the original generation behavior ignores these fields.

Example:

```yaml
- id: sample-image
  image_path: images/cat.jpg
  question: What is the animal doing?
- id: sample-no-image
  image_path: ""
  question: List three safety checks before loading a large checkpoint.
```

Validate before running generation:

```bash
python scripts/validate_inference_yaml.py prompts.yaml --check-local-images
```

The validator is safe: it reads YAML, checks schema and optional local-image existence, and never downloads media or loads models.

A self-contained batch loop should:

1. Load the model once.
2. Iterate over YAML items in order.
3. For non-empty `image_path`, open a local image or an explicitly allowed URL in the calling project.
4. For blank `image_path`, create a blank `224x224` PIL image for preprocessing or a zero `vision_x` tensor and use the no-image prompt template.
5. Store results under zero-padded string IDs such as `000`, `001`, etc., with `image_path`, `question`, and `answer` fields.

## OtterHD/Fuyu-style inference

OtterHD demo-style inference uses Hugging Face Fuyu components rather than `OtterForConditionalGeneration`:

```python
import torch
from PIL import Image
from transformers import AutoTokenizer, FuyuForCausalLM, FuyuImageProcessor
from otter_ai.models.fuyu.processing_fuyu import FuyuProcessor

checkpoint = "adept/fuyu-8b"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = FuyuForCausalLM.from_pretrained(checkpoint).to(device)
model.eval()
tokenizer = AutoTokenizer.from_pretrained("adept/fuyu-8b")
processor = FuyuProcessor(image_processor=FuyuImageProcessor(), tokenizer=tokenizer)

image = Image.open("input.jpg").convert("RGB")
if max(image.size) > 1080:
    image.thumbnail((1080, 1080))
prompt = "User: Describe the image. Assistant:"
inputs = processor(text=prompt, images=[image], device=device)
inputs = {k: (v.to(device) if isinstance(v, torch.Tensor) else [vv.to(device) for vv in v]) for k, v in inputs.items()}
output = model.generate(**inputs, max_new_tokens=256)
print(processor.batch_decode(output, skip_special_tokens=True)[0])
```

For no-image OtterHD/Fuyu-style prompts, pass `images=None` or omit images according to the processor call and keep the prompt `User: {question} Assistant:`.

## Memory and device placement notes

- Large OpenFlamingo/Otter 9B-class checkpoints can exceed a single consumer GPU. The package supports Hugging Face `device_map="auto"` so Accelerate can shard model modules across multiple GPUs.
- Historical notes for this package reported OpenFlamingo-9B requiring at least about 33 GB of GPU memory for straightforward GPU loading; `device_map="auto"` was introduced to make multi-GPU 24 GB setups feasible.
- Otter Hugging Face checkpoints were intended to run on multiple RTX-3090-class 24 GB GPUs with throughput comparable to a single A100-80G, but actual memory depends on checkpoint, dtype, batch size, generation length, and KV cache.
- Prefer `torch.bfloat16` on Ampere/newer GPUs. Use `torch.float16` when bf16 is unsupported and the checkpoint is known to be stable in fp16.
- CPU-only inference is useful for import or shape debugging, not for realistic 9B-class generation latency.

## Boundary reminders

- Do not start distributed training from this sub-skill; route to [training](../../training/SKILL.md).
- Do not start a web server or worker; route to [serving](../../serving/SKILL.md).
- Do not run benchmark datasets from a YAML inference file; route to [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
