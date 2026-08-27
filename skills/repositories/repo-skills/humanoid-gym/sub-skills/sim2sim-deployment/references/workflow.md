# Workflow

This sub-skill deploys an exported TorchScript policy into the MuJoCo sim-to-sim loop used for XBot-L.
It is intentionally split into a safe validation step and a launch step.

## 1) Validate assets and optional policy

Run the bundled validator before launching the viewer:

```bash
python scripts/validate_sim2sim_assets.py --repo-root <repo-root> [--policy <policy.pt>]
```

What it checks:
- `humanoid/scripts/sim2sim.py` exists and still exposes the terrain choice.
- `humanoid/envs/custom/humanoid_config.py` can be read for the current observation contract.
- `resources/robots/XBot/mjcf/XBot-L.xml` exists.
- `resources/robots/XBot/mjcf/XBot-L-terrain.xml` exists.
- `resources/robots/XBot/urdf/XBot-L.urdf` exists.
- `resources/robots/XBot/terrain/uneven.png` exists.
- All mesh and heightfield files referenced by the MJCF and URDF files exist.
- If `--policy` is provided, the policy loads as TorchScript on CPU and accepts the expected zero tensor.

The validator does not launch MuJoCo, does not open a viewer, and does not run a 60s rollout.

## 2) Choose plane vs terrain

- Plane mode: use `resources/robots/XBot/mjcf/XBot-L.xml`.
- Terrain mode: use `resources/robots/XBot/mjcf/XBot-L-terrain.xml` and the bundled `terrain/uneven.png` heightfield.

Use terrain only when you want the uneven-ground deployment path. For a quick sanity check, plane mode is the lighter choice.

## 3) Build the launch command

Use the command builder to avoid hand-typing the MuJoCo entry point:

```bash
python scripts/build_sim2sim_command.py --policy <policy.pt> [--terrain]
```

The printed command uses the repository's sim2sim entry point and only adds `--terrain` when requested.
If you pass a relative policy path, launch from the same working directory or use an absolute policy path.

## 4) Launch the rendered rollout

Run the printed command in a graphical session:

```bash
python -m humanoid.scripts.sim2sim --load_model <policy.pt>
python -m humanoid.scripts.sim2sim --load_model <policy.pt> --terrain
```

Important notes:
- The source sim2sim loop uses `mujoco_viewer.MujocoViewer`.
- There is no built-in `--headless` flag in the source script.
- On a headless server, you must provide a working X11/EGL/OSMesa/display path before launch.
- The source loop runs for about 60 seconds, so do not use it as a validator.

## Fast decision rules

- If the policy file is missing, hand off to `training-and-evaluation` to export one first.
- If the policy loads but the input width is 47 instead of 705, the export does not match this sub-skill's contract.
- If the model output is not 12-D, the policy or robot contract has changed and belongs in `environment-customization`.
- If the viewer fails, treat it as a runtime/display problem, not as a policy-shape problem.
