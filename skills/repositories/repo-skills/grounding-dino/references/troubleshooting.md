# GroundingDINO Troubleshooting

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: groundingdino` | Package not installed in the active Python. | Install the package, then run `python scripts/check_grounding_dino_install.py`. |
| Setup tries to install Torch during metadata generation and fails | `setup.py` imports Torch before package metadata is complete. | Install compatible `torch` and `torchvision` first, then reinstall GroundingDINO. |
| `Failed to load custom C++ ops. Running on CPU mode Only!` | `groundingdino._C` extension was not built or cannot import. | For CPU workflows this can be acceptable; for CUDA/full performance, set a matching `CUDA_HOME`, ensure the compiler/toolkit match Torch, and reinstall. |
| `NameError: name '_C' is not defined` | Custom op import failed but a code path tried to call it. | Reinstall with the correct CUDA/Torch/toolkit combination, or use a CPU-compatible path that avoids custom CUDA ops. |
| `pycocotools` import errors | COCO evaluation dependency missing or broken. | Install `pycocotools` in the target environment and rerun evaluator checks. |

## Configs, Checkpoints, And Devices

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing checkpoint/config file | Helper was given a path that does not exist. | Download or provide the intended release checkpoint and use the matching config path. |
| State dict loads with many missing/unexpected keys | Config/checkpoint mismatch or wrong checkpoint file. | Pair Swin-T config with Swin-T OGC checkpoint and Swin-B config with Swin-B checkpoint. |
| CUDA selected but unavailable | CPU-only Torch, missing driver passthrough, or invalid device string. | Use `--device cpu` or install a CUDA-enabled Torch build on a GPU host. |
| CPU inference is too slow | Full model inference and evaluation are compute-heavy. | Use CUDA for production runs, reduce input volume, or use CPU only for smoke validation. |

## Workflow Routing

- Single image, token spans, annotated output: `../sub-skills/inference/`.
- COCO AP and benchmark diagnosis: `../sub-skills/evaluation/`.
- Folder pseudo-labeling and COCO export: `../sub-skills/dataset-annotation/`.
- Web demo, HF downloads, SAM/GLIGEN/Stable Diffusion handoffs: `../sub-skills/integrations/`.

## Data And Optional Dependencies

- COCO evaluation requires a real annotation JSON and matching image directory; mini-subsets are smoke checks, not benchmark evidence.
- Pseudo-labeling with FiftyOne requires optional workflow dependencies and should default to non-GUI mode unless the user wants a local viewer.
- Gradio and Hugging Face checkpoint helpers are optional integration dependencies; do not install or download them unless the user selects that route.
