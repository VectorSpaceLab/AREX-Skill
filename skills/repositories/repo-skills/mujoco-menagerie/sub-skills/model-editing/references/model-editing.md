# Menagerie Model Editing Workflows

This reference distills Menagerie editing evidence into reusable, checkout-independent operating guidance. It covers safe XML edits, attachment-site composition, actuator/keyframe updates, PD gains, MjSpec composition, mirrored hands, and bi-arm variants. It does not replace final formatting, loading, or CI checks; route those to the sibling maintenance/loading skills after the edit is planned or written.

## Core safety rules

1. **Never overwrite the only copy of a source XML.** Write generated compositions to a new XML path first, then diff and validate.
2. **Keep model XML and scene XML roles separate.** Menagerie model XMLs describe the robot; `scene*.xml` wrappers add planes, lights, cameras, props, or tables.
3. **Preserve relative asset layout.** Moving XML without the matching `assets/`, `meshdir`, or `<include>` paths commonly breaks compilation.
4. **Keep variant intent explicit.** `_mjx`, `_nohand`, `_with_hands`, controller, and keyframe variants should be separate named files rather than silent in-place changes.
5. **Update keyframes whenever `nq` or `nu` changes.** A valid composition can still fail or initialize incorrectly if `qpos` and `ctrl` vectors are stale.
6. **Treat MjSpec round-trips as semantic, not byte-preserving.** Inspect the serialized XML for dropped or reordered attributes and reapply important metadata intentionally.

## Attachment sites and arm/hand composition

Menagerie arm models commonly expose a site named `attachment_site` on the terminal link. Use that site as the rigid attach anchor for a gripper or hand. If the arm lacks such a site, add one deliberately to the end-effector body with an explicit `pos`/`quat`; do not guess from visual mesh names alone.

Safe PyMJCF pattern:

```python
from dm_control import mjcf
import numpy as np

arm = mjcf.from_path("arm.xml")
hand = mjcf.from_path("hand.xml")
hand_physics = mjcf.Physics.from_mjcf_model(hand)

site = arm.find("site", "attachment_site")
if site is None:
  raise ValueError("arm model has no site named attachment_site")

arm_home = arm.find("key", "home")
if arm_home is not None:
  hand_home = hand.find("key", "home")
  if hand_home is None:
    arm_home.qpos = np.concatenate([arm_home.qpos, np.zeros(hand_physics.model.nq)])
    arm_home.ctrl = np.concatenate([arm_home.ctrl, np.zeros(hand_physics.model.nu)])
  else:
    arm_home.qpos = np.concatenate([arm_home.qpos, hand_home.qpos])
    arm_home.ctrl = np.concatenate([arm_home.ctrl, hand_home.ctrl])

site.attach(hand)
```

Keyframe notes:

- Expand every keyframe you intend to preserve, not only `home`, when the downstream task needs multiple named poses.
- If a hand has no keyframe, append zeros of length `hand_model.nq` and `hand_model.nu` in the same attach order used by the composition API.
- If a hand has fewer controls than joints because it uses tendons/equality coupling, append `hand_model.nu`, not the number of joints.
- If a scene includes a keyframe via `<include file="keyframe_ctrl.xml"/>`, update the included keyframe file or create a parallel variant rather than leaving the include stale.

## Actuator and controller variants

Menagerie models use several actuator styles:

- Position actuators with `kp`/`kv`, `dampratio`, `inheritrange`, `forcerange`, or joint-level `actuatorfrcrange`.
- Equality-coupled grippers where one finger or tendon drives another.
- Motor or general actuators when a position servo would not match the real mechanism.
- Separate XML variants for alternate controllers or keyframe behavior.

When changing actuators:

1. Identify the joint or tendon each actuator targets and whether the control vector length `nu` changes.
2. Keep actuator names aligned with joint names when the model already follows that convention.
3. Preserve physically meaningful force limits. Menagerie frequently groups joints by motor size or joint class; do not mix gripper-scale limits with arm-scale limits.
4. If you add/remove actuators, update `ctrl` keyframes and any external controller examples that assume control order.
5. Use the bundled gain helper for joint-backed position actuators; use model-specific reasoning for tendon/site/general actuators.

## PD gain computation

The bundled helper [compute_pd_gains.py](../scripts/compute_pd_gains.py) generalizes the Rizon-style gain derivation. It computes the dense joint-space mass matrix at `qpos0` or a named keyframe, takes the diagonal effective inertia for each single-DoF joint-backed actuator, and applies:

```text
kp = M_ii * w_n^2
kv = 2 * damping_ratio * M_ii * w_n
```

By default, the helper derives one natural frequency per force-limit class from a saturation coordinate error:

```text
w_n = sqrt(force_limit / (max_class_M_ii * saturation_error))
```

Commands:

```bash
# Flexiv-style: derive per-class frequencies from a 10 degree error and critical damping.
python scripts/compute_pd_gains.py /path/to/model.xml --saturation-angle-deg 10 --damping-ratio 1.0

# Use a nonzero home keyframe before measuring effective inertia.
python scripts/compute_pd_gains.py /path/to/model.xml --keyframe home --saturation-angle-deg 7.5

# Use actuator-level force limits and disable 0.5 Hz rounding.
python scripts/compute_pd_gains.py /path/to/model.xml --force-limit-source actuator --round-frequency-hz 0

# If force limits are absent or not the desired design driver, use a fixed frequency.
python scripts/compute_pd_gains.py /path/to/model.xml --frequency-hz 2.0 --damping-ratio 0.9
```

