# Cross-Cutting Troubleshooting

Use this file for issues that cross multiple Pyramid-Flow workflows or that happen before you know which sub-skill owns the task.

## Fast triage

1. Run `python scripts/check_environment.py --repo PATH_TO_PYRAMID_FLOW`.
2. If repo imports fail, fix the checkout root on `PYTHONPATH` before debugging the workflow.
3. If CUDA is unavailable, generation, extraction, and training are not truthfully validated on the current host.
4. If the failure is workflow-specific, switch to the matching sub-skill's troubleshooting reference.

## Symptom table

| Symptom | Likely cause | Where to go |
| --- | --- | --- |
| `ModuleNotFoundError: pyramid_dit`, `video_vae`, `dataset`, `diffusion_schedulers`, or `trainer_misc` | The checkout root is not visible to Python, or a subdirectory was added instead of the repo root. | `references/installation.md` and `sub-skills/core-components/references/troubleshooting.md` |
| `torch.cuda.is_available()` is false | CPU-only torch build, missing driver/runtime visibility, or a container that does not expose GPUs. | `references/installation.md` and `sub-skills/core-components/references/troubleshooting.md` |
| `model path does not exist` or missing `config.json` under the requested variant | The checkpoint path is wrong or the selected model family does not match the path. | `sub-skills/generation-inference/references/troubleshooting.md` |
| `pyramid_flux` with a 768p request fails fast | The bundled generation helper intentionally rejects that incompatible pair. | `sub-skills/generation-inference/references/troubleshooting.md` |
| `image-path is required for image-to-video` | The image-to-video launcher was called without an input image. | `sub-skills/generation-inference/references/troubleshooting.md` |
| JSONL schema, latent shape, or missing `text_fea` problems | Annotation or precompute data does not match the data-preparation contract. | `sub-skills/data-preparation/references/troubleshooting.md` |
| `NUM_FRAMES`, `VIDEO_SYNC_GROUP`, `BATCH_SIZE`, or LPIPS-related launch failures | Training launch invariants or external checkpoints are inconsistent with the workflow. | `sub-skills/training-workflows/references/troubleshooting.md` |
| VAE encode/decode shape mismatch, scheduler stage errors, or device mismatch | Low-level model-component misuse. | `sub-skills/core-components/references/troubleshooting.md` |

## Checklist before escalating

- Confirm the requested workflow family and model family.
- Confirm whether the runtime is single-process, multi-GPU, or CUDA-less.
- Confirm whether the needed checkpoint, dataset, or LPIPS artifact exists.
- Confirm that the checkout root is importable before trying to debug deeper API issues.

## Escalation rule

If a failure reproduces in a tiny helper or smoke check, use the matching sub-skill. If it only appears in a long launch with missing external artifacts, keep it documented as a prerequisite rather than a code defect.
