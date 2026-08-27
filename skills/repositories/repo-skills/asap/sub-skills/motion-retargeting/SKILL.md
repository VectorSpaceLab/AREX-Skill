---
name: motion-retargeting
description: "Prepare SMPL and AMASS assets, fit ASAP humanoid shapes and
  motions, validate robot motion assets, and visualize retargeted motion in
  MuJoCo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# motion-retargeting

Use this sub-skill when an ASAP task is about turning SMPL or AMASS motion into robot motion `.pkl` files, checking robot XML/motion config assets, fitting a humanoid shape, retargeting motion, or visualizing retargeted motion with MuJoCo.

Run ASAP retargeting entry points from the repository checkout root. Run bundled validation helpers from the generated ASAP skill root with `--repo-root <asap-checkout>`. If the request is about policy training, checkpoint evaluation, or deployment/control rather than motion file preparation, route to the sibling skills instead.

## When to use this sub-skill

- Prepare SMPL model files under `humanoidverse/data/smpl/`.
- Prepare AMASS-style `.npz` motion files for the ASAP retargeting scripts.
- Check `robot.motion` config fields, MuJoCo XML, URDF, and mesh layout for a robot such as `g1/g1_29dof_anneal_23dof`.
- Run `fit_smpl_shape.py` to create `humanoidverse/data/shape/<humanoid_type>/shape_optimized_v1.pkl`.
- Run `fit_smpl_motion.py` to create per-motion joblib files under `humanoidverse/data/motions/<humanoid_type>/TairanTestbed/singles/`.
- Run `vis_q_mj.py` with `+visualize_motion_file=...` to inspect the retargeted motion in MuJoCo.

## Do not use this sub-skill for

- PPO, motion-tracking, locomotion, or delta-action policy training. Use [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md).
- ROS2, Unitree SDK, joystick, ONNX policy runtime, or live robot deployment. Use [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md).
- Generic SMPL or AMASS conversion outside the ASAP/HumanoidVerse file layout unless the user explicitly wants to adapt files into ASAP's expected layout.

## Required reading order

1. Read the root ASAP router and install guidance first: [`../../SKILL.md`](../../SKILL.md) and [`../../references/install-and-backends.md`](../../references/install-and-backends.md).
2. Read [`references/workflows.md`](references/workflows.md) for the five-step retargeting flow and exact commands.
3. Read [`references/data-formats.md`](references/data-formats.md) before changing file names, joblib keys, or robot config values.
4. Run the bundled safe checker before expensive fitting:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --check-raw
```

5. If an error occurs, read [`references/troubleshooting.md`](references/troubleshooting.md), then the root troubleshooting page [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for shared install, Hydra, and backend issues.

## Fast command map

Preflight current G1 assets and a known retargeted motion file:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --motion-file humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl \
  --check-raw
```

Fit robot shape after SMPL files are present:

```bash
python scripts/data_process/fit_smpl_shape.py +robot=g1/g1_29dof_anneal_23dof
```

Fit motions after the shape file and raw `.npz` motion files are present:

```bash
python scripts/data_process/fit_smpl_motion.py +robot=g1/g1_29dof_anneal_23dof
```

Visualize one retargeted output:

```bash
python scripts/vis/vis_q_mj.py \
  +robot=g1/g1_29dof_anneal_23dof \
  +visualize_motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl"
```

## Dependency and asset gates

- The fitting scripts require the normal ASAP Python dependencies plus external `smpl_sim`. ASAP's package metadata includes `hydra-core`, `lxml`, `joblib`, `numpy-stl`, `open3d`, and other scientific dependencies, but `smpl_sim` is a separate required dependency for shape and motion fitting.
- `fit_smpl_shape.py` and `fit_smpl_motion.py` import `smpl_sim.smpllib.smpl_parser`, `smpl_sim.smpllib.smpl_joint_names`, and, for motion fitting, `smpl_sim.utils.smoothing_utils`.
- The bundled checker intentionally avoids importing ASAP or `smpl_sim`; it validates file layout and joblib structure without running optimization.

## Expected outputs

- Shape fit output: `humanoidverse/data/shape/g1_29dof_anneal_23dof/shape_optimized_v1.pkl`.
- Retargeted single-motion outputs: `humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/<motion-key>.pkl`.
- A retargeted `.pkl` is a joblib-loaded dictionary. For directory-mode consumers, each file's top-level key should match the file stem. See [`references/data-formats.md`](references/data-formats.md).

## Cross-links

- Root ASAP skill: [`../../SKILL.md`](../../SKILL.md).
- Root install and backend notes: [`../../references/install-and-backends.md`](../../references/install-and-backends.md).
- Root troubleshooting: [`../../references/troubleshooting.md`](../../references/troubleshooting.md).
- Training and evaluation: [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md) for consuming generated motion files in policy training.
- Sim2real deployment: [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md) for MuJoCo/ROS2/Unitree runtime control after a policy exists.
