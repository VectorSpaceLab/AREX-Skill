# API and parameter reference

This file captures the local inference CLI surfaces, model-loading choices, image preprocessing behavior, and dependency clues needed to adapt Skywork-R1V3 inference safely.

## Transformers CLI surface

| Parameter | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--model_path` | No | `Skywork/Skywork-R1V3-38B` | Hugging Face model id or local checkpoint directory. |
| `--image_paths` | Yes | none | One or more input images. The native parser uses `nargs='+'`. |
| `--question` | Yes | none | User question appended after generated image tags. |

Native Transformers load behavior:

```text
AutoModel.from_pretrained(
  model_path,
  torch_dtype=torch.bfloat16,
  load_in_8bit=False,
  low_cpu_mem_usage=True,
  use_flash_attn=True,
  trust_remote_code=True,
  device_map=split_model(model_path),
).eval()
AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, use_fast=False)
```

Native generation behavior:

| Generation key | Native value |
| --- | --- |
| `max_new_tokens` | `64000` |
| `do_sample` | `True` |
| `temperature` | `0.6` |
| `top_p` | `0.95` |
| `repetition_penalty` | `1.05` |

Important: these generation values are hard-coded in the native Transformers entrypoint. To change them, adapt the script or use a wrapper; do not pass unsupported CLI flags to the native entrypoint.

## vLLM CLI surface

| Parameter | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--model_path` | Yes in practice | none | Hugging Face model id or local checkpoint directory. |
| `--tensor_parallel_size` | No | `4` | Number of GPUs for vLLM tensor parallelism. |
| `--image_paths` | Yes | none | One or more input image paths. |
| `--question` | Yes | none | User question; image tags are prepended unless the question already starts with one. |
| `--temperature` | No | `0.0` | Sampling temperature. |
| `--max_tokens` | No | `8000` | Maximum generated tokens. |
| `--repetition_penalty` | No | `1.05` | Repetition penalty. |
| `--top_p` | No | `0.95` | Nucleus sampling value. |

Native vLLM initialization behavior:

```text
LLM(
  model=model_path,
  tensor_parallel_size=tensor_parallel_size,
  trust_remote_code=True,
  limit_mm_per_prompt={"image": 20},
  gpu_memory_utilization=0.7,
)
```

Native vLLM prompt behavior:

- Loads the tokenizer and calls `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`.
- Sends `multi_modal_data={"image": image_or_image_list}` to `llm.generate(...)`.
- Uses `SamplingParams(temperature, top_p, max_tokens, repetition_penalty)`.

## Prompt and image rules

| Backend | Image tag handling | Multi-image behavior |
| --- | --- | --- |
| Transformers | Always prepends `"<image>\n"` once per provided image before the question. | Concatenates image patch tensors and passes `num_patches_list` when more than one image is provided. |
| vLLM | Prepends image tags only when the question does not already start with `"<image>\n"`. | Passes a single PIL image for one path or a list of PIL images for multiple paths; vLLM limit is configured as 20 images per prompt. |

When adapting prompts manually, avoid duplicate image tags. If the user supplies a pre-tagged vLLM prompt, verify the tag count still matches the supplied images because the native guard only checks the prefix.

## Dynamic image preprocessing parameters

The native image loader for Transformers uses:

| Parameter | Native value |
| --- | --- |
| `input_size` | `448` |
| `max_num` | `12` |
| `use_thumbnail` | `True` |
| normalization mean | `(0.485, 0.456, 0.406)` |
| normalization std | `(0.229, 0.224, 0.225)` |

The grid selection considers `(columns, rows)` products up to `max_num`, chooses the closest aspect-ratio grid, crops that resized canvas into tiles, and appends a thumbnail when the grid has more than one tile. Use [`../scripts/check_image_grid.py`](../scripts/check_image_grid.py) to estimate patch count without torch.

## Device mapping behavior

The native Transformers helper:

- Gets the number of visible CUDA devices from `torch.cuda.device_count()`.
- Reads `llm_config.num_hidden_layers` from model config with `trust_remote_code=True`.
- Computes layer allocation with `ceil(num_layers / (world_size - 0.5))`.
- Gives GPU 0 half of the usual language-layer capacity.
- Pins vision/model-head components to GPU 0, including the vision model, projector, token embeddings, output/norm/rotary components, language head, and the final language layer.

This means GPU 0 needs extra free memory. If GPU 0 OOMs while other GPUs are underused, consider reducing competing processes, changing visible-device order, adapting the device map, or using a larger tensor-parallel setup through vLLM.

## Dependency clues and safety classification

The source setup recipe pins these Transformers-side packages:

| Package | Pinned clue |
| --- | --- |
| `torch` | `2.6.0` |
| `torchvision` | `0.21.0` |
| `pillow` | `11.1.0` |
| `transformers` | `4.37.2` |
| `einops` | `0.6.1` |
| `einops-exts` | `0.0.4` |
| `timm` | `0.9.12` |
| `bitsandbytes` | `0.42.0` |
| `accelerate` | `1.5.2` |
| `flash-attn` | installed with `--no-build-isolation` |

Treat the setup recipe as heavy CUDA installation guidance, not as a safe bundled script. It can compile or install large GPU packages and should only be run in a deliberate model-inference environment. The bundled helpers here require only the Python standard library, except that `check_image_grid.py --image` uses Pillow when available.
