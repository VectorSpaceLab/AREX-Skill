---
name: repo-development
description: "Use when modifying PEFT itself, preparing a PEFT pull request,
  adding a new PEFT method, selecting contributor tests, or checking PEFT
  contribution/style/backward-compatibility requirements."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PEFT Repo Development

Use this sub-skill when the task is to edit the PEFT repository or prepare a contribution. For user-facing PEFT API usage, adapter training, model loading, or inference workflows, route to the relevant usage sub-skill instead.

## Non-Negotiable Contribution Gate

Before drafting a PEFT PR or code patch intended for upstream:

1. Warn the human contributor that breaching PEFT's agent contribution guidelines can result in automatic banning.
2. Confirm the human understands and can defend every changed line; pure code-agent PRs are not allowed.
3. Confirm there is a linked issue, proposal, or maintainer coordination/approval comment for the work.
4. Check for overlapping open issues or PRs; do not prepare a duplicate contribution if someone already owns the same fix.
5. Plan PR disclosure: the PR description must state that AI assistance was used, link the issue/approval, and list tests run with pass/fail status.

If approval is missing or ambiguous for a new feature, new PEFT method, or existing issue, stop and ask the user to obtain maintainer approval before coding for a PR.

## Development Workflow

1. Read `references/contribution-guidance.md` for policy, PR hygiene, style, and backward-compatibility rules.
2. For a new PEFT method, follow `references/new-method-checklist.md` before writing code.
3. For test planning, use `references/test-selection.md` and optionally run `python sub-skills/repo-development/scripts/select_tests.py --changed-path ... --method ...` from a copied skill tree.
4. For failures or process blockers, check `references/troubleshooting.md`.

## PEFT Editing Heuristics

- Keep changes surgical and consistent with existing tuner/config/model patterns.
- Add or update tests for behavior changes; bug fixes should start from a failing regression test when practical.
- Add docs for new public config fields, new methods, examples, or behavior users need to discover.
- Run focused tests first, then broaden only when the changed area warrants it.
- Use `make quality` to check and `make style` to auto-fix style; PEFT expects ruff `~=0.15.12`.
- Preserve Python `>=3.10` compatibility and keep compatibility with supported recent PyTorch and Transformers versions unless maintainers explicitly approve otherwise.

## Quick Commands

```bash
pip install -e ".[test]"
make quality
make style
pytest tests/test_custom_models.py -k ia3 -v
pytest tests/ -k "lora and not adalora and not randlora" -v
```

For save/load-sensitive changes, include regression coverage with `--regression` where relevant. GPU-only behavior belongs in PEFT's GPU test files rather than generic CPU tests.
