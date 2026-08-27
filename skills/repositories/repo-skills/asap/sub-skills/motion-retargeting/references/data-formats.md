# Motion retargeting data formats

This reference explains the file layouts consumed and emitted by ASAP's motion retargeting scripts. Use it before renaming paths, editing robot configs, merging joblib files, or passing generated files to training and visualization.

## Repository-relative layout

```text
humanoidverse/
├── config/robot/g1/g1_29dof_anneal_23dof.yaml
└── data/
    ├── robots/g1/
    │   ├── g1_29dof_anneal_23dof_fitmotionONLY.xml
    │   ├── g1_29dof_anneal_23dof.urdf
    │   └── meshes/*.STL
    ├── smpl/
    │   ├── SMPL_FEMALE.pkl
    │   ├── SMPL_MALE.pkl
    │   └── SMPL_NEUTRAL.pkl
    ├── motions/raw_tairantestbed_smpl/*.npz
    ├── shape/g1_29dof_anneal_23dof/shape_optimized_v1.pkl
    └── motions/g1_29dof_anneal_23dof/TairanTestbed/singles/*.pkl
```

The G1 files above are examples. For another humanoid, keep the same relationship among `robot.motion.humanoid_type`, the shape directory, and the generated motion directory.

## SMPL model files

`fit_smpl_shape.py` and `fit_smpl_motion.py` instantiate:

```python
SMPL_Parser(model_path="humanoidverse/data/smpl", gender="neutral")
```

Minimum practical files:

| File | Purpose |
|---|---|
| `humanoidverse/data/smpl/SMPL_NEUTRAL.pkl` | Required by the neutral parser used in ASAP's scripts. |
| `humanoidverse/data/smpl/SMPL_MALE.pkl` | Not used by the current neutral fitting path, but expected by common SMPL distributions/tools. |
| `humanoidverse/data/smpl/SMPL_FEMALE.pkl` | Not used by the current neutral fitting path, but expected by common SMPL distributions/tools. |

The `smpl_sim` package is also required; the `.pkl` model files alone are not enough.

## Raw AMASS/SMPL `.npz` files

The README describes AMASS download/extraction under `humanoidverse/data/motions/AMASS/AMASS_Complete/`, but the current motion fitting script reads only:

```python
all_pkls = glob.glob("./humanoidverse/data/motions/raw_tairantestbed_smpl/*.npz", recursive=True)
```

Required keys in each `.npz` file:

| Key | Expected shape/type | How ASAP uses it |
|---|---:|---|
| `mocap_framerate` | scalar number | Used to choose `skip = int(fps // 30)` before downsampling. Values below 30 make `skip` zero and will break slicing. |
| `trans` | `(T, 3)` | Root translation trajectory. |
| `poses` | `(T, >=66)`; sample files have `(T, 72)` | First 66 axis-angle pose values are kept, then six zeros are appended to produce a 72-vector. |
| `betas` | usually `(16,)` in AMASS exports | Loaded into the intermediate dictionary; the current retargeting script fits with the separate optimized shape instead of directly optimizing per-file betas. |
| `gender` | scalar string/bytes | Loaded for completeness; the current parser path uses neutral SMPL. |

The loader returns `None` and skips the file if `mocap_framerate` is missing.

Sample checked raw file:

```text
humanoidverse/data/motions/raw_tairantestbed_smpl/video_side_jump_level4_filter_amass.npz
keys: betas, gender, mocap_framerate, poses, trans
poses shape: (101, 72)
trans shape: (101, 3)
gender: neutral
```

## Robot motion config fields

The shape, motion, and visualization scripts all resolve the Hydra robot config with an override such as:

```bash
+robot=g1/g1_29dof_anneal_23dof
```

The important fields are under `robot.motion` in `humanoidverse/config/robot/g1/g1_29dof_anneal_23dof.yaml`:

| Field | Example | Why it matters |
|---|---|---|
| `motion_file` | `humanoidverse/data/motions/g1_29dof_anneal_23dof/v1/amass_all.pkl` | Default motion source for training/evaluation consumers; not the hardcoded raw `.npz` glob in `fit_smpl_motion.py`. |
| `asset.assetRoot` | `humanoidverse/data/robots/g1/` | Base directory for MuJoCo XML, URDF, and meshes. |
| `asset.assetFileName` | `g1_29dof_anneal_23dof_fitmotionONLY.xml` | XML loaded by `Humanoid_Batch` and `vis_q_mj.py`. |
| `asset.urdfFileName` | `g1_29dof_anneal_23dof.urdf` | Companion URDF for robot assets. |
| `humanoid_type` | `g1_29dof_anneal_23dof` | Names shape and output motion directories. |
| `extend_config` | virtual `left_hand_link`, `right_hand_link`, `head_link` | Adds target bodies that do not have physical motors but are used for fitting/tracking. |
| `joint_matches` | `[robot_body_or_extend_joint, SMPL_joint]` pairs | Defines correspondence for shape and motion fitting losses. |
| `smpl_pose_modifier` | Pelvis/shoulder/elbow Euler offsets | Creates the default standing SMPL pose before fitting. |

