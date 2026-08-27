# Security Scanning Workflows

## Changed-skill PR scan

`scan_pr_skills.py` accepts skill directories and writes a Markdown comment report:

```bash
uv run python scan_pr_skills.py --output pr_scan_comment.md --fail-on HIGH skills/<name>
```

Behavior to remember:

- Directories without `SKILL.md` are skipped.
- The default fail threshold in the script is CRITICAL; the PR workflow uses HIGH.
- When `SKILL_SCANNER_LLM_API_KEY` is unset, the script writes a skipped/no-key comment and exits 0. That path is intentional for fork PRs.
- With a key, it builds the scanner from `scan_skills.py`, scans each changed skill, and performs cross-skill overlap analysis when more than one skill is scanned.

## Weekly and full scans

`scan_skills.py` scans all skills and writes both:

- `docs/security-report.md`
- `docs/security-report.json`

It uses incremental caching by content hash unless a full scan is requested, the scanner/model changes, or the max age expires. Relevant variables:

- `SKILL_SCANNER_LLM_API_KEY`: required for LLM-backed analysis.
- `SKILL_SCANNER_LLM_MODEL`: default model id.
- `SKILL_SCAN_WORKERS`: concurrent skill scans.
- `SKILL_SCAN_FULL`: force a full rescan when set.
- `SKILL_SCAN_MAX_AGE_DAYS`: age backstop for cache invalidation.

Do not run a full scan merely to check a prose edit unless the user approved the cost/network side effects.

## Security policy scope

In scope: malicious or unsafe bundled scripts, instructions that steer agents toward destructive/exfiltrating/unauthorized action, prompt-injection vectors, misrepresentation of bundled code behavior, unsafe credential handling, and vulnerabilities in scanner/repo workflows.

Out of scope: vulnerabilities in third-party libraries/services, vulnerabilities in agent hosts, the inherent capability of a skill to do its documented work, and missing dependency pins without a concrete exploitation path.

## Triage record

Use `docs/security-triage.md` for human verdicts. It should say what was actually wrong, what was fixed, or why a finding is a known false positive. Include a cheap verification command or filesystem check when possible.
