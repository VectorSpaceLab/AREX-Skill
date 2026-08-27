# Inference troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import fails in `helios.modules.helios_kernels` | Missing or mismatched `kernels`/flash-attn build | Re-run `scripts/check_helios_env.py` and align the torch/CUDA wheel with a supported kernel variant |
| Demo import is slow or downloads weights immediately | The demo module preloads and compiles at import time | Treat the demo as a deployment flow, not a cheap smoke test |
| `torch.cuda.is_available()` is false | No CUDA backend is present | Switch to a CUDA-capable environment before attempting generation |
| `enable_low_vram_mode` and `enable_compile` are both set | The local source pipeline rejects that combination | Use one or the other, not both |
| Low-VRAM mode fails under `torchrun` | The local source path supports low-VRAM offload only for single-GPU runs | Disable low-VRAM mode for context-parallel runs or use a single GPU |
| mp4 export fails | `imageio-ffmpeg` is missing or the output path is not writable | Install/repair `imageio-ffmpeg` and choose a writable output directory |
| Multi-GPU run does nothing useful | `torchrun`/world-size setup or `cp_backend` is wrong | Use a supported context-parallel backend and launch with a real multi-GPU world |
| Image/video input is ignored | The mode and input type do not match | Use image input only for `i2v` and video input only for `v2v` |
| Distilled run is slower than expected | Wrong checkpoint or attention backend | Re-check the checkpoint, backend, and model family |

## Practical reminders

- Use a prompt-only test before large inputs.
- Keep the first run small enough to confirm that the backend, model cache, and
  output path all work.
- If the model hub rate-limits you, set the usual Hugging Face auth token in the
  shell environment before retrying.
