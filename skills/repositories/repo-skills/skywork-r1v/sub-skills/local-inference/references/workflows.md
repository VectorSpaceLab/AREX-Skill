# Local inference workflows

This reference explains how to choose and adapt the local Skywork-R1V3 inference paths. It intentionally avoids running heavyweight CUDA/model code. Use the bundled helpers for safe command construction and patch-count estimation.

## Model naming and setup boundary

- Current local inference default: `Skywork/Skywork-R1V3-38B`.
- The public README's local-run examples use a user-supplied model path placeholder; replace it with a prepared local checkpoint directory or an accessible model id.
- Older release notes mention earlier `Skywork-R1V`/`Skywork-R1V2` variants and AWQ variants for those earlier releases. Do not assume a quantized R1V3 checkpoint exists unless the user supplies one.
- Full local inference requires a Python environment with CUDA-capable PyTorch and either Transformers or vLLM. The source setup recipe is a heavy CUDA install and is documented as reference-only in [`api-and-parameters.md`](api-and-parameters.md).

## README local-run shape

The public local-run recipe has this shape:

1. Obtain the Skywork-R1V source and enter the directory that contains the native inference entrypoints.
2. For Transformers, create a Python 3.10 environment and install the heavy CUDA/Transformers stack before running `inference_with_transformers.py`.
3. For vLLM/evaluation, create a separate Python 3.10 environment and install the vLLM/evaluation stack before running `inference_with_vllm.py`.
4. The README Transformers example uses visible CUDA devices plus `--model_path`, `--image_paths`, and `--question`.
5. The README vLLM example uses `--model_path`, one or more `--image_paths`, `--question`, and `--tensor_parallel_size 4`.

Use the bundled command builder to render those command shapes safely before attempting a real run.

## Backend choice

| Choose | When to use | Main constraints |
| --- | --- | --- |
| Transformers | You need the native `model.chat()` path, explicit image tiling, or want to adapt generation config directly. | Loads a 38B multimodal checkpoint, uses `trust_remote_code=True`, bfloat16, flash-attn, explicit `.cuda()`, and a custom device map. No CPU fallback for full inference. |
| vLLM | You need tensor-parallel generation with vLLM and tokenizer chat-template formatting. | Requires a vLLM version compatible with the model's remote code, enough GPUs for `tensor_parallel_size`, and multimodal prompt/image limits. |

## Safe command construction

Use the command builder before attempting a real model run:

```bash
python scripts/build_inference_command.py --backend transformers \
  --model-path Skywork/Skywork-R1V3-38B \
  --image-path image1.png \
  --question "What is shown?"
```

For multiple images and vLLM:

```bash
python scripts/build_inference_command.py --backend vllm \
  --model-path MODEL_DIR_OR_ID \
  --image-path image1.png image2.png \
  --question "Compare the two images." \
  --tensor-parallel-size 4 \
  --temperature 0.0 \
  --max-tokens 8000
```

Add `--print-prereqs` to include a short prerequisites checklist above the command. The helper only prints a deterministic command; it does not import model libraries or touch image files.

## Transformers workflow

The native Transformers path performs these operations:

1. Parse `--model_path`, one or more `--image_paths`, and required `--question`.
2. Build a CUDA device map with `split_model(model_path)`.
3. Load the model through `AutoModel.from_pretrained(...)` with:
   - `torch_dtype=torch.bfloat16`
   - `load_in_8bit=False`
   - `low_cpu_mem_usage=True`
   - `use_flash_attn=True`
   - `trust_remote_code=True`
   - the computed `device_map`
4. Load the tokenizer with `AutoTokenizer.from_pretrained(..., trust_remote_code=True, use_fast=False)`.
5. For each image, run the image loader with `max_num=12`, convert to bfloat16, and move patches to CUDA.
6. If there are multiple images, concatenate the patch tensors and pass `num_patches_list` so the model can separate each image. For a single image, `num_patches_list` is `None`.
7. Build the prompt as `"<image>\n" * number_of_images + question`.
8. Call `model.chat(...)` with generation config: `max_new_tokens=64000`, `do_sample=True`, `temperature=0.6`, `top_p=0.95`, `repetition_penalty=1.05`.

Practical notes:

- The 64k token cap is very large. Lower it in an adapted script for smoke tests, demos, or constrained VRAM.
- The source entrypoint does not expose sampling flags on its CLI; changing sampling requires editing or wrapping the generation config.
- Because image tensors are moved with `.cuda()`, a CPU-only machine cannot run the full native Transformers path.

## vLLM workflow

The native vLLM path performs these operations:

1. Parse `--model_path`, `--tensor_parallel_size` (default `4`), one or more `--image_paths`, required `--question`, and sampling flags.
2. Load images with PIL and pass either a single image or a list of images.
3. If the question does not start with `"<image>\n"`, prepend one image token per image. If the question already starts with an image token, the helper leaves it unchanged.
4. Load a tokenizer and apply its chat template with `tokenize=False` and `add_generation_prompt=True`.
5. Initialize `LLM(...)` with `trust_remote_code=True`, `limit_mm_per_prompt={"image": 20}`, `gpu_memory_utilization=0.7`, and the requested tensor-parallel size.
6. Generate with `SamplingParams(temperature, top_p, max_tokens, repetition_penalty)` and `multi_modal_data={"image": images}`.

Practical notes:

- Keep raw image count at or below the vLLM multimodal limit unless you adapt the vLLM initialization.
- Increase `tensor_parallel_size` only when enough visible GPUs are available and the model/runtime supports that degree of tensor parallelism.
- The default vLLM temperature is deterministic-style (`0.0`); the Transformers source path samples at `0.6`.

## Image tiling and prompt tags

The Transformers image loader uses dynamic tiling:

- It considers tile grids whose column count times row count is between `min_num` and `max_num` (`max_num=12` in the native loader).
- It chooses the grid whose aspect ratio is closest to the image aspect ratio.
- Each tile is resized to `448 x 448` before tensor conversion.
- With thumbnail mode enabled, it appends one extra square thumbnail when the chosen grid has more than one tile.
- The native `load_image` path always enables thumbnail mode, so a wide/tall image can produce up to `12 + 1` patch tensors.

Estimate this safely with:

```bash
python scripts/check_image_grid.py --image image1.png --thumbnail
python scripts/check_image_grid.py --width 3000 --height 1000 --max-num 12 --thumbnail
```

For multiple images in Transformers, estimate each image separately and sum the `total_patches`; the model also receives `num_patches_list` so it can map patch groups back to images.

## GPU and tensor-parallel planning

- Transformers `split_model()` reads the language layer count from model config and maps layers across all visible CUDA devices.
- GPU 0 is assigned half layer capacity because it also hosts vision/model-head components such as the vision model, projector, embeddings, norm, rotary embedding, output, and language head.
- vLLM defaults to `--tensor_parallel_size 4` and `gpu_memory_utilization=0.7`. Raise or lower the tensor-parallel size based on visible GPUs, VRAM, and runtime compatibility.
- If the user asks for a CPU run of the full 38B model, state that the native scripts do not provide a CPU fallback.

## Excluded workflows

- R1V4 API batch testing belongs to `r1v4-api-testing`.
- VLMEvalKit, EMMA, MMK12, and benchmark reproduction belong to `evaluation-reproduction`.
- This sub-skill can help construct local inference commands that later feed evaluation workflows, but it does not score benchmark outputs.
