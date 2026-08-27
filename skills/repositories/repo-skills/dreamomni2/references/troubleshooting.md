# Troubleshooting

This page collects the shared DreamOmni2 failure modes that affect both the CLI and the Gradio demos.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` while importing `torch` mentioning `iJIT_NotifyEvent` | The PyTorch build on this host needs an Intel ITT shared library at runtime | Use a CUDA build of PyTorch that bundles a compatible runtime or make the Intel ITT library available before retrying the environment check |
| `ImportError: cannot import name 'patch_npu_record_stream' from 'utils'` | The repository's `utils/` directory is a namespace directory with no `__init__.py`; the standalone scripts rely on a direct package import that is not defined | Use the bundled helpers in this skill or import from `utils.utils` instead of `from utils import ...` |
| `torch.cuda.is_available()` is false | The environment is CPU-only, the wrong wheel was installed, or the driver/runtime is not visible inside the environment | Re-run `scripts/check_env.py`, confirm the CUDA wheel, and make sure the host GPU is visible to the environment |
| The bundled scripts cannot locate the DreamOmni2 checkout | The wrapper was launched from outside the repository root and no checkout hint was provided | Run from the DreamOmni2 repo root, pass `--repo-root` to `scripts/check_env.py`, or set `DREAMOMNI2_REPO_ROOT` before launching the bundled scripts |
| Model path errors such as missing `vlm-model`, `edit_lora`, or `gen_lora` | The local model directories were not created or the path points at the wrong cache | Use `scripts/check_models.py` and correct the model paths before launching the workflow |
| The edit output ignores the intended source image | The edit workflow expects the source image first and the reference image second | Reorder the input paths so the source image is first |
| The output looks cropped or strangely resized | The prompt stage and diffusion model prefer Kontext-style aspect buckets | Leave `height`/`width` at the defaults or choose a nearby aspect ratio from the supported buckets |
| Gradio fails to launch or the page stays blank | Port conflict, blocked browser access, or a model-load failure before the UI starts | Choose another port, confirm the process has access to the model paths, and inspect the console log before refreshing the browser |
| The workflow OOMs on load or generation | The VLM and FLUX stack is large and the chosen image size is too aggressive | Reduce the requested output size, ensure the GPU has enough VRAM, or use a larger GPU |
| The prompt text looks malformed | The VLM output format changed and the wrapper's text-stripping logic no longer matches the response | Inspect the raw VLM output and update the prompt-extraction helper in `scripts/dreamomni2_common.py` if needed |

## Shared recovery checklist

1. Run `scripts/check_env.py`.
2. Run `scripts/check_models.py`.
3. Confirm the CUDA GPU is visible and that the correct model paths exist.
4. Re-run the relevant inference or web launcher with the source image first for editing workflows.
