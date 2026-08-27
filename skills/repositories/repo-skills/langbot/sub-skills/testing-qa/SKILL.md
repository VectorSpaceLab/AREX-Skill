---
name: testing-qa
description: "Select LangBot verification layers, run focused pytest, pnpm, Box,
  startup, and lbs QA checks, interpret fixtures and manual_check readiness, and
  collect evidence without over-running slow gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Testing and QA

Use this sub-skill when the task asks which LangBot tests to run, how to verify
a change, how to use the in-repo `skills/` QA assets, or how to interpret
fixture/manual readiness and evidence requirements.

## Read First

- [references/test-selection.md](references/test-selection.md) for layered gates
  and change-surface-to-command mapping.
- [references/lbs-qa-assets.md](references/lbs-qa-assets.md) for `skills/bin/lbs`,
  cases, suites, fixtures, troubleshooting, and UI evidence rules.
- [references/troubleshooting.md](references/troubleshooting.md) for flaky,
  skipped, service-backed, frontend, and browser/fixture failures.

## Golden Rule

Run the narrowest meaningful check first. Expand only when the change crosses
subsystems or the focused test is too synthetic for the risk.

## Command Selector

```bash
python scripts/select_langbot_checks.py quick
python scripts/select_langbot_checks.py api-mcp
python scripts/select_langbot_checks.py pipeline
python scripts/select_langbot_checks.py plugin-box
python scripts/select_langbot_checks.py persistence-rag
python scripts/select_langbot_checks.py frontend
python scripts/select_langbot_checks.py skills-lbs
```

Add `--run --repo-root /path/to/LangBot` only after prerequisites are confirmed.

## Evidence Discipline

- Do not turn optional backend skips into passes.
- UI/browser test cases require UI evidence; API/curl checks are diagnostic for
  UI paths, not replacements.
- Preserve command, scope, result, skipped prerequisites, and artifacts.
- For live provider/platform/browser tests, state credentials/preconditions and
  avoid printing secrets.
