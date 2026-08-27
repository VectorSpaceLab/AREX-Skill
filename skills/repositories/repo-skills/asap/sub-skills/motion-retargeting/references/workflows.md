# Motion retargeting workflows

Run all commands from the ASAP repo root. These workflows prepare data for later training or visualization; they do not train policies and do not run sim2real control.

## Five-step ASAP retargeting flow

### 1. Prepare SMPL shape assets

`fit_smpl_shape.py` constructs an `SMPL_Parser(model_path="humanoidverse/data/smpl", gender="neutral")`, so the SMPL directory must exist before shape fitting.

Expected layout after downloading and unpacking SMPL v1.1.0 pkl assets:

```text
humanoidverse/data/smpl/
├── SMPL_FEMALE.pkl
├── SMPL_MALE.pkl
└── SMPL_NEUTRAL.pkl
```

The README also describes the unpacked source archive layout:

```text
humanoidverse/data/smpl/
├── SMPL_python_v.1.1.0/
├── models/
│   ├── basicmodel_f_lbs_10_207_0_v1.1.0.pkl
│   ├── basicmodel_m_lbs_10_207_0_v1.1.0.pkl
│   └── basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl
└── smpl_webuser/
```

Rename/copy the three model files to the `SMPL_FEMALE.pkl`, `SMPL_MALE.pkl`, and `SMPL_NEUTRAL.pkl` names above. The fitting code uses the neutral model directly, but keeping all three names makes later SMPL tooling less fragile.

Preflight only the SMPL and robot assets:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --require-smpl
```

### 2. Prepare AMASS/SMPL motion `.npz` files

The README tells users to download AMASS with `SMPL + H G format` under `humanoidverse/data/motions/AMASS/AMASS_Complete/` and unpack archives such as `ACCAD.tar.bz2`, `CMU.tar.bz2`, and `Transitions.tar.bz2`:

```bash
cd humanoidverse/data/motions/AMASS/AMASS_Complete
for file in *.tar.bz2; do
    tar -xvjf "$file"
done
```

The current `fit_smpl_motion.py` implementation does **not** recursively scan `AMASS_Complete`; it hardcodes this input glob:

```text
./humanoidverse/data/motions/raw_tairantestbed_smpl/*.npz
```

For the unmodified script, place or symlink the selected AMASS/SMPL `.npz` files there. Each `.npz` must contain `mocap_framerate`, `trans`, `poses`, `betas`, and `gender`.

Check a few raw files before launching the optimizer:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --check-raw \
  --require-raw
```

### 3. Prepare robot XML and motion config

For G1, the relevant config and assets are:

```text
humanoidverse/config/robot/g1/g1_29dof_anneal_23dof.yaml
humanoidverse/data/robots/g1/g1_29dof_anneal_23dof_fitmotionONLY.xml
humanoidverse/data/robots/g1/g1_29dof_anneal_23dof.urdf
humanoidverse/data/robots/g1/meshes/*.STL
```

The shape and motion scripts instantiate `Humanoid_Batch(cfg.robot.motion)`. The important `robot.motion` fields are:

```yaml
motion:
  motion_file: humanoidverse/data/motions/g1_29dof_anneal_23dof/v1/amass_all.pkl
  asset:
    assetRoot: humanoidverse/data/robots/g1/
    assetFileName: g1_29dof_anneal_23dof_fitmotionONLY.xml
    urdfFileName: g1_29dof_anneal_23dof.urdf
  humanoid_type: g1_29dof_anneal_23dof
  extend_config:
    - joint_name: left_hand_link
      parent_name: left_elbow_link
      pos: [0.25, 0.0, 0.0]
      rot: [1.0, 0.0, 0.0, 0.0]
  joint_matches:
    - [pelvis, Pelvis]
    - [left_hip_pitch_link, L_Hip]
```

Rules that matter in practice:

- `assetRoot` and `assetFileName` must point to a MuJoCo XML with `<worldbody>`, `<actuator>`, motors, non-free joints, and mesh references.
- XML mesh paths are resolved relative to the XML directory plus `<compiler meshdir="...">` when present. For G1, `meshdir="meshes"` means mesh files live in `humanoidverse/data/robots/g1/meshes/`.
- `joint_matches` robot-side names must exist either in XML body names or in `extend_config.joint_name` entries. SMPL-side names must be valid `SMPL_BONE_ORDER_NAMES` values at runtime.
- `extend_config.parent_name` must be an XML body name because `Humanoid_Batch` appends virtual bodies to the parsed skeleton.
- The number of motion `dof` columns must match the number of MuJoCo motors. The G1 fit-motion XML has 23 motors, matching the sample retargeted files' `dof` shape `(T, 23)`.

Validate XML, URDF, meshes, and config references:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof
```

### 4. Fit humanoid-to-SMPL shape

Run shape fitting after SMPL assets and the robot XML/config are ready:

```bash
python scripts/data_process/fit_smpl_shape.py +robot=g1/g1_29dof_anneal_23dof
```

Optional shape visualization:

```bash
python scripts/data_process/fit_smpl_shape.py +robot=g1/g1_29dof_anneal_23dof +vis=True
```

Expected output:

```text
humanoidverse/data/shape/g1_29dof_anneal_23dof/shape_optimized_v1.pkl
```

That file is a joblib dump of `(shape_new.detach(), scale)`, where `shape_new` is a 10-parameter SMPL beta tensor and `scale` is a scalar tensor learned to align the selected SMPL joints with robot keypoints.

Validate the output before motion fitting:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --require-shape
```

### 5. Retarget motion and visualize in MuJoCo

Run motion fitting after the shape file and raw `.npz` files are ready:

```bash
python scripts/data_process/fit_smpl_motion.py +robot=g1/g1_29dof_anneal_23dof
```

The current script processes every `.npz` under `humanoidverse/data/motions/raw_tairantestbed_smpl/` one at a time. For each valid input, it writes a single-motion joblib file:

```text
humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/<motion-key>.pkl
```

Example output path from the README and checked sample data:

```text
humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl
```

Validate the generated motion file structure before training or visualization:

```bash
python sub-skills/motion-retargeting/scripts/validate_motion_assets.py \
  --repo-root <asap-checkout> \
  --robot g1/g1_29dof_anneal_23dof \
  --motion-file humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl \
  --require-motion
```

Visualize with MuJoCo:

```bash
python scripts/vis/vis_q_mj.py \
  +robot=g1/g1_29dof_anneal_23dof \
  +visualize_motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl"
```

Viewer controls from the source script:

- `Space`: pause/unpause.
- `R`: reset time to the first frame.
- `N`: switch to the next motion key in a multi-motion joblib file.

## After retargeting

- For policy training with the generated motion file, route to [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md).
- Delta-action policy training needs a motion file with an extra per-frame `action` key. The retargeting script described here emits geometry/kinematics keys but does not synthesize `action`.
- For MuJoCo sim2sim or robot runtime control after a policy exists, route to [`../sim2real-deployment/SKILL.md`](../sim2real-deployment/SKILL.md).
