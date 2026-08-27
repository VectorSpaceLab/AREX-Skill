# ASAP install and backend notes

Use this page for shared setup before choosing a training, evaluation, or deployment route.

## Base editable installs

From the ASAP repository checkout root, install the editable packages:

```bash
pip install -e .
pip install -e isaac_utils
# only if you need deployment helpers
pip install -e sim2real
```

The verified checkout exposes these import names from package metadata:

- `asap` → `humanoidverse`
- `isaac_utils` → `isaac_utils`
- `sim2real` → `sim2real`

## Safe dependency checks

These checks do not launch simulators:

```bash
python humanoidverse/train_agent.py --help
python humanoidverse/eval_agent.py --help
python - <<'PY'
import torch, humanoidverse
print('cuda:', torch.cuda.is_available())
print('humanoidverse:', humanoidverse.__file__)
PY
```

For a single-command summary, run the bundled doctor script from the generated ASAP skill root and point `--repo-root` at the checkout you want to inspect:

```bash
python scripts/asap_doctor.py --repo-root <asap-checkout> --section core
```

In the inspection environment used for this skill tree, `torch` was CUDA-capable and `humanoidverse` imported successfully, but backend packages such as `isaacgym`, `omni.isaac.lab`, and `genesis` were not installed in the active shell.

## Backend selection guide

| Backend | When to choose | Required runtime pieces |
| --- | --- | --- |
| `+simulator=isaacgym` | README-aligned high-throughput training and motion-tracking examples. | IsaacGym Preview 4 Python API and CUDA Torch. |
| `+simulator=isaacsim` | IsaacLab/IsaacSim runs. | IsaacSim install plus `omni.isaac.lab`. |
| `+simulator=genesis` | Genesis environment runs. | `genesis-world` plus CUDA Torch when available. |
| `+simulator=mujoco` | Only if the workflow has been adapted and verified for MuJoCo. | `mujoco` Python package. |

Do not change only `sim_type`; the real backend selection comes from the Hydra group `+simulator=<choice>`.

## Shared failure signals

- `ModuleNotFoundError: No module named 'utils.config_utils'` → run from the repository root and use script form, not `python -m humanoidverse.train_agent`.
- `ModuleNotFoundError: No module named 'isaacgym'` → install IsaacGym or switch backend.
- `ModuleNotFoundError: No module named 'omni'` → IsaacSim/IsaacLab is not installed.
- `ModuleNotFoundError: No module named 'genesis'` → Genesis is not installed.
- `ModuleNotFoundError: No module named 'mujoco'` → MuJoCo is not installed.

## Cross-links

- Root router: [`../SKILL.md`](../SKILL.md)
- Training and evaluation: [`../sub-skills/training-and-evaluation/SKILL.md`](../sub-skills/training-and-evaluation/SKILL.md)
- Motion retargeting: [`../sub-skills/motion-retargeting/SKILL.md`](../sub-skills/motion-retargeting/SKILL.md)
- Sim2real deployment: [`../sub-skills/sim2real-deployment/SKILL.md`](../sub-skills/sim2real-deployment/SKILL.md)
