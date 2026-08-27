# Dipy Cross-Cutting Troubleshooting

Use this reference for failures that span several Dipy task families. Route workflow-specific details to the nearest sub-skill.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: dipy` | Dipy is not installed in the active Python environment | Install Dipy in the environment that will run the code, then run `python scripts/check_dipy_install.py`. |
| Import fails only inside a source checkout | The checkout shadows the installed wheel or generated build metadata is missing | Run from outside the checkout, install Dipy normally, or ensure the checkout has been built before importing. |
| Console command exists but imports fail | Shell entry point and Python interpreter come from different environments | Compare `python scripts/check_dipy_install.py --format json` with `python sub-skills/cli-workflows/scripts/dipy_cli_probe.py --check-help dipy_info`. |
| `fury`, `matplotlib`, `torch`, or `tensorflow` is missing | Optional visualization or neural-network extra was not installed | Use numeric/non-GUI workflows by default, or install only the optional extra needed for the requested task. |
| Editable install rebuild fails with Meson/Ninja errors | Compiled extension build state is incomplete or backend tools are unavailable | Prefer a normal wheel install for using Dipy; use repository build tooling only for maintainer work. |

## Data Validation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| DWI volume count disagrees with gradients | `data.shape[-1]`, `len(bvals)`, or `bvecs.shape[0]` mismatch | Use `sub-skills/io-data/` to validate sidecars before modeling or preprocessing. |
| Non-b0 b-vectors are rejected | Vectors are transposed, unnormalized, or paired with the wrong b-values | Re-read bvals/bvecs, inspect `(N, 3)` shape, and adjust `atol` only for small numeric tolerance. |
| Mask shape errors | 3D mask does not match `data.shape[:3]` | Rebuild or resample the mask before fitting, denoising, registration, or tracking. |
| Tractogram bbox/reference errors | Streamline coordinates, `Space`, `Origin`, or reference image/header are inconsistent | Use `sub-skills/io-data/` to normalize `StatefulTractogram` state before saving or analysis. |
| All-zero or NaN model outputs | Bad signal range, over-broad mask, missing b0, or unsuitable model choice | Use `denoising-preprocessing` to repair inputs and `reconstruction-models` to choose a simpler fit or validate signals. |

## CLI And Workflow Safety

- Run `COMMAND --help` before building production commands; Dipy CLIs are generated from workflow classes and docstrings.
- Use explicit `--out_dir` and output names, and add `--force` only when overwriting is safe.
- Treat `dipy_fetch` downloads as network/cache-mutating operations; `dipy_fetch list` is discovery only.
- Treat whole-brain tracking, full-image registration, MAPMRI/DSI/FORCE/RUMBA-style fits, BUAN group analysis, and neural workflows as potentially expensive.
- Use `sub-skills/cli-workflows/` when a command is missing, deprecated, or behaves differently from a Python API recipe.

## Optional Surfaces

- Visualization: `dipy_horizon` and plotting helpers may need FURY, matplotlib, display, or OpenGL/headless setup.
- Neural networks: `dipy_evac_plus` and neural bias correction paths can need ML dependencies and model assets.
- Patch2Self: selected models can require scikit-learn-compatible estimators; scripts may skip this check when optional dependencies are absent.
- BundleWarp and some statistics/plotting workflows can require additional scientific or plotting packages depending on selected outputs.

## Sub-Skill Recovery Routes

- Files, affines, gradients, tractograms, PAM, and dataset fetches: `sub-skills/io-data/`.
- Denoising, noise estimation, Gibbs removal, Patch2Self, and bias correction: `sub-skills/denoising-preprocessing/`.
- Model choice, tensor/CSD/DKI/ODF/peaks, scalar maps, and reconstruction CLIs: `sub-skills/reconstruction-models/`.
- Tractography, streamlines, clustering, bundle recognition, masks, tissue classification, AFQ, and BUAN: `sub-skills/tracking-segmentation/`.
- Reslice, affine/SyN registration, transforms, motion correction, SLR, and BundleWarp: `sub-skills/registration-alignment/`.
- Command discovery, parser mechanics, and output naming: `sub-skills/cli-workflows/`.
