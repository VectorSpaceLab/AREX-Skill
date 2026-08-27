---
name: robocasa
description: "Guides Researchers through RoboCasa365 embodied-AI simulation,
  kitchen task and scene selection, demonstration datasets, teleoperation, and
  safe validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RoboCasa

Use this skill for RoboCasa/RoboCasa365 simulation, kitchen manipulation tasks,
scene and asset configuration, demonstration datasets, policy-evaluation setup,
or interactive collection. It covers the public `robocasa` package and its
robosuite/MuJoCo integration; it does not replace a policy-learning framework.

## Fast route

1. **Check package readiness first.** RoboCasa 1.0.1 asserts MuJoCo `3.3.1`,
   NumPy `2.2.5`, and robosuite `>=1.5.2`. Install the package's declared
   dependencies and public robosuite separately, then run the diagnostic in
   [simulation-environments](sub-skills/simulation-environments/SKILL.md).
2. **Separate data gates.** A successful import or environment constructor does
   not prove that the external kitchen fixture/object/texture archives or
   datasets exist. Validate those paths before `reset`, playback, rendering,
   or collection; do not download multi-GB data implicitly.
3. **Choose the route below.** Read only the focused sub-skill and its linked
   references before producing commands or code.

## Install and import gate

Use an isolated Python 3.11 environment when possible. Install a compatible
public robosuite release before RoboCasa, then install RoboCasa from its source
or release tree:

```bash
python -m pip install "robosuite>=1.5.2"
python -m pip install -e .
python -c 'import robocasa, robosuite, mujoco, numpy; print(robocasa.__version__, robosuite.__version__, mujoco.__version__, numpy.__version__)'
```

Keep the exact package pins together. If import fails, fix version conflicts
before investigating assets. Optional MimicGen, GR00T, SpaceMouse, display, and
asset-authoring tools are not part of the minimal import gate.

## Choose a sub-skill

- [simulation-environments](sub-skills/simulation-environments/SKILL.md) —
  install/import checks, `gym.make`, `create_env`, controller and camera
  choices, split mapping, reset/step data, seeds, rendering, and bounded
  rollouts.
- [tasks-scenes-assets](sub-skills/tasks-scenes-assets/SKILL.md) — atomic and
  composite task selection, kitchen layouts/styles, fixture and object
  registries, placement configuration, custom tasks, and asset prerequisites.
- [datasets-demonstrations](sub-skills/datasets-demonstrations/SKILL.md) —
  dataset registry metadata and soups, pretrain/target sources, LeRobot and
  HDF5 structure, inspection, playback, conversion, and download planning.
- [teleoperation-and-collection](sub-skills/teleoperation-and-collection/SKILL.md)
  — keyboard/SpaceMouse setup, interactive viewer constraints, demonstration
  collection, HDF5 handoff, and interruption recovery.

## Cross-route rules

- Route `split`, `layout_ids`, `style_ids`, object registries, and fixture/XML
  failures to the task/scene route; route reset/step and action-shape failures
  to the simulation route.
- Route registry paths, LeRobot/HDF5 schemas, and playback flags to the dataset
  route; route live input and HDF5 recording to teleoperation/collection.
- Keep rollouts, downloads, playback, and collection bounded and explicit.
  Always close environments and preserve a writable output directory.
- Do not tell a future agent to open the original checkout. All reusable
  diagnostics and recipes are bundled under this skill.

Read [troubleshooting](references/troubleshooting.md) for cross-cutting install,
data, rendering, and optional-dependency failures. Read
[repository provenance](references/repo-provenance.md) before deciding whether
this graph is current for a repository checkout or should be refreshed.
