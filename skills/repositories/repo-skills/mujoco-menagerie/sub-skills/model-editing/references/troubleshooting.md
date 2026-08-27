# Model Editing Troubleshooting

Use this reference for editing-specific failures. For generic MuJoCo compile, viewer, asset-path, or short-step issues, route to `model-loading`. For formatter, license, changelog, gallery, pytest, or CI-equivalent failures, route to `contribution-maintenance`.

## Attachment and keyframes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No attachment_site` or gripper attaches to the wrong frame | The arm XML lacks a site named `attachment_site`, or the site is on an intermediate body. | Add/verify a terminal-link site with explicit `pos`/`quat`; re-export to a new XML; then attach through that site. |
| XML compiles before attach but keyframe load fails after attach | `qpos`/`ctrl` vectors were not expanded to the combined model dimensions. | Compile the hand alone to get `hand_model.nq` and `hand_model.nu`; append hand keyframe values or zeros in the same attach order. Repeat for every preserved keyframe. |
| Attached hand controls move the wrong actuator | Actuator order changed but controller/keyframe assumptions were reused. | Print or inspect actuator names after composition; regenerate `ctrl` vectors by actuator name/order rather than copying old numeric arrays blindly. |
| Gripper equality or tendon constraint references missing names | Composition renamed or prefixed bodies/joints/actuators but not constraints. | Delete source-local constraints before duplication, then re-add them with the final prefixed names. |

## MjSpec composition

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Duplicate body/joint/actuator names | Multiple attached specs were inserted without unique prefixes. | Use `prefix="left/"`, `prefix="right/"`, or another controlled prefix for every attached copy. |
| Generated XML loses a detail from the source | MjSpec serialization is not byte-preserving and can drop or normalize some fields. | Diff the source and output; intentionally reapply important defaults, mesh metadata, compiler options, or post-processing before validation. |
| Bi-arm output overwrote the single-arm source | Generator wrote to a hard-coded output path. | Treat source scripts as patterns only. Use explicit output paths and write to a new file until the diff is reviewed. |
| Contact behavior changes unexpectedly | Source excludes were not restored, or cross-arm contacts were accidentally excluded. | Re-add model-local excludes with prefixes; create cross-arm excludes only when physically justified. |

## Mirrored hands and side variants

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Mirrored mesh appears inside-out or collides oddly | Vertices were reflected but face winding was not reversed. | Reverse face index order during mesh export and regenerate collision assets in a separate mirrored asset directory. |
| Mesh files cannot be found after mirroring | XML `meshdir` or mesh `file` attributes still point at the original side. | Repoint `meshdir` before serialization and rename only the intended side-specific file prefixes. |
| Right hand joints move opposite of expected command sign | Joint axis/range convention was geometrically mirrored but the controller expects an encoder-coordinate relabel. | Decide whether to mirror motion or preserve command sign. For command-sign preservation, mirror geometry and adjust axis/range consistently rather than only renaming identifiers. |
| Some geoms/sites mirror but inherited defaults do not | Pose data in default classes was missed. | Mirror default-class geom, joint, and site poses as well as concrete body-tree elements. |
| Text replacement changed unrelated names | Global `left`/`right` substitution was too broad. | Restrict identifier rewrites to controlled tokens such as `left_` or a known namespace prefix after structural transformation. |

## PD gain helper

Run the helper help from the sub-skill directory, or use an absolute script path from any working directory:

```bash
python scripts/compute_pd_gains.py --help
```

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `no eligible joint-backed actuators` | The XML uses tendon/site/general actuators, has no actuators, or regex filters excluded every actuator. | Use the helper only for single-DoF joint-backed position actuators. For tendon/site/general actuators, compute gains manually from the mechanism model. |
| `missing force limit` | Neither actuator `forcerange` nor joint `actuatorfrcrange` is present, or the selected `--force-limit-source` is wrong. | Try `--force-limit-source auto`, add/confirm force limits in the XML, or use `--frequency-hz` to bypass saturation-derived frequencies. |
| Very high `kp`/`kv` values | Effective inertia is large, saturation error is too small, or the chosen keyframe is far from the intended operating pose. | Re-run with `--keyframe home`, increase `--saturation-angle-deg` or `--saturation`, reduce `--frequency-hz`, or lower gains for MJX variants. |
| Slide/prismatic gains look nonsensical | The default saturation angle was interpreted as a generic coordinate error. | Pass `--saturation <meters-or-native-coordinate-error>` for prismatic joints. |
| Helper compiles one XML but not another | Includes/assets or MuJoCo version requirements differ between variants. | Route the concrete compile error to `model-loading`; do not edit gains until the XML compiles. |

## MJX variants

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| MJX variant is unstable while canonical model is stable | Canonical gains, friction, contacts, tendons, or solver settings were copied directly. | Keep a separate MJX fork; simplify contacts, lower gains, and tune solver settings in the variant only. |
| MJX fork no longer matches base robot topology | Base model was edited but the variant was not synchronized. | Diff base vs variant; update renamed joints/sites/actuators and keyframes intentionally. |
| Variant keyframes fail after removing a hand or tendon | `nq`/`nu` changed but variant keyframe includes remained canonical. | Regenerate or remove stale keyframe XMLs; ensure variant `qpos`/`ctrl` lengths match its compiled dimensions. |
| User asks whether a model has MJX support | Catalog-selection question, not editing. | Route to `model-catalog` before planning MJX edits. |

## When to stop editing and hand off

Stop expanding the edit plan and hand off when:

- the model no longer compiles or has an asset-path error;
- a formatter/check/lint/test command is needed to declare readiness;
- the user needs a model inventory or wants to choose between multiple Menagerie directories;
- MJX behavior requires runtime stepping or benchmark validation beyond a static XML plan.
