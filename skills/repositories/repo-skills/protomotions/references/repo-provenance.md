# ProtoMotions repo provenance

This generated operating skill was distilled from a local ProtoMotions checkout. It intentionally avoids absolute checkout paths and private environment details.

## Source snapshot

- Repository name: ProtoMotions
- Distribution name: `protomotions`
- Package version from `pyproject.toml`: `3.1.0`
- Current branch: `main`
- Current commit: `a6df301d312dc58ac40a4d994f4f1064728d854c`
- Exact tag at HEAD: none detected
- Remote URL: omitted-private-or-unknown
- Working tree state during distillation: dirty because generated production artifacts were created under `skills/`; no source-code edits were required for the skill.

## Evidence paths used

- `pyproject.toml`, `MANIFEST.in`, `requirements_isaacgym.txt`, `requirements_isaaclab.txt`, `requirements_newton.txt`, `requirements_genesis.txt`, `requirements_mujoco.txt`
- `README.md`
- `docs/source/getting_started/installation.rst`, `quickstart.rst`, `pretrained_models.rst`, and data-preparation guides
- `docs/source/user_guide/configuration.rst`, `experiments.rst`, `gpc.rst`, `slurm_training.rst`
- `docs/source/tutorials/code_tutorials.rst` and workflow guides for AMASS SMPL, custom robots, domain randomization, G1 deployment, and PyRoki retargeting
- `protomotions/cli.py`, `train_agent.py`, `inference_agent.py`, `assets.py`
- `protomotions/agents/`, `components/`, `envs/`, `robot_configs/`, `simulator/`, and `utils/` source trees
- `deployment/` helper modules and ONNX/MuJoCo deployment scripts
- `data/scripts/`, `scripts/`, and `pyroki/` conversion/retargeting helpers
- `examples/experiments/`, `examples/tutorial/`, visualizer scripts, and benchmark scripts as workflow evidence
- `protomotions/tests/` for parser, packaging, config, simulator seam, deployment-input, and unit-helper evidence
- `data/pretrained_models/**/MODEL_CARD.md` and experiment configs for model-artifact roles
- `legal/` notices for asset/license caveats

## Environment-verification baseline

A private inspection environment verified the selected CPU/package scope for skill drafting:

- Python 3.11 Conda prefix
- Editable `protomotions==3.1.0`
- CPU `torch==2.5.1+cpu`
- `pytest`, `onnxruntime`, MuJoCo import dependency, and base package dependencies
- Passed: `pip check`, distribution metadata, package import, robot and simulator factories, MotionLib config construction, `protomotions --help`, `protomotions train-agent --help`, `protomotions inference-agent --help`, and `protomotions info --json`

Optional full runtime backends were not installed into this minimum inspection prefix because ProtoMotions documents mutually distinct stacks for IsaacGym, IsaacLab/IsaacSim, Newton, Genesis, MuJoCo, and PyRoki. The generated skill documents those choices and keeps optional backend verification explicit.

Private command evidence was stored in the creation artifacts and is not required for runtime use of this skill.

## Refresh signals

Refresh this skill if any of these change:

- `pyproject.toml` entry points, optional dependencies, extras, or dependency conflicts.
- Backend install docs or supported simulator versions.
- CLI arguments in `protomotions/cli.py`, `train_agent.py`, or `inference_agent.py`.
- Public experiment file structure, resolved-config semantics, GPC/PEFT checkpoint contracts, or domain-randomization behavior.
- MotionLib schema, conversion scripts, PyRoki retargeting sequence, contact-label handling, or FPS conventions.
- ONNX export metadata, deployment tracker input semantics, MuJoCo standalone contract, or custom robot/MJCF/USD behavior.
