---
name: physo
description: "Use PhySO for symbolic regression, class symbolic regression,
  toolkit-level expression workflows, and benchmark problem loaders."
read_when: "Use when the user names `physo`, `PhySO`, symbolic regression,
  ClassSR, toolkit expression helpers, or benchmark problem loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PhySO

Use this skill when working with the `physo` package, the scientific Python symbolic-regression library.

## Install and Import Check

Run [`scripts/physo_skill_doctor.py`](scripts/physo_skill_doctor.py) to confirm the installed package, key public exports, and the CPU scientific stack used by the verified baseline. The checked baseline was PhySO 1.2.0 on CPU; this skill does not claim CUDA verification. Import-time LaTeX warnings are expected when optional display tools are missing.

## Route by Task

- One dataset with `X`, `y`, units, `y_weights`, `candidate_wrapper`, run presets, logging, or Pareto inspection: use [`sub-skills/sr/SKILL.md`](sub-skills/sr/SKILL.md).
- Multiple realizations with shared class constants or realization-specific constants: use [`sub-skills/class-sr/SKILL.md`](sub-skills/class-sr/SKILL.md).
- Prefix expressions, libraries, tokens, `Program`/`VectPrograms`, random sampling, constant optimization, display, or result reloads: use [`sub-skills/toolkit/SKILL.md`](sub-skills/toolkit/SKILL.md).
- Feynman/Class benchmark problems, sample generation, metadata, or symbolic equivalence checks: use [`sub-skills/benchmarks/SKILL.md`](sub-skills/benchmarks/SKILL.md).

## Shared References

- [`references/install-and-smoke.md`](references/install-and-smoke.md): install/import check and smoke commands.
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting import, display, backend, and routing failures.
- [`references/repo-provenance.md`](references/repo-provenance.md): source version, dirty-state snapshot, and evidence paths.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): router placement metadata for compatible agents.

## Common Starting Points

- Start with the doctor script when the environment or package import is uncertain.
- Route to a sub-skill before drafting commands or code for a user workflow.
- Use the sub-skill smoke scripts for route-specific tiny checks after the environment is known to be usable.
- If the user asks for benchmark reproduction, training-scale sweeps, or maintainer jobfiles, stop at the boundary and keep this runtime skill focused on day-to-day package workflows.

## Boundaries

This skill is self-contained. It does not depend on opening the source checkout at runtime, and it does not cover repo maintenance, release automation, or long benchmark campaigns.
