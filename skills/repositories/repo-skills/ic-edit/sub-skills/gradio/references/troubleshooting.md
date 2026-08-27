# ICEdit Gradio troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Address already in use` or the page never binds | The requested port is already taken | Re-run with a free `--port`. On busy machines, combine `--server-name 127.0.0.1`, `--no-browser`, and `--dry-run` first. |
| `ModuleNotFoundError: spaces` or Spaces-only assumptions | You are running the source script directly, or your environment lacks the Spaces helper | Use the bundled helper first. It falls back to a no-op GPU decorator outside Spaces. If you want the exact source-script behavior, install `spaces` from the repo requirements. |
| MoE mode cannot import the vendored package | The repo-local `icedit/` tree is missing from the checkout path | Run from an ICEdit checkout, or pass `--repo-root /path/to/ICEdit` so the helper can prepend `repo-root/icedit` to `sys.path`. Switch to `--mode normal` if you do not need MoE. |
| `CUDA out of memory` | The full model is too large for the GPU | Add `--enable-model-cpu-offload`. For lower-memory launches, use the GGUF recipe from `references/workflows.md`. The README notes that a 512×768 edit can need roughly 35 GB without offload. |
| GGUF file not found | `--transformer` or `--text-encoder-2` points at the wrong local file | Recheck both paths. These GGUF inputs are optional, but if you pass them they must exist on disk. |
| The image is silently resized | The input width is not 512 | Pre-resize the input to width 512 if you need exact framing. The helper will otherwise resize to width 512 and round the height down to a multiple of 8. |
| The result looks weak or style-shifted | The model is sensitive to seed and source image type | Try another seed, use one of the bundled presets, or switch to a more realistic source image. |
| The UI opens but edits fail on local weights | The base model or LoRA path is wrong | Recheck `--flux-path` and `--lora-path`. If you use local directories, confirm they contain the expected Flux and LoRA weights. |

## Quick recovery checklist
1. Check the port.
2. Verify the demo mode.
3. Confirm the model paths.
4. Decide whether CPU offload or GGUF is required.
5. Retry with a different seed if the result is valid but unsatisfactory.