Interpretation:

- The table reports candidate `kp`/`kv`; it does not rewrite XML.
- Hinge joints use radians. For prismatic joints or non-angle coordinates, pass `--saturation <coordinate-error>` instead of relying on `--saturation-angle-deg`.
- A large change in effective inertia between `qpos0` and `home` is a signal to choose the configuration that best matches the intended operating pose.
- For MJX variants, lower gains can be intentionally more stable than the canonical XML; keep MJX-specific choices in the MJX variant file.

## MjSpec composition pattern for bi-arm or multi-part models

Use `mujoco.MjSpec` when composition must duplicate a model tree and preserve compiled MJCF semantics. The distilled safe plan from Menagerie bi-arm generation is:

1. Load the single-arm XML into a spec with `mujoco.MjSpec.from_file(...)`.
2. Extract model-local contact excludes and equality constraints that should be re-added with prefixes; delete them before duplicating if they would otherwise refer to stale names.
3. Serialize the cleaned spec to a string and load independent copies for each arm. This prevents shared mutable state.
4. Create a new root `MjSpec` for the combined model. Copy only global visual or option settings that are intentionally shared.
5. Add explicit attach sites to the new root worldbody, for example `left_attach` and `right_attach`, with planned `pos` and `quat` values.
6. Attach each copy with a unique prefix, such as `left/` and `right/`, so body, joint, actuator, and site names do not collide.
7. Re-add contact excludes and equality constraints using the prefixed names. Do not assume equality constraints from the single-arm model remain valid after duplication.
8. Serialize to a new output XML and inspect the result for attributes that MjSpec may drop or normalize during round-trip.

Minimal skeleton:

```python
import mujoco
from pathlib import Path

single = mujoco.MjSpec.from_file("single_arm.xml")
clean_xml = single.to_xml()
left = mujoco.MjSpec.from_string(clean_xml)
right = mujoco.MjSpec.from_string(clean_xml)

combo = mujoco.MjSpec()
left_site = combo.worldbody.add_site(name="left_attach", pos=[-0.41, 0, 0], quat=[1, 0, 0, 0])
right_site = combo.worldbody.add_site(name="right_attach", pos=[0.41, 0, 0], quat=[0, 0, 0, 1])
combo.attach(left, site=left_site, prefix="left/")
combo.attach(right, site=right_site, prefix="right/")

Path("combined_model.xml").write_text(combo.to_xml())
```

Use this skeleton as a plan, not as a drop-in generator. Real Menagerie models may need contact excludes, gripper equalities, mesh defaults, `maxhullvert`, cameras, lights, or keyframes restored explicitly after serialization.

## Mirrored hand or left/right variant workflow

Mirroring is not a text replacement. A safe mirrored hand workflow covers geometry, kinematics, defaults, names, and verification:

1. Mirror every mesh through the chosen plane, for example `M_y = diag(1, -1, 1)` for a Y-plane reflection.
2. Reverse face winding after vertex reflection so normals and collision surfaces remain outward-facing.
3. Write mirrored assets into a dedicated output mesh directory; do not overwrite the original left/right asset directory.
4. Mirror body, geom, site, inertial, and default-class pose data. Normalize quaternions before converting to rotation matrices when source quaternions are not unit length.
5. Decide joint-coordinate convention before changing axes/ranges. Some mirrored hands preserve encoder sign by negating the mirrored axis while keeping the range; others geometrically mirror motion by swapping/negating ranges.
6. Repoint `meshdir` and mesh `file` attributes before serialization so the XML resolves the mirrored asset files.
7. Apply uniform identifier renaming only after the structural transform, and only for controlled prefixes such as `left_` to `right_`.
8. Verify at least one named site or fingertip against the expected mirror transform before accepting the variant.

## URDF/compiler and model-generation notes

Per-model READMEs show that URDF-to-MJCF conversion settings are model-specific. Common compiler choices include `discardvisual="false"` to preserve visual geoms, `strippath="false"` to retain asset paths, `fusestatic="false"` or `true` depending on whether jointless bodies should remain separate, and `balanceinertia` when upstream inertials need repair. Do not copy one model's compiler flags blindly to another.

A safe model-generation plan records:

- source format and conversion command, if any;
- chosen compiler flags and why they preserve the needed geometry/inertia;
- manual default-class extraction and attribute grouping;
- actuator model and force/control limits;
- keyframes added or regenerated;
- scene wrapper content kept outside the robot model XML;
- any MJX or controller-specific fork created as a separate file.

## Editing checklist

Before handing off an edited model:

- [ ] Input XMLs and assets are preserved; generated output uses a new path unless overwrite was explicitly approved.
- [ ] All names introduced by composition are unique or intentionally prefixed.
- [ ] Attachment sites have explicit poses and are on the correct body.
- [ ] `qpos` keyframes match final `nq`; `ctrl` keyframes match final `nu`.
- [ ] Actuator order, control ranges, force limits, and equality/tendon coupling are documented.
- [ ] Mirrored assets use reversed winding and a separate mesh directory.
- [ ] MJX changes live in `_mjx`/`scene_mjx` variants and are explained separately from the canonical model.
- [ ] XML style is Menagerie-like: two-space indentation, double-quoted attributes, default classes before `worldbody`, and a scene XML when the model is standalone.
- [ ] Compile/smoke validation is ready for `model-loading`; formatter/license/test orchestration is ready for `contribution-maintenance`.
