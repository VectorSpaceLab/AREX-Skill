# Verification and Handoff

## Purpose

Read this after editing an existing skill. The update is not complete until automatic verification has run and a human reviewer has a concise package to inspect.

## Static Verification

Run a static verification pass over the edited skill tree and usability test
cases. DisCo does not require an external Python verifier for this
workflow; perform the checks below directly and save the findings when
practical.

The static pass checks:

- Generated skill directory and root `SKILL.md` existence.
- Frontmatter validity, lowercase-hyphen IDs, double-quoted descriptions,
  `disable-model-invocation: true` on repo root/sub-skill files for compatible
  agents, and `repo-skills-router` routing behavior.
- Root routes, sub-skill routes, bundled reference/script links, and relative Markdown links.
- Public install/import guidance.
- Local path, virtualenv, conda, and `pip show Location` leaks.
- Usability test-case directory shape, `index.md`, copyable prompts, README review sections, and minimum case count.
- Optional `reports/self-refine/evals.json` shape when present.
- Review/test artifacts live under the configured review/test artifact
  directory, with concrete cases in `test-cases/` and reports in `reports/`,
  not inside the runtime skill directory.
- Bundled helper examples use the helper's actual parser or command names.
- High-frequency support workflows are discoverable from the root router or the
  nearest owning sub-skill instead of being implied only in prose.
- The runtime skill tree contains no cache or build debris such as
  `__pycache__/`, `*.pyc`, `*.pyo`, or temporary scratch files.

Write the findings into `reports/verification/` or `reports/final/` under the
review/test artifact directory, including failures, warnings, evidence, and
accepted risks.

## Regression-Sensitive Review

For extension work, verification must include both new coverage and regression risk:

- New capability: at least one usability prompt should require the newly added guidance.
- Existing workflow: at least one prompt should still route through a pre-existing capability.
- Links: every new reference/script must be reachable from a nearby `SKILL.md`.
- Runtime local links: every Markdown link to a local reference, script,
  template, or asset must resolve inside the edited skill directory and point to
  an existing bundled file.
- Copyable examples: command snippets in references should match the bundled
  helper's accepted flags, file paths, and failure behavior.
- Privacy: newly inspected environment details must not appear in public skill files.
- Self-containment: new guidance must not rely on original repo paths, and any
  source repo script/example a future agent is told to use must have a bundled
  skill-owned replacement.

When practical, run a fresh agent or isolated review against the updated skill with no access to working notes. If isolated runs are unavailable, review from the perspective of a future agent that can only read the updated skill directory and usability cases.

## Human Review Package

Recommended review artifacts:

- `reports/verification/verification-report.json`: machine-readable PASS/WARN/FAIL checks.
- `reports/final/human-review.md`: summary, failures, warnings, and reviewer questions.
- `reports/final/publication-checklist.md`: pre-publication checklist.
- `reports/final/prompt-sampling.md`: usability prompt samples for quick inspection.

Do not publish the review package as runtime skill documentation by default. It is a quality gate for humans.

## Fix and Repeat

If verification reports critical or high failures:

1. Fix the edited skill or tests.
2. Re-run verification.
3. Keep the final review package only after failures are resolved or explicitly accepted.

Warnings require judgment. Fix warnings that indicate shallow guidance, missing links, weak tests, or likely trigger issues.

## Managed Import

After verification passes, keep the runtime tree outside the live DisCo skills
root and follow `verify-repo-skill`'s structured approval policy. For an approved
new import, run:

```bash
node <verify-repo-skill>/scripts/import_repo_skill.mjs \
  --agent-dir <agent-dir> \
  --routing-entry <repo-path>/skills/disco/routing_decision/classification.json \
  <verified-runtime-skill-dir>
```

For an approved replacement of that exact managed repo skill, add
`--overwrite`. The importer validates the complete runtime tree, installs it
under `<agent-dir>/skills/repositories/repo-skills/<skill-id>/`, rebuilds the sibling live
`repo-skills-router`, and restores both the prior skill and router on failure.
Do not edit the live tree or manually combine copy and updater commands.

The routing entry is mandatory for a normal classified import. It must match
the runtime v2 metadata exactly and include an existing absolute
`source_checkout`; every assignment's repository-relative evidence path and
line range must resolve under that checkout. Keep the full routing decision
outside the runtime skill. If the extension did not change repository
capability scope or taxonomy hash, reuse the previously verified decision only
after confirming that its identity, runtime content digest, and evidence still
match the edited skill. Never let the importer infer or backfill routing.
Every classified assignment in a new or retained handoff must include
assignment-level `confidence` (`high`, `medium`, or `low`) in addition to its
rationale and evidence. This field is written to the central assignment index
only; do not add it to the compact runtime v2 metadata.

After success, the extended skill is available to DisCo Researcher in a new
session without cross-agent export. Use `import-repo-skills-to-agent` only when
the user explicitly asks to export the managed library to another agent.

## Final Handoff

Report:

- Source or external working runtime directory updated.
- Repository evidence used for the extension.
- Changed runtime skill files.
- New or revised usability test cases.
- Verification status and review package path under `reports/`.
- Managed import path and status, including whether overwrite was approved, or a
  clear statement that the verified runtime tree remains staged.
- Confirmation that DisCo Researcher can use a successful managed import
  directly; report cross-agent export only when separately requested.
- Remaining gaps or accepted warnings.

Keep the handoff concise, but make it clear what is public skill content and what is review/development artifact.
