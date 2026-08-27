---
name: repo-maintenance
description: "Maintain CleanRL-style code, docs, tests, metadata, and
  contribution workflows without breaking single-file algorithm conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CleanRL Repo Maintenance

Use this sub-skill when a task asks you to edit CleanRL itself: algorithm scripts, utility code, contribution workflow, package metadata, requirements snapshots, documentation, tests, benchmark/RLOps notes, or CI-like local checks.

Do not use this sub-skill for ordinary user training, evaluation, checkpoint loading, or experiment interpretation unless the user is changing repository code or docs as part of that task.

## Maintenance Routing

1. Classify the change before editing:
   - Documentation-only: docs pages, README tables, mkdocs navigation, examples, spelling.
   - Non-performance code: refactors, style fixes, CLI help wording, logging text, low-risk utilities.
   - Performance-impacting code: algorithm math, wrappers, rewards, termination/truncation handling, seeding, hyperparameters, environment preprocessing, optimizer updates, replay buffers, batch sizing.
   - Packaging/dependency: `pyproject.toml`, `uv.lock`, `requirements/`, optional extras, pre-commit hooks.
   - Cloud/benchmark: `cloud/`, benchmark utilities, AWS, W&B, Slurm, regression reports.
2. Preserve CleanRL's single-file implementation philosophy. Keep each algorithm variant readable as a standalone script, even when this duplicates code across variants. Do not introduce shared abstractions just to reduce duplication if they hide algorithm details.
3. Keep the neighboring surfaces in sync. A script change can require its algorithm docs page, focused smoke test, README algorithm matrix, optional extra requirements, and help output checks.
4. Use the bundled selector before running checks:

   ```bash
   python sub-skills/repo-maintenance/scripts/select_native_checks.py cleanrl/sac_continuous_action.py --keywords cli docs
   ```

   The selector prints recommended checks and warnings only; it never runs pytest, mkdocs, cloud jobs, or benchmarks.
5. Prefer focused local checks first, then broader checks only when needed. Treat optional backend tests, cloud tests, W&B tracking, Slurm, and long benchmarks as opt-in actions requiring the right dependencies, credentials, hardware, and user approval.
6. For performance-impacting changes, do not claim correctness from smoke tests alone. Plan an RLOps benchmark/regression workflow and docs update after benchmarks are approved and complete.

## Reference Order

- Read `references/contributor-workflows.md` for editing conventions, RLOps expectations, package metadata, and requirements upkeep.
- Read `references/testing-and-docs.md` for focused pytest/docs/help check selection.
- Read `references/troubleshooting.md` when environment, optional backend, tyro, docs, requirements, benchmark, or cloud failures appear.
- Use `scripts/select_native_checks.py` to turn touched files and keywords into a check shortlist.

## High-Value Review Questions

- Does the edit keep the modified algorithm script understandable without chasing shared modules?
- Did every changed CLI flag or default reach both help output and the relevant docs/test command?
- Are optional extras and generated requirements snapshots still aligned with package metadata?
- Are smoke tests clearly separated from optional backend, cloud, W&B, and benchmark checks?
- If behavior can affect returns or runtime, is an RLOps regression plan documented instead of relying only on short tests?
