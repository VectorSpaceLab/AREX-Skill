# Neuralangelo Repo Skill Provenance

Schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: `NVlabs/neuralangelo`
- Remote URL: `https://github.com/NVlabs/neuralangelo.git`
- Branch inspected: `main`
- Commit inspected: `94390b64683c067c620d9e075224ccfe582647d0`
- Generation date (UTC): `2026-08-16T04:18:45Z`
- Generated skill id: `neuralangelo`
- Generated runtime skill directory: `skills/disco/neuralangelo/`
- Import policy for this run: not imported by user request.

Working tree state at handoff: dirty from generated `skills/` outputs only. The source-code baseline itself was not modified during skill construction.

## Evidence Scope

This skill distills operating behavior from the repository's public runtime surface and supporting source modules:

- Environment specs and dependency evidence: `neuralangelo.yaml`, `requirements.txt`.
- User-facing workflow evidence: project overview, data-processing notes, training launch surface, config templates, and extraction guidance.
- Runtime source evidence: `train.py`, `imaginaire.config.Config`, training utilities, checkpoint/logging utilities, `projects/nerf/`, and `projects/neuralangelo/` model/data/trainer/util modules.
- Data-preparation evidence: custom config generation, COLMAP/DTU/Tanks-and-Temples conversion code paths, video/COLMAP preprocessing shell behavior, and coordinate/bounds handling.
- Mesh-extraction evidence: extraction CLI, mesh utility behavior, marching-cubes/blocking/texturing/largest-component logic, and dataset coordinate readjustment.
- Native verification evidence: safe `--help` checks for training, config generation, conversion, and extraction entry points; core CUDA/import checks for `torch`, `torchvision`, `tinycudann`, `Config`, `Model`, `Dataset`, and `Trainer`.

Excluded as direct runtime dependencies for this skill:

- Large datasets, pretrained checkpoints, downloads, and end-to-end training runs.
- Interactive notebooks and visualization-only assets.
- Most vendored COLMAP internals, except the conversion behavior distilled into data-preparation guidance.
- Private local environment paths and private checkout paths.

## Verified Environment Baseline

A CUDA-capable inspection environment was prepared and verified for skill drafting. The successful baseline used:

- Python 3.9 for inspection, selected because a compatible prebuilt `tinycudann` package was available.
- PyTorch `2.6.0` with CUDA support.
- TorchVision `0.21.0`.
- `tinycudann` `1.7`.
- NumPy `1.26.4`.
- PyYAML, addict, OpenCV headless, trimesh, PyMCubes, and W&B packages sufficient for import/help inspection.
- Host capability: 8 NVIDIA A100-SXM4-40GB GPUs, driver `580.126.20`, compute capability `8.0`.

Important compatibility note: the repository's original environment file names Python 3.8. A Python 3.8 attempt reached useful dependency installation but source builds of tiny-cuda-nn failed through CUDA/header/ABI issues on the inspected host. The verified drafting route used Python 3.9 plus a prebuilt tiny-cuda-nn package instead. Future agents should prefer a working CUDA/tiny-cuda-nn combination over mechanically reproducing the original environment file.

## Source-to-Skill Replacement Map

The generated skill does not rely on repository documentation or examples at runtime. The relevant behavior is distilled or wrapped as follows:

| Source behavior | Runtime skill replacement |
| --- | --- |
| Environment setup and import expectations | `references/installation-and-environment.md`, `scripts/check_neuralangelo_environment.py` |
| Video/COLMAP/DTU/Tanks-and-Temples preparation guidance | `sub-skills/data-preparation/references/` and `sub-skills/data-preparation/scripts/plan_preprocessing_commands.py` |
| `transforms.json` metadata expectations | `sub-skills/data-preparation/references/data-formats.md` and `sub-skills/data-preparation/scripts/validate_transforms_json.py` |
| Custom YAML config generation | `sub-skills/data-preparation/scripts/generate_config_from_images.py` and `sub-skills/training-and-configs/references/configuration.md` |
| Training launch/config/resume behavior | `sub-skills/training-and-configs/references/` and `sub-skills/training-and-configs/scripts/plan_training_command.py` |
| Runtime entry-point delegation | `scripts/run_neuralangelo_entrypoint.py` |
| Mesh extraction planning and output validation | `sub-skills/mesh-extraction/references/`, `sub-skills/mesh-extraction/scripts/plan_mesh_extraction.py`, and `sub-skills/mesh-extraction/scripts/validate_mesh_file.py` |

## Refresh Signals

Refresh this repo skill if any of these change in a newer Neuralangelo commit:

- Environment requirements for PyTorch, CUDA, tiny-cuda-nn, Python, image/mesh dependencies, or W&B.
- Training CLI flags, distributed launch behavior, config override semantics, checkpoint layout, or logging layout.
- YAML schema under the base/custom/DTU/Tanks-and-Temples configs.
- Dataset `transforms.json` schema, pose conventions, bounding sphere/AABB handling, image subdirectory expectations, or conversion scripts.
- Mesh extraction CLI flags, grid/block/texturing/largest-component logic, output coordinate transformation, or PLY export behavior.
- Module/class names for `Config`, `Model`, `Dataset`, or `Trainer`.
