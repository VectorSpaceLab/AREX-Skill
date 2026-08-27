# Install And Data Setup

Habitat-Lab is a monorepo with separate installable packages for core APIs, baselines, and HITL support. Setup success depends on matching `habitat-sim`, `magnum`, Python, and physics/graphics requirements before running config or environment code.

## Package Roles

- `habitat-lab`: core package exposing `habitat`, config composition, `Env`, datasets, tasks, registries, and vector envs.
- `habitat-baselines`: optional training/evaluation package exposing `habitat_baselines`, Hydra baselines configs, trainers, and the `habitat-baselines` console entry point.
- `habitat-hitl`: optional human-in-the-loop package for interactive apps and clients.
- `habitat-sim`: required simulator dependency for most meaningful Habitat-Lab imports and runtime use; it supplies `habitat_sim`, `magnum`, rendering, scene loading, and optional Bullet physics support.

The inspected package set for this skill was version `0.3.3` for `habitat-lab`, `habitat-baselines`, `habitat-hitl`, and `habitat-sim`. Public skill guidance should still prefer compatibility checks over hard-coded assumptions because users may install newer forks or releases.

## Recommended Install Shape

The public README recommends a conda environment with Python 3.9 and CMake, then installing Habitat-Sim before editable Habitat-Lab packages. This remains the safest recommendation because current Habitat-Sim binary availability is tied to conda/Python compatibility.

Typical order:

```bash
conda create -n habitat python=3.9 cmake=3.14.0
conda activate habitat
conda install habitat-sim withbullet -c conda-forge -c aihabitat
pip install -e habitat-lab
pip install -e habitat-baselines
```

Use `pip install -e habitat-baselines` only when the user needs trainers, baseline configs, or the `habitat-baselines` CLI. Use HITL package installation only for HITL workflows.

If the user starts from a wheel/source install instead of a repo checkout, keep the same dependency order: compatible Python, compatible `habitat-sim`/`magnum`, core `habitat-lab`, then optional packages.

## Python And Habitat-Sim Compatibility

Use these rules when diagnosing version choices:

- Prefer Python 3.9 when users need a reliable public install path for Habitat-Lab `0.3.x` with `habitat-sim` conda packages.
- Python classifiers in package metadata may include newer Python versions, but successful core install is not enough if `habitat_sim` or `magnum` cannot import.
- A Python 3.11 environment can fail at `import habitat` with missing `magnum`/`habitat_sim` even when `habitat-lab` itself installs, because the simulator package may not be available for that Python/build combination.
- If `ModuleNotFoundError: magnum` or `ModuleNotFoundError: habitat_sim` appears, solve the simulator install first; do not debug Hydra or task code until these imports succeed.
- Install Bullet support (`withbullet`) when rearrangement, physics, or robot manipulation workflows are in scope.

A minimal import sanity check:

```bash
python - <<'PY'
import habitat
import habitat_sim
import magnum
print("habitat", getattr(habitat, "__version__", "unknown"))
print("habitat_sim import ok")
print("magnum import ok")
PY
```

For baselines:

```bash
python - <<'PY'
import habitat_baselines
from habitat_baselines.config.default import get_config
cfg = get_config("pointnav/ppo_pointnav_example.yaml")
print(cfg.habitat_baselines.trainer_name)
PY
```

## Core Dependencies

The core package requires standard Python scientific/config dependencies including Gym `>=0.22,<0.23.1`, NumPy, OpenCV, Hydra Core, OmegaConf, Numba, SciPy, tqdm, and media helpers. A visible Gym deprecation warning does not necessarily mean Habitat-Lab setup failed; see troubleshooting for interpretation.

Habitat-Sim brings native rendering/physics dependencies and is usually the source of graphics, EGL, Magnum, Bullet, and driver compatibility issues.

## Data Directory Layout

Habitat-Lab configs commonly assume a `data/` directory relative to the process working directory. Users may create a real directory or a symlink. The important point is that composed config paths must resolve from where commands are launched.

Common scene dataset layouts:

