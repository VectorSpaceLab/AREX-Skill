# Troubleshooting

| Symptom | Likely cause | Practical fix | Safe check |
|---|---|---|---|
| `Model path ... does not exist` | `--model-id` points to a missing folder or to a raw Hugging Face repo id | Download the checkpoint locally and rename it to a dot-free directory such as `./HunyuanImage-3`, `./HunyuanImage-3-Instruct`, or `./HunyuanImage-3-Instruct-Distil`. | The dry-run helper should warn if the path is missing or if the local directory name still contains dots. |
| `hunyuan-image` raises `TypeError` | The console script is wired to `main()` without parsed args | Use `scripts/run_hunyuan_image_generation.py` or the bundled dry-run helper instead of the broken console script. | The helpers stay off the console-script path entirely. |
| `Prompt is required` or editing fails early | Missing `--prompt`, missing `--image` for TI2I, or malformed flag mix | Provide the prompt, and supply `--image` for instruct / editing flows. Keep `--use-system-prompt custom` paired with `--system-prompt`. | The helper should reject the bad combination before generation starts. |
| `Image size should be in the format ...` | Bad `--image-size` syntax | Use `auto`, `1024x1024`, or a ratio form such as `16:9`. Explicit sizes are snapped to preset buckets by the image processor. | The helper can validate the shape string before launching anything. |
| Rewrite fails before the model runs | Missing `DEEPSEEK_KEY_ID` / `DEEPSEEK_KEY_SECRET`, or the current parser mismatch in the rewrite branch | Skip `--rewrite` until the credentials exist and the branch is patched. Treat this path as experimental in this snapshot. | The helper should surface missing credentials and the branch warning up front. |
| `flashinfer` or `flash_attention_2` is unavailable | Optional accelerators are not installed | Fall back to `--moe-impl eager` and `--attn-impl sdpa`. These accelerators are performance options, not baseline requirements. | The helper should warn, not assume they are installed. |
| CUDA out of memory or generation never stabilizes | The host is below the README's VRAM guidance for the 80B checkpoints | Reduce the checkpoint demand, reduce the sampling steps, or use a larger GPU cluster. Base generation is already heavy; instruct / distil demand even more memory. | The helper cannot fix capacity limits; it can only keep the command explicit. |
| `--help` or import-time inspection fails | The local environment is missing required dependencies, or the package stack is not installed in editable form | Install the declared requirements and keep the local dry-run helper for command validation when the model stack is unavailable. | The helper does not import `run_image_gen.py` or the model package. |

## Fast fallback path

If a user just needs a safe answer now, give them the dry-run helper first, then the explicit bundled-runner command shape, then the checkpoint reminder.

## Cross-skill boundary

- System-prompt selection and prompt rewriting details belong to `prompt-and-image-conditioning`.
- Model internals, tokenizer behavior, and API signatures belong to `core-apis-and-architecture`.
- vLLM serving issues belong to `vllm-serving`.
