---
name: nle_action_space
description: Validate NLE full or reduced action-space choices and invalid-action penalties.
---

# Nle Action Space

Use this skill when reconstructing or validating mechanisms from the NetHack Learning Environment paper without reading the original repository during recovery. It is appropriate for reduced or full recovery harnesses that need a stable contract for the paper's symbolic RL interface. Do not use it to claim full NLE training success unless the real package, benchmark, and training runtime are available and separately validated.

## Inputs

- Paper-derived NLE observations, actions, rewards, or feature dictionaries depending on the module.
- A recovery harness path that records source provenance and whether the run is proxy or full.

## Outputs

- Deterministic JSON-serializable records or numeric traces suitable for `recovery/recovery_result.json`.
- Errors for missing mandatory fields instead of silent fallback behavior.

## Workflow

1. Load the paper-derived input fixture or live environment output.
2. Apply the module script in `scripts/` to normalize, validate, score, or update state.
3. Save outputs under the current attempt's `recovery/logs/` directory.
4. Cross-check the output against downstream modules rather than duplicating their logic in the recovery harness.
5. Record reduced/proxy status whenever the real NLE package and distributed training loop are unavailable.

## Validation

Run `python /share/project/yuyang/workspace/Paper2Skills/Paper2Skills-Agent/src/packages/paper2skills-agent/src/paper2skills/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations

This skill preserves the mechanism contract from the paper but does not include the original NetHack source code. Full-score reproduction still requires the real NLE package, large-scale RL training, and held-out seed evaluation.
