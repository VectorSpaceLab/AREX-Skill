# Qwen-VL inference troubleshooting

Use this reference for direct inference failures. For task recipes, see [workflows.md](workflows.md); for API signatures, see [api-reference.md](api-reference.md).

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model.chat` is missing | Loaded without Qwen custom code, or loaded the wrong class/model | Reload with `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)` and a chat checkpoint. |
| Answer ignores the instruction or behaves like autocomplete | `Qwen/Qwen-VL` base model was used for chat | Use `Qwen/Qwen-VL-Chat` or `Qwen/Qwen-VL-Chat-Int4` for assistant chat. Use base model only with `model.generate`. |
| `qwen.tiktoken` not found | Tokenizer merge file/checkpoint files are incomplete | Re-download the full model snapshot, including tokenizer files and all checkpoint shards. |
| `transformers_stream_generator`, `tiktoken`, or `accelerate` missing | Base inference dependencies are absent | Install the documented base requirements, especially `transformers==4.32.0`, `accelerate`, `tiktoken`, `einops`, and `transformers_stream_generator==0.0.4`. |
| Local checkpoint load fails after manual download | Incomplete sharded checkpoints or stale code | Verify all shard files are present; prefer an official full snapshot via Hugging Face or ModelScope; keep `trust_remote_code=True`. |
| `draw_bbox_on_latest_picture` returns `None` | No valid box markup or no image in latest history | Ask explicitly for boxes, keep the unmodified response, and pass `history` for chat rendering. |
| Box output is needed but text was cleaned first | `<ref>`/`<box>` tags were removed before rendering | Render first, then clean a copy of the response if the user wants plain text. |
| Int4 load fails with AutoGPTQ/import/build errors | Optional quantization stack is not installed or is incompatible | Use non-quantized `Qwen/Qwen-VL-Chat`, or prepare compatible `optimum` and AutoGPTQ wheels for the host PyTorch/CUDA stack. |
| CPU-only run appears hung or extremely slow | 7B multimodal model on CPU | Warn the user, reduce generation length, or move to CUDA with `device_map="cuda"`/`"auto"`. |
| Long-sequence quality is poor | Dynamic NTK/log attention config may be disabled | Check the model `config.json` for `use_dynamic_ntk` and `use_logn_attn` set to `true` when using long contexts. |

## Trust-remote-code failures and safety

Qwen-VL relies on repository-provided tokenizer/model code for multimodal formatting, `model.chat`, and box rendering. If `trust_remote_code=True` is omitted, the load may fail or silently lack Qwen-specific methods.

Safe operating pattern:

1. Ask the user to confirm the model ID or local snapshot source.
2. Prefer official model IDs: `Qwen/Qwen-VL`, `Qwen/Qwen-VL-Chat`, `Qwen/Qwen-VL-Chat-Int4`, or their ModelScope `qwen/...` mirrors.
3. If using a local directory, ensure it came from a trusted full snapshot and contains tokenizer files, config, model shards, and custom code.
4. Keep `trust_remote_code=True` for Qwen-VL inference unless the code has been separately audited and packaged.

## Base model versus chat model mismatch

The most common inference mistake is using `Qwen/Qwen-VL` for a chat prompt.

- `Qwen/Qwen-VL`: pretrained base LVLM. Use `tokenizer(...)` plus `model.generate(...)`. Expect generated text, prompt echoing, or grounding-caption behavior rather than aligned assistant dialogue.
- `Qwen/Qwen-VL-Chat`: aligned assistant. Use `tokenizer.from_list_format(...)` plus `model.chat(...)` with `history`.
- `Qwen/Qwen-VL-Chat-Int4`: quantized aligned assistant. Same chat API, but optional quantization dependencies are required.

If a user reports that the generation is unrelated to the instruction, first check the model ID before tuning prompts.

## Bounding-box and grounding problems

### The model returns text but no boxes

Try a direct grounding prompt:

```text
Frame the main object in the image and return bounding boxes.
```

or:

```text
输出图中所有车辆的检测框。
```

Then inspect whether the raw response contains `<box>(x1,y1),(x2,y2)</box>`. If not, the renderer has nothing to draw.

### Rendering returns no image

For chat, use:

```python
image = tokenizer.draw_bbox_on_latest_picture(response, history)
```

For base generation, use:

```python
image = tokenizer.draw_bbox_on_latest_picture(response)
```

Do not pass `history=None` to the chat renderer after an image turn; the renderer needs the image context stored in history.

### The user wants the caption without tags

Keep two values:

1. `raw_response` for rendering and coordinate inspection.
2. `clean_response` created with the regex in [api-reference.md](api-reference.md) for display-only text.

## CPU, CUDA, and precision caveats

- CPU-only: acceptable for code-path checks and small experiments, but it may be very slow and memory-heavy. Warn before launching a real generation.
- CUDA: preferred for practical inference. Use `device_map="cuda"` for a single CUDA target or `device_map="auto"` when Accelerate should decide placement.
- BF16: useful on GPUs that support bfloat16 well.
- FP16: common alternative and required by the training Q-LoRA path, but direct inference can use non-quantized BF16/FP16 depending on hardware.
- Int4: memory-efficient but optional; do not promise it unless AutoGPTQ/optimum are installed and compatible.

## Quantization documentation conflicts

Some older Qwen-VL notes say quantization is unsupported. The released inference path includes `Qwen/Qwen-VL-Chat-Int4` based on AutoGPTQ. Resolve the conflict this way:

1. If the user wants the official released Int4 chat checkpoint, use `Qwen/Qwen-VL-Chat-Int4`.
2. Require `optimum` and a compatible AutoGPTQ build.
3. If the optional stack is unavailable, use `Qwen/Qwen-VL-Chat` and document that Int4 is not verified in the current environment.
4. Do not apply Int4 instructions to `Qwen/Qwen-VL` base unless the user provides a compatible quantized base checkpoint.

## Generation length and performance

Large image+text contexts consume many tokens. If generation is slow or memory spikes:

- Reduce `max_new_tokens`.
- Use a shorter prompt or fewer images.
- Prefer CUDA and lower precision when supported.
- Consider Int4 only after optional quantization dependencies are prepared.
- Avoid repeated model reloads in loops; load once, then run multiple prompts.

## Network and download control

The first `from_pretrained` or `snapshot_download` call may download model weights and custom code. Before running:

- Confirm the user permits network access and model downloads.
- Use `local_files_only=True` if the model is already cached and network must be avoided.
- Use ModelScope snapshot loading when Hugging Face access is blocked or the user requests ModelScope.
- For local snapshots, pass the local directory as the model ID and keep `trust_remote_code=True`.

## Streaming and serving confusion

Direct `model.chat` inference here is not an OpenAI-compatible streaming server. If the user asks for a web demo, API endpoint, port binding, streaming behavior, Docker launch, or server exposure settings, route to the `serving` sub-skill instead of extending this direct inference workflow.
