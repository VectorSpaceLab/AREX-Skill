# Troubleshooting

This reference collects cross-cutting AnyDoor failures that affect more than one
sub-skill.

## Install and import failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for `cldm`, `datasets`, or `ldm` | The repo is not on `PYTHONPATH`, or the current directory is not the repo root. | Run the environment checker from the repo root and confirm the source tree is visible. |
| `No module named xformers` | Optional dependency missing. | Usually safe to continue; the attention code has a fallback. Record it as optional, not fatal. |
| `share==1.0.4` cannot be installed | Package unavailable from the configured index. | Treat it as a limitation of the conversion helper only unless you specifically need that script. |
| Torch imports but CUDA is unavailable | CPU-only torch, driver mismatch, or wrong backend wheel. | Reinstall a CUDA-capable torch build and rerun the smoke test. |

## Checkpoint and path failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Generation fails immediately on `path/epoch=...ckpt` | Placeholder checkpoint value was never patched. | Use the config patcher and supply a real checkpoint. |
| DINOv2 encoder fails to load `path/dinov2_vitg14_pretrain.pth` | Placeholder DINOv2 path or missing weight file. | Patch `configs/anydoor.yaml` and verify the file exists. |
| Demo refinement toggle fails | Optional `iseg` weight is missing or the toggle is enabled without the file. | Turn the toggle off or supply the bundled weight. |
| Conversion script complains about `./models/anydoor.yaml` | The source helper uses a stale path. | Use the bundled conversion wrapper and override the config path explicitly. |

## Data and mask failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Empty generation target or reference mask | Mask file is blank or thresholded incorrectly. | Validate the mask with the input checker before running inference. |
| RGB image but mask has the wrong channel layout | Separate mask path was not supplied or an RGBA assumption was wrong. | Use the validator to derive a binary mask or supply the correct mask file. |
| Dataset load errors for VITON-HD / DressCode / FashionTryon | The mask label convention is wrong. | Read the dataset-format reference for the exact foreground label. |
| `datasets` imports the Hugging Face package instead of the local folder | Name shadowing. | Run from the repo root with the repo on the module search path. |

## Demo and service failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Gradio launches but the output is wrong | The reference/background masks are coarse or non-binary. | Re-run the validation script and refine the masks. |
| `use_interactive_seg` appears ignored | The source demo script has a config assignment bug. | Document the caveat and treat the interactive segmentation path as optional. |
| Cog download takes over | The predictor tries to fetch a model cache. | Use the deployment reference and note the network dependency. |

## Training failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Training never starts cleanly | Dataset paths in `configs/datasets.yaml` are still placeholders. | Patch the dataset config or use the dataset config checker. |
| Lightning/DDP setup complains about world size or GPUs | The source training defaults assume a multi-GPU CUDA environment. | Match the host resource plan or keep training as a documented workflow only. |
| `pycocotools`, `lvis`, or `panopticapi` imports fail | Dataset extras were not installed. | Install the dataset helper packages and rerun the environment smoke. |

## Recovery policy

- Prefer a bundled checker or patcher before editing source files by hand.
- Prefer a small validation or dry-run before a heavy inference or training run.
- If a required checkpoint or dataset is missing, stop and record the missing
  asset instead of guessing.
- If the issue is backend-related, verify the CUDA host and torch wheel before
  blaming the model code.

## Which sub-skill owns the follow-up

- `setup-and-checkpoints` owns install, import, backend, and placeholder-path
  fixes.
- `inference-and-demo` owns mask/image validation, demo launch issues, and Cog
  deployment symptoms.
- `data-and-training` owns dataset layout, preprocessing, training, and weight
  conversion problems.
