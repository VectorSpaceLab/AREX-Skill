---
name: security-scanning
description: "Plans and triages Scientific Agent Skills security scans using
  scan_pr_skills.py, scan_skills.py, SKILL_SCANNER_LLM_API_KEY, no-key PR
  behavior, weekly incremental reports, docs/security-report outputs, and
  docs/security-triage false-positive verification rules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Security Scanning

Use this route when the task involves the repository's automated skill scanner, generated security reports, or a scanner finding against a skill.

## Safety posture

Scanner output is a prompt for review, not a determination that a skill is unsafe. Always verify findings against the actual files before changing a skill.

Do not run LLM-backed scans, upload generated reports, or post PR comments unless the user authorizes network/API-key use. Never print API key values.

## Changed-skill scan

Read `references/security-scanning.md` and use the bundled planner:

```bash
python sub-skills/security-scanning/scripts/plan_security_scan.py \
  --repo-root . \
  --mode changed \
  --skill <name> \
  --fail-on HIGH \
  --output pr_scan_comment.md
```

The PR workflow fails on HIGH or above when a key is present. If `SKILL_SCANNER_LLM_API_KEY` is unavailable, `scan_pr_skills.py` writes an explanatory skipped comment and exits 0; this is expected for fork PRs and no-key contexts.

## Weekly/full scan

Use `scan_skills.py` only after explicit approval because it can run many LLM-backed analyses and update generated report files:

```bash
SKILL_SCANNER_LLM_API_KEY=... uv run python scan_skills.py --full --workers 8
```

`docs/security-report.md` and `docs/security-report.json` are generated outputs. Human verdicts and repeat false-positive notes belong in `docs/security-triage.md`.

## Triage workflow

1. Locate the cited skill and files; confirm they exist.
2. Inspect the code or Markdown around each cited line.
3. Compare environment variables to the documented service destination.
4. Check `references/troubleshooting.md` for known false-positive classes.
5. Fix only verified unsafe behavior or instructions.
6. Record false-positive classes or real fixes in the triage note when the report would otherwise cause repeat work.

Route structural/test failures to `validation-testing`; route content/version/layout fixes to `skill-authoring`.