## Robot XML, URDF, and mesh expectations

`Humanoid_Batch` reads the XML with `lxml`, expects a valid `<worldbody>`, expects at least one actuator motor, parses body names recursively, and loads meshes with Open3D.

For the checked G1 fit-motion XML:

| Asset | Observed fact |
|---|---|
| XML | `humanoidverse/data/robots/g1/g1_29dof_anneal_23dof_fitmotionONLY.xml` |
| XML model | `g1_29dof_anneal_23dof` |
| Bodies | 24 body names, beginning with `pelvis` |
| Joints | 24 joints including the floating base |
| Motors | 23 motors |
| Mesh refs | 28 mesh files under compiler `meshdir="meshes"` |

The generated motion `dof` array must have one column per motor. For the checked G1 files, that means `dof.shape[1] == 23`.

## Shape output file

`fit_smpl_shape.py` writes:

```text
humanoidverse/data/shape/<humanoid_type>/shape_optimized_v1.pkl
```

For G1:

```text
humanoidverse/data/shape/g1_29dof_anneal_23dof/shape_optimized_v1.pkl
```

The file is a joblib dump of a tuple:

```python
(shape_new.detach(), scale)
```

Expected content:

| Tuple item | Expected value |
|---|---|
| `shape_new` | Torch tensor with shape compatible with `(1, 10)` SMPL betas. |
| `scale` | Torch scalar/one-element tensor used to align SMPL joint distances to robot keypoints. |

`fit_smpl_motion.py` loads this exact path with:

```python
shape_new, scale = joblib.load(f"humanoidverse/data/shape/{cfg.robot.motion.humanoid_type}/shape_optimized_v1.pkl")
```

## Retargeted motion `.pkl` files

`fit_smpl_motion.py` writes one joblib file per raw `.npz` input:

```text
humanoidverse/data/motions/<humanoid_type>/TairanTestbed/singles/<motion-key>.pkl
```

The top-level object is a dictionary:

```python
{
    "<motion-key>": {
        "root_trans_offset": ...,
        "pose_aa": ...,
        "dof": ...,
        "root_rot": ...,
        "smpl_joints": ...,
        "fps": 30,
    }
}
```

Required per-motion keys for ASAP's current consumers:

| Key | Expected shape/type | Used by |
|---|---:|---|
| `root_trans_offset` | `(T, 3)` | `vis_q_mj.py` and `MotionLibBase.load_motion_with_skeleton`. |
| `pose_aa` | `(T, num_robot_bodies + num_extend_bodies, 3)`; checked G1 sample is `(101, 27, 3)` | Forward kinematics and training motion library. |
| `dof` | `(T, num_motors)`; checked G1 sample is `(101, 23)` | MuJoCo visualization (`mj_data.qpos[7:]`) and motion library `dof_pos`. |
| `root_rot` | `(T, 4)` SciPy quaternion order `[x, y, z, w]` | `vis_q_mj.py` reorders to MuJoCo `[w, x, y, z]`. |
| `smpl_joints` | `(T, 24, 3)` | Optional visual/debug reference; `vis_q_mj.py` checks for the key. |
| `fps` | integer; current script writes `30` | Motion timestep. |
| `action` | optional `(T, action_dim)` | Needed only by delta-action training routes, not emitted by this retargeting script. |

Sample checked retargeted file:

```text
humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_side_jump_level4_filter_amass.pkl
root_trans_offset: (101, 3), float32
pose_aa: (101, 27, 3), float32
dof: (101, 23), float32
root_rot: (101, 4), float64
smpl_joints: (101, 24, 3), float32
fps: 30
```

## Joblib key expectations

Two common loaders have different key sensitivities:

- `vis_q_mj.py` loads a motion file and iterates `list(motion_data.keys())`; the top-level key can be any readable motion key as long as the per-motion value has the required arrays.
- `MotionLibBase` directory mode loads file paths, computes `key = <file-stem>`, and then indexes `joblib.load(path)[key]`. For directory-mode training/evaluation, each single-motion `.pkl` file must have a top-level key exactly equal to its file stem.

`fit_smpl_motion.py` satisfies directory-mode key matching because it writes `<motion-key>.pkl` and stores `{<motion-key>: data_dump}`. If you merge or rename files manually, preserve this rule or use a single file path rather than directory mode.

## Visualization assumptions

`vis_q_mj.py` expects:

- `+visualize_motion_file=...` to be provided. If it is omitted, the script logs an error but still refers to `visualize_motion_file`, which can cause a runtime failure.
- The XML from `cfg.robot.motion.asset.assetRoot / assetFileName` to be valid for `mujoco.MjModel.from_xml_path(...)`.
- `dof.shape[1]` to match `mj_model.nq - 7` for a floating-base humanoid.
- `root_rot` to be `[x, y, z, w]`; the script reorders with `[[3, 0, 1, 2]]` before assigning MuJoCo `qpos[3:7]`.
- A GUI/display-capable environment for `mujoco.viewer.launch_passive`. Use the checker when only headless structural validation is possible.
