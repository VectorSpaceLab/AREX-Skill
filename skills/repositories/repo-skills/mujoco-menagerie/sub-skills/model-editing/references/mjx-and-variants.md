# MJX and Variant XML Notes

Use this reference when an edit touches a Menagerie variant: `_mjx.xml`, `scene_mjx.xml`, no-hand/with-hands XMLs, alternate actuator XMLs, or keyframe-only includes. For model discovery or deciding whether a model has an MJX file at all, route to `model-catalog`.

## Menagerie variant roles

| Variant pattern | Typical role | Editing caution |
| --- | --- | --- |
| `<model>.xml` | Canonical robot model without extra scene objects. | Keep robot-only content here; put planes, lights, props, and task objects in a scene XML. |
| `scene.xml` | Standalone viewer/load wrapper around the canonical model. | Update includes if the canonical model filename changes; do not tune robot dynamics only in the scene unless it is scene-specific. |
| `<model>_mjx.xml` or `mjx_<part>.xml` | MJX-compatible fork of the robot or part. | Maintain as a separate fork; do not silently replace canonical contacts, tendons, or gains. |
| `scene_mjx.xml` | Scene wrapper that includes the MJX fork. | Keep it paired with the MJX model XML and scene-specific simplifications. |
| `_nohand`, `_with_hands`, `left_`, `right_`, `biarm` | Structural composition or side variants. | Reconcile names, keyframes, and actuator order after adding/removing bodies. |
| controller/keyframe XML includes | Alternative actuators or saved poses. | Any `nu` or `nq` change must update included `ctrl`/`qpos` vectors. |

## Common MJX edits seen in Menagerie evidence

MJX variants are usually not cosmetic diffs. They often trade detailed canonical modeling for JAX-friendly simulation behavior.

| Edit type | Why it appears | Safe handling |
| --- | --- | --- |
| Manually designed collision geoms or contact pairs | MJX and learning workflows often prefer fewer, simpler contacts. | Keep visual geoms separate from collision simplifications; document which canonical contacts were removed or approximated. |
| Sphere-only or sphere-heavy collision approximations | Some MJX workflows avoid unsupported or slow non-sphere collision geoms. | Place spheres at physically important locations such as joints, torso, feet, or gripper pads; do not delete canonical collision geometry outside the MJX fork. |
| Solver/iteration/line-search changes | MJX scenes may need lower-cost solver settings. | Keep solver changes in the MJX scene/model and record why they differ from the canonical XML. |
| Lower `kp`/`kv`, changed `dampratio`, or removed `frictionloss` | High gains or some damping/friction details can destabilize accelerated rollouts. | Use conservative gains in MJX variants; the bundled gain helper can produce a starting point, but stability testing belongs to loading/validation workflows. |
| Tendon/gripper simplification | Tendons or equality-coupled grippers may be replaced by direct position actuators for compatibility. | Check actuator count and keyframe `ctrl` length after simplification. |
| Extra keyframes | MJX examples often add `home`, crouched, or task-specific poses. | Keep keyframe vectors aligned with the variant's own `nq`/`nu`, not the canonical model. |

## MJX edit plan

When asked to create or revise an MJX variant:

1. Confirm the base canonical XML and intended MJX output filenames. Use a new `_mjx` or `scene_mjx` path unless the user explicitly approves updating an existing variant.
2. Decide whether the variant is a forked model XML, a scene wrapper, or both.
3. List unsupported or expensive canonical features to simplify: detailed collision meshes, high actuator gains, friction loss, tendons, equality constraints, or dense contact pairs.
4. Preserve the canonical XML unchanged; copy only the assets/includes the MJX variant still needs.
5. Tune solver and actuator settings in the variant, not in the base XML.
6. Update variant keyframes after all body/joint/actuator changes.
7. Hand off compile/smoke validation to `model-loading`; hand off formatting and final PR-style checks to `contribution-maintenance`.

## Variant synchronization checklist

Use this whenever the base model or a composition changes:

- [ ] Does the scene include the correct canonical or MJX model file?
- [ ] Did a renamed body, joint, actuator, site, mesh, or material break references in variants?
- [ ] Did a removed hand/gripper also remove its equality constraints, tendons, sensors, actuators, and keyframe entries?
- [ ] Did a with-hands or bi-arm variant introduce unique prefixes and non-overlapping contacts?
- [ ] Does an MJX fork still include only geoms/contact patterns that the intended MJX workflow supports?
- [ ] Do all keyframe `qpos` and `ctrl` values match the variant's compiled dimensions?
- [ ] Are actuator gains intentionally different from the canonical XML, and are those differences documented?

## Useful local commands

Commands should target the user's checkout or exported model copy; they do not require Menagerie source helper scripts.

```bash
# Inspect how the base and variant differ before editing further.
diff -u /path/to/base_model.xml /path/to/variant_model.xml | less

# Derive candidate gains for a variant using an explicit natural frequency.
python scripts/compute_pd_gains.py /path/to/variant_model.xml --frequency-hz 2.0 --damping-ratio 1.0

# Derive gains from force limits after choosing a variant home pose.
python scripts/compute_pd_gains.py /path/to/variant_model.xml --keyframe home --saturation-angle-deg 5
```

If these commands surface asset-path, compile, or runtime errors, stop editing and route the concrete failure to `model-loading` or `contribution-maintenance` rather than expanding this sub-skill into final CI orchestration.
