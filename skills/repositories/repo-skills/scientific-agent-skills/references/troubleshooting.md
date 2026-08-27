# Cross-Cutting Troubleshooting

## When to read

Read this when a repo-maintenance task fails before you know whether the owner is skill authoring, validation/testing, or security scanning.

## Quick routing by symptom

| Symptom | Likely owner | What to do |
|---|---|---|
| `skills-ref` cannot parse frontmatter, `name`/`description` appear missing, or a JSON-like `metadata: {...}` block is present | `skill-authoring` | Convert frontmatter to block-style YAML; keep only spec fields at top level for canonical repo skills; quote scalar metadata values. |
| `metadata.version` missing or unquoted | `skill-authoring` then `validation-testing` | Add or quote `metadata.version`; bump it when updating an existing skill. |
| A skill ships `scripts/` and `tests/_meta` reports no suite or manifest entry | `validation-testing` | Add `tests/<skill>/test_*.py` and `[skills.<skill>]` in `tests/skill-requirements.toml`; use `packages = []` for standard-library-only helpers. |
| Pytest complains that multiple skills cannot be collected in one process | `validation-testing` | Run one skill at a time with `pytest tests/<skill>`, or use `python tests/run_all.py` for the whole tree. |
| `python tests/run_all.py --help` says `no test directory for: --help` | `validation-testing` | This runner has a docstring, not an argparse help mode. Read `tests/run_all.py` or run it with a skill name/`--isolated`. |
| `scan_pr_skills.py` writes a skipped comment because `SKILL_SCANNER_LLM_API_KEY` is unset | `security-scanning` | This is expected for fork PRs/no-key contexts. It is not a finding. Ask before using a key/network. |
| Security scanner reports files that do not exist, env-var exfiltration for normal service auth, or `eval` inside words like `retrieval` | `security-scanning` | Verify against the filesystem and `docs/security-triage.md` before editing the skill. |
| Diagram policy says to regenerate `docs/images/<skill>.png`, but no generator is present | `skill-authoring` | Do not fabricate an image. Record the missing tool as a blocker or use the documented generator only if it exists in the target checkout. |
| A repo-wide `skills/*/` glob starts including construction output directories | root/integration | Treat `skills/disco/` and `skills/tests/` as generated construction outputs. Do not commit them to the canonical collection unless the repo policy is updated to exclude or handle them. |

## Safe escalation order

1. Read the changed skill and its nearest references/scripts first.
2. Run a lightweight frontmatter/layout audit from `skill-authoring` if the failure looks structural.
3. Run single-skill validation and tests from `validation-testing`.
4. Run repo-wide `tests/_meta` only after local structural issues are fixed.
5. Plan security scanning last, because scanner output is review material and may require credentials/network.

## Stop conditions

Stop and ask before:

- Installing broad scientific dependency stacks into the project environment.
- Running full security scans with live LLM credentials.
- Uploading or committing generated security reports.
- Creating releases, tags, or public security advisories.
- Mutating or deleting existing skill directories outside the user's requested scope.
