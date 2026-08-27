---
name: asap
description: "Use ASAP to train humanoid policies, retarget SMPL motions, and
  run sim2sim or sim2real deployment workflows for humanoidverse-based robots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ASAP

Use this skill for the ASAP humanoid learning stack: training and evaluating policies in HumanoidVerse, retargeting SMPL/AMASS motion into robot motion files, and running sim2sim or sim2real deployment helpers.

## Install and Import Check

Start with the bundled doctor script from the generated ASAP skill root, then add the backend-specific pieces you need.

```bash
python scripts/asap_doctor.py --help
python scripts/asap_doctor.py --repo-root <asap-checkout> --section core
```

For the common Python stack, install the editable packages plus the repo-local utilities you need:

```bash
pip install -e .
pip install -e isaac_utils
# optional for deployment helpers
pip install -e sim2real
```

Use a CUDA-capable PyTorch build for the training routes and the policy runtime routes that expect GPU acceleration. Install simulator- or hardware-specific SDKs separately when the doctor script reports them missing.

Read [`references/install-and-backends.md`](references/install-and-backends.md) before choosing a simulator backend or attempting motion retargeting or robot deployment.

## Route by Task

- **Train, evaluate, or export humanoid policies**: use [`sub-skills/training-and-evaluation/SKILL.md`](sub-skills/training-and-evaluation/SKILL.md) for motion-tracking, locomotion, delta-action, checkpoint, and Hydra-config workflows.
- **Retarget SMPL or AMASS motion**: use [`sub-skills/motion-retargeting/SKILL.md`](sub-skills/motion-retargeting/SKILL.md) for shape fitting, motion fitting, asset validation, and MuJoCo visualization.
- **Run sim2sim or sim2real deployment**: use [`sub-skills/sim2real-deployment/SKILL.md`](sub-skills/sim2real-deployment/SKILL.md) for MuJoCo playback, ROS2/Unitree bridges, policy toggles, joystick control, and data logging.

## Common Starting Points

- If you just need a fast dependency or backend check, run [`scripts/asap_doctor.py`](scripts/asap_doctor.py) first.
- If a task fails with a Hydra or import-path error, read [`references/troubleshooting.md`](references/troubleshooting.md) before editing commands.
- If a task needs the current repository baseline, read [`references/repo-provenance.md`](references/repo-provenance.md) to compare the checkout against the generated skill snapshot.
- If you are unsure which config group to override, read [`references/configuration-map.md`](references/configuration-map.md) and then route to the relevant sub-skill.

## Shared References

- [`references/configuration-map.md`](references/configuration-map.md) — Hydra groups, common overrides, and output-directory conventions.
- [`references/install-and-backends.md`](references/install-and-backends.md) — base package install, simulator backends, and external SDK prerequisites.
- [`references/troubleshooting.md`](references/troubleshooting.md) — import, backend, config, and runtime failure patterns.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source commit and evidence baseline for refresh decisions.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured router placement metadata for import into repo-skills-router.

## Boundaries

This is a runtime skill for the ASAP package, not a maintainer release guide. It does not cover unrelated repo maintenance, packaging policy, or non-ASAP robot stacks.

If a task is only about generic PyTorch, general RL theory, or a different simulator stack, route it elsewhere instead of forcing it through ASAP-specific guidance.
