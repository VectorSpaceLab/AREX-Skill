# Motion retargeting troubleshooting

Fix failures in this order: dependency/import blockers, missing data assets, robot XML/config mismatches, joblib key/shape mismatches, then viewer/display issues. Running the bundled checker first often identifies the cheapest fix.

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --check-raw
```

## Import and dependency failures

### `ModuleNotFoundError: No module named 'smpl_sim'`

Where it appears:

- `scripts/data_process/fit_smpl_shape.py`
- `scripts/data_process/fit_smpl_motion.py`

Why it happens:

- ASAP's `setup.py` lists common dependencies such as `hydra-core`, `joblib`, `lxml`, `numpy-stl`, and `open3d`, but the retargeting scripts import `smpl_sim` from an external SMPL simulation stack.

Recovery:

1. Install the external `smpl_sim` package in the same Python environment used to run ASAP retargeting.
2. Re-run a minimal import check:

   ```bash
   python - <<'PY'
   import smpl_sim
   from smpl_sim.smpllib.smpl_parser import SMPL_Parser
   from smpl_sim.smpllib.smpl_joint_names import SMPL_BONE_ORDER_NAMES
   print('smpl_sim OK')
   PY
   ```

3. If the task only needs the provided G1 retargeted motions, skip fitting and use files already under `humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/`.

### `ModuleNotFoundError` for `hydra`, `open3d`, `lxml`, `joblib`, `mujoco`, `isaac_utils`, or `sim2real`

Recovery:

1. Read the root install/backend guidance: [`../../references/install-and-backends.md`](../../references/install-and-backends.md).
2. Install the editable repo packages and dependencies:

   ```bash
   pip install -e .
   pip install -e isaac_utils
   pip install -e sim2real  # only needed for deployment helpers, but harmless for shared checks
   ```

3. Re-run the specific script in the same environment. Do not treat a successful import in one shell as proof that a different shell or job scheduler has the dependency.

## Missing SMPL files

Typical symptoms:

- `FileNotFoundError` from `SMPL_Parser(model_path="humanoidverse/data/smpl", gender="neutral")`.
- Shape fitting starts but fails before optimization.

Expected files:

```text
humanoidverse/data/smpl/SMPL_FEMALE.pkl
humanoidverse/data/smpl/SMPL_MALE.pkl
humanoidverse/data/smpl/SMPL_NEUTRAL.pkl
```

Recovery:

1. Download SMPL v1.1.0 pkl assets from the SMPL provider using appropriate credentials/license.
2. Unzip under `humanoidverse/data/smpl/`.
3. Rename/copy:

   ```text
   models/basicmodel_f_lbs_10_207_0_v1.1.0.pkl       -> SMPL_FEMALE.pkl
   models/basicmodel_m_lbs_10_207_0_v1.1.0.pkl       -> SMPL_MALE.pkl
   models/basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl -> SMPL_NEUTRAL.pkl
   ```

4. Check before retrying:

   ```bash
   python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
     --repo-root <asap-checkout> \
     --robot g1/g1_29dof_anneal_23dof \
     --require-smpl
   ```

## Missing or misplaced AMASS/raw motion files

Typical symptoms:

- `fit_smpl_motion.py` exits without dumping anything.
- Progress shows zero motions.
- No files appear under `humanoidverse/data/motions/<humanoid_type>/TairanTestbed/singles/`.

Cause:

- The README describes AMASS extraction under `humanoidverse/data/motions/AMASS/AMASS_Complete/`, but `fit_smpl_motion.py` hardcodes `./humanoidverse/data/motions/raw_tairantestbed_smpl/*.npz`.

Recovery:

1. Place or symlink selected AMASS/SMPL `.npz` files under:

   ```text
   humanoidverse/data/motions/raw_tairantestbed_smpl/
   ```

2. Ensure each `.npz` has `mocap_framerate`, `trans`, `poses`, `betas`, and `gender`.
3. Avoid `mocap_framerate < 30`; the script computes `skip = int(fps // 30)`, and values below 30 produce an invalid zero slice step.
4. Check raw files:

   ```bash
   python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
     --repo-root <asap-checkout> \
     --robot g1/g1_29dof_anneal_23dof \
     --check-raw \
     --require-raw
   ```

## Missing shape file during motion fitting

Typical symptom:

```text
FileNotFoundError: humanoidverse/data/shape/<humanoid_type>/shape_optimized_v1.pkl
```

Cause:

- `fit_smpl_motion.py` loads the shape output before optimizing any motion.

Recovery:

1. Run shape fitting first:

   ```bash
   python scripts/data_process/fit_smpl_shape.py +robot=g1/g1_29dof_anneal_23dof
   ```

2. Confirm the output:

   ```bash
   python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
     --repo-root <asap-checkout> \
     --robot g1/g1_29dof_anneal_23dof \
     --require-shape
   ```

3. Only then run:

   ```bash
   python scripts/data_process/fit_smpl_motion.py +robot=g1/g1_29dof_anneal_23dof
   ```

## Robot XML, URDF, mesh, and config mismatches

Typical symptoms:

- `ValueError: MJCF parsed incorrectly please verify it.`
- `AssertionError: No motors found in the mjcf file`
- XML parse errors from `lxml` or `xml.etree.ElementTree`.
- Open3D warnings/errors while loading meshes.
- Optimizer errors because a `joint_matches` robot name is not in `body_names_augment`.

Recovery:

1. Confirm `robot.motion.asset.assetRoot` and `assetFileName` in the Hydra config point to an existing XML.
2. Confirm the XML has a `<worldbody>` with at least one body and an `<actuator>` with motors.
3. Confirm every XML `<mesh file="...">` exists relative to the XML directory and compiler `meshdir`.
4. Confirm every `extend_config.parent_name` exists in the XML body names.
5. Confirm every robot-side `joint_matches` entry exists in XML body names or `extend_config.joint_name`.
6. Run:

   ```bash
   python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
     --repo-root <asap-checkout> \
     --robot g1/g1_29dof_anneal_23dof
   ```

For a new robot, start by copying the G1 structure and changing one thing at a time: XML path, `humanoid_type`, body names, `extend_config`, then `joint_matches`.

## Motion `.pkl` loads but training or visualization fails

### DOF shape mismatch

Typical symptoms:

- MuJoCo assignment error at `mj_data.qpos[7:] = curr_motion['dof'][curr_time]`.
- Training/motion library tensor shape mismatch.

Cause:

- The motion file's `dof` columns do not match the XML motor count. For checked G1 assets, expected `dof.shape[1] == 23`.

Recovery:

1. Validate the file:

   ```bash
   python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
     --repo-root <asap-checkout> \
     --robot g1/g1_29dof_anneal_23dof \
     --motion-file path/to/motion.pkl \
     --require-motion
   ```

2. If the file came from another robot XML, regenerate it with the target robot config.
3. If the XML changed after fitting, refit the motion.

### Joblib `KeyError` in directory mode

Typical symptom:

- A loader computes a file stem and then fails on `joblib.load(path)[key]`.

Cause:

- `MotionLibBase` directory mode expects each single-motion `.pkl` to contain a top-level key equal to that file's stem.

Recovery:

1. Keep the structure emitted by `fit_smpl_motion.py`: file `<motion-key>.pkl` contains `{"<motion-key>": data}`.
2. If you renamed files, rename the top-level key too, or use a single file path rather than a directory as `motion_file`.
3. Use the checker with `--require-key-matches-file` for directory-mode compatibility.

### Missing per-motion keys

Required keys are `root_trans_offset`, `pose_aa`, `dof`, `root_rot`, and `fps`; `smpl_joints` is optional but useful for debugging. See [`data-formats.md`](data-formats.md).

## MuJoCo visualization failures

### `No motion file provided` followed by another exception

Cause:

- `vis_q_mj.py` logs an error when `cfg.visualize_motion_file is None`, but then continues and references `visualize_motion_file`.

Recovery:

Always pass a motion file:

```bash
python scripts/vis/vis_q_mj.py \
  +robot=g1/g1_29dof_anneal_23dof \
  +visualize_motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl"
```

### Viewer does not open or fails on a headless machine

Cause:

- `mujoco.viewer.launch_passive` needs a GUI/display-capable environment.

Recovery:

1. First validate the file structurally with `validate_motion_assets.py`.
2. Run visualization on a machine/session with a display.
3. If using remote Linux, ensure the OpenGL/display configuration is valid for MuJoCo viewer before debugging the motion file itself.

## Output path surprises

`fit_smpl_motion.py` always writes to:

```text
humanoidverse/data/motions/<cfg.robot.motion.humanoid_type>/TairanTestbed/singles/<motion-key>.pkl
```

It does not write to `robot.motion.motion_file` from the config. That config field is mainly for consumers such as training/evaluation after you choose the generated file or directory.

## When to route elsewhere

- If the motion file is valid and the next failure is about PPO config, reward terms, simulator selection, or checkpoints, use [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md).
- If the failure is about ROS2, Unitree SDK, joystick keys, low-level mode, or live robot safety, use [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md).
