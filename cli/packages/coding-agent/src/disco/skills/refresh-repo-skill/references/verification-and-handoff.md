# Verification And Handoff

## Purpose

Read this after editing. A refresh is not complete until the updated skill has
been checked for stale claims, broken links, unsafe leaks, and usability
regressions.

## Static Verification

Run a static pass over the refreshed skill tree and usability test cases.
DisCo does not require an external verifier for this workflow; perform the
checks directly and save findings when practical.

Write all verification and review artifacts under the configured review/test
artifact directory, defaulting to `<repository-path>/skills/tests/<skill-id>/`.
Use `test-cases/` for concrete usability cases and `reports/` for staleness
audits, self-refine evals, verification reports, human-review notes,
publication checklists, prompt samples, and benchmark notes. Do not write these
inside the runtime skill directory.

Check:

- Root `SKILL.md` exists and frontmatter is valid.
- `references/repo-provenance.md` exists after refresh.
- The root `SKILL.md` links to `references/repo-provenance.md` for freshness
  checks.
- `references/repo-provenance.md` uses schema
  `disco.repo-provenance.v1` and reflects the current repo commit or
  explicit non-Git source identifier, dirty state, package version when
  available, and relative evidence paths.
- Skill IDs are lowercase hyphen IDs and descriptions are double-quoted.
- Root and sub-skill routes still point to existing references, scripts, and
  sub-skills.
- Every new or edited Markdown link resolves.
- Removed files are no longer linked.
- Public install, import, API, CLI, config, and workflow guidance matches
  current repository evidence.
- High-frequency support workflows identified during the refresh, such as data
  preparation, validation, conversion, command generation, data-layout checks,
  optional dependency checks, environment checks, and maintainer guidance, are
  reachable from the root or nearest owning sub-skill.
- Copyable commands and examples that invoke bundled scripts use option names,
  file paths, config keys, and inputs accepted by the current bundled scripts or
  templates.
- Public files do not leak local checkout paths, conda prefixes, Python
  executable paths, `pip show Location` values, credentials, or machine-specific
  details.
- Provenance does not leak local absolute paths, private remote URLs, cache
  paths, credentials, Python executable paths, or environment names.
- Usability test cases under `test-cases/` have copyable prompts and an updated
  `index.md`.
- Optional `reports/self-refine/evals.json` remains valid when present under
  the review/test artifact directory.
- The runtime skill directory contains no Python cache files, `__pycache__/`,
  `*.pyc`, `*.pyo`, build outputs, downloaded caches, or temporary scratch
  files.

Write review artifacts such as
`reports/verification/verification-report.json` and
`reports/final/human-review.md` with PASS/WARN/FAIL findings, evidence, and
accepted risks.

## Current-Repo Verification

For refreshed content, stale-claim checks matter more than style checks. Verify
the highest-risk refreshed facts against current repo evidence:

- Import paths and symbols: safe `python -c` import checks or introspection.
- Function/class signatures: `inspect.signature` or equivalent source checks.
- CLI commands and flags: current `--help` output.
- Config keys and schemas: schema loading or tiny validation checks.
- Script behavior: run skill scripts on tiny safe fixtures where possible.
- Script/documentation consistency: compare each edited script's parser or
  accepted CLI flags against the examples in nearby references.
- Documentation-derived workflows: confirm the referenced current examples or
  tests still exist and match the distilled guidance.

Avoid expensive training, network calls, destructive commands, GPU-only jobs, or
large downloads unless the user explicitly asks and the environment is safe.

## Regression-Sensitive Review

Verify both sides of the refresh:

- Refreshed behavior: at least one usability prompt should require updated
  current repo facts.
- Retained behavior: at least one prompt should still exercise an existing
  supported workflow.
- Removed behavior: no public skill route should still recommend unsupported
  old APIs, flags, configs, or examples.
- Routing: root and sub-skill descriptions should trigger for current user
  wording, not just old terminology.

When practical, run a fresh agent or isolated review against the refreshed skill
with no access to working notes. If isolated runs are unavailable, review from
the perspective of a future agent that can only read the refreshed skill
directory and usability cases.

## Human Review Package

Recommended review artifacts:

- `reports/verification/staleness-audit.md`: claim-by-claim current evidence and decisions.
- `reports/verification/verification-report.json`: machine-readable PASS/WARN/FAIL checks.
- `reports/final/human-review.md`: summary, changed public files, warnings, and reviewer
  questions.
- `reports/final/publication-checklist.md`: final checks before committing or publishing the
  refreshed skill.
- `reports/final/prompt-sampling.md`: usability prompt samples for quick inspection.

Keep these artifacts outside runtime skill docs unless the user wants to publish
them.

## Fix And Repeat

If verification reports critical or high failures:

1. Fix the refreshed skill or tests.
2. Re-run the failed checks.
3. Keep the final review package only after failures are resolved or explicitly
   accepted by the user.

Warnings require judgment. Fix warnings that indicate stale claims, missing
links, shallow current guidance, weak tests, or likely trigger issues.

## Managed Import

After verification passes, keep the runtime tree outside the live DisCo skills
root and follow `verify-repo-skill`'s structured approval policy. For an
approved refresh of the exact managed skill, run:

```bash
node <verify-repo-skill>/scripts/import_repo_skill.mjs \
  --agent-dir <agent-dir> \
  --routing-entry <repo-path>/skills/disco/routing_decision/classification.json \
  --overwrite \
  <verified-runtime-skill-dir>
```

Use `--overwrite` only after approval to replace that exact managed skill. A
normal classified import requires the external routing entry even when the
area-family assignments did not change. The handoff must match the runtime v2
metadata and final skill content digest, provide an existing absolute
`source_checkout`, and use repository-relative evidence paths and valid line
ranges under that checkout. When capability scope and taxonomy are unchanged,
the refresh may retain the existing assignments, but it must refresh or verify
the handoff against the current checkout and final runtime graph. If capability
scope or taxonomy changed, reclassify before import. Do not hand-edit router
Markdown or let the importer infer or backfill routing metadata.
Every retained or changed classified assignment in the handoff must include
`confidence` (`high`, `medium`, or `low`), `rationale`, and repository evidence.
Confidence is a central-index audit field and does not belong in the runtime
v2 metadata fragment.

## Final Handoff

Report:

- Existing skill directory refreshed.
- Previous provenance or fallback baseline used.
- Current repository state recorded in `references/repo-provenance.md`.
- Public skill files changed.
- Stale claims removed or updated.
- New or revised usability test cases.
- Verification status and review package path under `reports/`.
- External routing decision path and whether assignments were retained or
  reclassified.
- Managed import path and status, or a clear statement that the verified
  runtime tree remains staged.
- Remaining unknowns or accepted warnings.

Keep the handoff concise, and clearly distinguish public runtime skill content
from private review artifacts.
