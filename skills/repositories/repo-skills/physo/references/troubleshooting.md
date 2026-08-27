# Cross-Cutting Troubleshooting

## Import or package check fails

Symptoms:

- `ModuleNotFoundError: No module named 'physo'`
- The doctor script aborts before printing the summary.
- Root exports such as `SR`, `ClassSR`, `read_pareto_csv`, `read_pareto_pkl`, or `load_expr` are missing.

Checks:

```bash
python scripts/physo_skill_doctor.py
python -m pip check
```

Fixes:

- Install the `physo` package in the active environment.
- Make sure the same interpreter is used for both the doctor script and the user workflow.
- Re-run the doctor script before deeper debugging so you know the baseline package is usable.

## Optional display warnings

PhySO may warn when system LaTeX or optional display helpers are missing.
Treat those warnings as non-blocking unless you specifically need pretty LaTeX, tree images, or notebook-style rendering.

## CPU vs CUDA expectations

The verified baseline for this skill is CPU-only. Do not infer CUDA or parallel-mode coverage from the doctor script or smoke helpers. If a user asks about GPU execution, treat it as unverified unless a separate backend-specific verification has been performed.

## Workflow-specific failures

- Single-dataset shape, units, weights, wrapper, preset, or result-loading issues -> [`sub-skills/sr/SKILL.md`](../sub-skills/sr/SKILL.md)
- Multi-dataset or class/spe constant shape issues -> [`sub-skills/class-sr/SKILL.md`](../sub-skills/class-sr/SKILL.md)
- Encode/decode, library, program, sampling, constant-fit, or reload issues -> [`sub-skills/toolkit/SKILL.md`](../sub-skills/toolkit/SKILL.md)
- Benchmark selector, sample-generation, or symbolic-equivalence issues -> [`sub-skills/benchmarks/SKILL.md`](../sub-skills/benchmarks/SKILL.md)

## Common recovery steps

- Normalize array shapes before changing algorithms.
- Use the relevant sub-skill smoke helper to check a tiny valid case.
- If a failure is still unclear after route-specific guidance, inspect `references/repo-provenance.md` to make sure the skill matches the checkout.
