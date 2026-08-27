---
name: model-editing
description: "Guide safe Menagerie MJCF editing, attachment composition,
  actuator gains, mirrored hands, bi-arm specs, and MJX-aware variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Editing

Use this sub-skill when the task is about changing or generating Menagerie-style MJCF/XML content: attachment sites, arm/hand composition, actuator/keyframe variants, PD gains, mirrored hands, bi-arm assemblies, or MJX-specific model forks.

## Route boundaries

- Stay here for edit plans, local XML transformation patterns, actuator/keyframe updates, and the bundled read-only gain helper.
- Route model choice, model-directory anatomy, scene-vs-model XML selection, and MJX availability questions to `model-catalog`.
- Route direct `mujoco` loading, viewer use, compile/step debugging, and asset-path smoke tests to `model-loading`.
- Route final formatting, changelog/license updates, gallery changes, and CI/check orchestration to `contribution-maintenance`.
- Do not require future agents to run Menagerie source helper scripts from a checkout. Use the distilled workflows and bundled script in this sub-skill instead.

## Inputs to collect before editing

1. Base XML path(s), whether they are canonical model XMLs, scene XMLs, or variants.
2. Requested output path and overwrite policy; default to a new file or copy, not in-place source mutation.
3. Composition intent: attach end-effector, duplicate an arm, mirror a hand, add/remove a controller, or create an MJX fork.
4. Keyframe policy: preserve all keyframes, expand only `home`, create a new keyframe, or remove stale keyframes.
5. Validation budget and handoff target for loading/CI checks.

## Read first

- [Model editing workflows](references/model-editing.md) for attachment sites, MjSpec composition, mirrored/bi-arm generation patterns, actuator variants, PD gain formulas, and the editing checklist.
- [MJX and variants](references/mjx-and-variants.md) for `_mjx.xml`, `scene_mjx.xml`, no-hand/with-hand/controller variants, and common MJX caveats.
- [Troubleshooting](references/troubleshooting.md) for missing attachment sites, keyframe length mismatches, invalid joint references, mirrored mesh winding, gain-helper failures, and MJX incompatibilities.

## Bundled helper

Use [scripts/compute_pd_gains.py](scripts/compute_pd_gains.py) when the task asks for Menagerie-style position actuator `kp`/`kv` estimates from effective joint inertia:

```bash
python scripts/compute_pd_gains.py /path/to/model.xml --saturation-angle-deg 10 --damping-ratio 1.0
python scripts/compute_pd_gains.py /path/to/model.xml --keyframe home --frequency-hz 2.0 --damping-ratio 0.9
```

The helper is read-only. It accepts arbitrary MJCF XML paths, can use actuator or joint force limits, and prints candidate gains without modifying the XML.

## Validation signals before handoff

- Every generated or edited XML is written to an explicit output path and the original source XML remains available for comparison.
- Attachment and MjSpec composition plans include keyframe `qpos`/`ctrl` expansion or a decision to remove/regenerate stale keyframes.
- Mirroring plans cover mesh vertex reflection, face-winding reversal, pose/default mirroring, identifier renaming, and at least one geometric sanity check.
- MJX edits are kept in separate variant XMLs and do not silently replace canonical Menagerie models.
- After the edit plan or local modification is complete, hand off compile/smoke testing to `model-loading` and final contribution checks to `contribution-maintenance`.