- Habitat test scenes: `data/scene_datasets/habitat-test-scenes/{scene}.glb`
- ReplicaCAD: `data/scene_datasets/replica_cad/configs/scenes/{scene}.scene_instance.json`
- HM3D: `data/scene_datasets/hm3d/{split}/{scene-directory}/{scene}.basis.glb`
- Gibson: `data/scene_datasets/gibson/{scene}.glb`
- MatterPort3D: `data/scene_datasets/mp3d/{scene}/{scene}.glb`
- HSSD-Habitat: `data/scene_datasets/hssd-hab/scenes/{scene}.scene_instance.json`
- AI2-THOR-Habitat: `data/scene_datasets/ai2thor-hab/ai2thor-hab/configs/scenes/{dataset}/{scene}.scene_instance.json`

Common task dataset layouts:

- PointNav Habitat test dataset: `data/datasets/pointnav/habitat-test-scenes/v1/{split}/{split}.json.gz`
- PointNav Gibson: `data/datasets/pointnav/gibson/v1/{split}/{split}.json.gz`
- PointNav MP3D: `data/datasets/pointnav/mp3d/v1/{split}/{split}.json.gz`
- ObjectNav MP3D: `data/datasets/objectnav/mp3d/v1/{split}/{split}.json.gz`
- ObjectNav HM3D: `data/datasets/objectnav/hm3d/v1/{split}/{split}.json.gz` or versioned variants.
- Rearrangement ReplicaCAD: `data/datasets/rearrange_pick/replica_cad/v0/` and related rearrangement dataset roots.
- VLN R2R MP3D: `data/datasets/vln/mp3d/r2r/v1`

Use config keys rather than memory when checking a specific workflow. Compose the config, then inspect `habitat.dataset.data_path`, `habitat.dataset.scenes_dir`, `habitat.simulator.scene`, and robot/physics asset keys.

## Test Asset Downloads

For a small smoke setup, the public docs use Habitat-Sim's dataset downloader:

```bash
python -m habitat_sim.utils.datasets_download --uids habitat_test_scenes --data-path data/
python -m habitat_sim.utils.datasets_download --uids habitat_test_pointnav_dataset --data-path data/
```

These provide lightweight scene and PointNav episode assets suitable for import/config/Env smoke tests. They do not provide semantic annotations.

## Validating Paths Without Running Simulation

Use config composition before launching runtime:

```bash
python path/to/skills/habitat-lab/sub-skills/setup-and-configuration/scripts/config_probe.py \
  --kind habitat \
  --config benchmark/nav/pointnav/pointnav_habitat_test.yaml \
  --check-paths
```

If paths are missing, decide whether the config expects a different working directory, a symlinked `data/` root, downloaded test assets, or a different dataset config group. Avoid launching `Env` or baselines training until path checks are resolved.

## Install Decision Guide

- Config-only inspection: install `habitat-lab` and a compatible `habitat-sim` so imports succeed; no datasets required unless using `--check-paths`.
- Environment stepping: install `habitat-lab`, `habitat-sim`, and the scene/task assets required by the selected config.
- Rearrangement or robot manipulation: ensure `habitat-sim` was installed with Bullet support and robot/articulated-object assets exist.
- Baselines train/eval: install `habitat-baselines`, compatible PyTorch, and datasets/assets required by the baseline config; route execution details to `../baselines-training-and-evaluation/SKILL.md`.
- HITL apps: install HITL extras and graphics/client dependencies; route launch details to `../hitl-apps-and-interaction/SKILL.md`.
- Custom extensions: install enough dependencies to import and test the registered component; route registry/code authoring to `../extension-patterns/SKILL.md`.

## Data Path Checklist

Before runtime, confirm:

- The command is launched from a directory where relative `data/...` paths resolve, or config overrides point to the correct absolute/user-specific locations.
- `habitat.dataset.data_path` exists after replacing `{split}` with `habitat.dataset.split` when applicable.
- `habitat.dataset.scenes_dir` exists and contains the scene dataset referenced by episodes.
- `habitat.simulator.scene` exists when it names a concrete `.glb`, `.basis.glb`, or `.scene_instance.json` file.
- Robot URDFs and physics config files exist for rearrangement configs.
- Large datasets such as HM3D, MP3D, Gibson, or HSSD are only required for configs that name them; use Habitat test scenes for lightweight smoke tests.
