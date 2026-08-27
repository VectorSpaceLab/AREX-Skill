# Local inference troubleshooting

Use this guide when a local Skywork-R1V3 Transformers or vLLM run fails. The bundled helpers remain safe to run because they do not load models.

## Quick triage

1. Confirm backend: Transformers or vLLM.
2. Confirm model path: local checkpoint directory or accessible model id.
3. Confirm CUDA: the native full run requires CUDA and enough VRAM; there is no CPU fallback for the 38B model in the native scripts.
4. Confirm image paths and image-token count.
5. Reduce token budget for smoke tests before diagnosing deeper model issues.

## Symptoms and fixes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Model path not found, gated download error, or slow startup | Model id/path is wrong, weights are not cached, network access is unavailable, or remote model code/config must be fetched. | Pass an explicit prepared checkpoint path with `--model_path`; pre-download weights in the target environment; verify tokenizer/config files exist; expect first load to be slow. |
| Error mentions custom code, unknown architecture, or missing model class | `trust_remote_code=True` was removed or blocked. | Keep `trust_remote_code=True` for AutoModel/AutoTokenizer and vLLM model loading. Review remote code policy before running in a sensitive environment. |
| `torch.cuda.is_available()` false, `.cuda()` failure, or zero visible devices | CUDA runtime is unavailable or devices are hidden. | Do not attempt full native inference on CPU. Check driver/runtime compatibility and visible-device settings; run only the safe helpers until CUDA is ready. |
| `flash-attn` build/import failure | CUDA/PyTorch/compiler versions do not match the flash-attn build. | Install the pinned torch stack first, then install flash-attn with a compatible wheel or build environment. If adapting the script to disable `use_flash_attn`, expect slower and more memory-intensive inference. |
| CUDA OOM during Transformers load or generation | 38B model plus image patches and long token limit exceed available VRAM; GPU 0 carries extra vision/head modules. | Free GPU memory, use more GPUs, reorder visible devices so GPU 0 has the most free memory, lower generation length in an adapted script, reduce image count/resolution pressure, or switch to vLLM/tensor parallel if appropriate. |
| CUDA OOM in vLLM | Tensor parallel size or memory utilization does not fit the checkpoint and prompt. | Increase `--tensor_parallel_size` when more GPUs are available, lower `--max_tokens`, reduce image count, leave headroom around `gpu_memory_utilization=0.7`, and verify no other processes occupy the GPUs. |
| vLLM import/service error | vLLM is not installed, incompatible with the CUDA/PyTorch stack, or cannot load the model's remote code. | Install a compatible vLLM stack in the intended inference environment; keep `trust_remote_code=True`; verify the model can be initialized before using it behind a service. |
| Tokenizer chat-template error in vLLM | Tokenizer files are incomplete or incompatible with the installed Transformers version. | Verify the checkpoint includes tokenizer files and chat template support; use a Transformers version compatible with the model. |
| Image file not found or PIL decode error | Bad path, unsupported image, or corrupt file. | Validate paths before full inference. The command builder does not check files; use a small image-open smoke in the target environment if needed. |
| Wrong number of image tags | Prompt already contains image tags, or multi-image prompt was edited manually. | Transformers prepends one tag per image automatically. vLLM prepends tags only if the question does not already start with `"<image>\n"`; if manually tagged, ensure exactly one tag per image. |
| Unexpected memory usage with multiple images | Each image may become many patch tensors; thumbnails add one extra patch for multi-tile images. | Use `python scripts/check_image_grid.py --image your_image.png --thumbnail` per image and sum `total_patches`. With `max_num=12`, one image can produce up to 13 patches. |
| Very slow response or runaway generation | Native Transformers cap is `max_new_tokens=64000`; vLLM default is `8000`. | For tests, lower max generation length in an adapted Transformers script or pass a lower `--max-tokens` to vLLM. Keep long limits only for deliberate reasoning runs. |
| Request asks for single-card CPU or laptop inference | Native local scripts target the 38B model on CUDA and do not include a CPU fallback. | Explain the limitation. Use only safe command/image helpers locally, or ask the user for a smaller/quantized compatible checkpoint if they have one. |

## Backend-specific reminders

### Transformers

- Requires `AutoModel`, `AutoTokenizer`, torch bfloat16, flash-attn, and a valid device map.
- The native image path sends tensors to CUDA directly.
- Sampling values are hard-coded unless the script is adapted.
- `split_model()` reserves GPU 0 for vision/model-head components and gives GPU 0 fewer language layers, but GPU 0 still needs substantial free memory.

### vLLM

- Default tensor parallel size is 4.
- The native initialization caps multimodal prompts with `limit_mm_per_prompt={"image": 20}`.
- `gpu_memory_utilization=0.7` leaves headroom; raising it can improve capacity but may make OOMs harder to recover from.
- The default temperature is `0.0`, unlike the sampling Transformers path.

## Safe diagnostics before a full run

```bash
python scripts/build_inference_command.py --backend vllm \
  --model-path Skywork/Skywork-R1V3-38B \
  --image-path image1.png image2.png \
  --question "Compare the images." \
  --print-prereqs

python scripts/check_image_grid.py --width 2400 --height 1200 --max-num 12 --thumbnail
```

If these helpers produce the expected command and patch estimate, remaining failures are likely in the target CUDA/model/vLLM environment rather than in argument construction.
