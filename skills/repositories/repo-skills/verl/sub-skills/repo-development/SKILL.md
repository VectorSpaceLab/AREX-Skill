---
name: repo-development
description: "Guide verl maintainers through contribution policy,
  agent-instruction edits, focused test selection, generated config maintenance,
  and safe pre-commit choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# verl Repo Development

Use this sub-skill when changing verl repository internals, tests, docs, generated trainer config files, CI/workflow selections, or AI-agent instructions. Keep the advice maintainer-focused; for end-user training/inference workflows, route to the relevant runtime or configuration sub-skill instead.

## Maintainer Routing

- Before PR work, check `references/contributor-policy.md` for duplicate-work checks, low-value PR limits, AI-assistance disclosure, and AGENTS.md/domain-guide rules.
- For focused validation, read `references/testing-and-maintenance.md` and use `scripts/select_verl_tests.py` to map changed paths to suggested pytest targets and pre-commit hooks.
- For generated trainer config, docs, or config-reference changes, read the autogen section in `references/testing-and-maintenance.md`; generated YAML is maintained through the repo script, not by hand.
- For common failures, agent-instruction edit blockers, CPU/GPU/NPU routing mistakes, and out-of-date generated configs, read `references/troubleshooting.md`.

## Safe Helper

Run the bundled helper from the repository root to print suggestions only; it does not execute tests, mutate files, call GitHub, or invoke pre-commit:

```bash
python skills/disco/verl/sub-skills/repo-development/scripts/select_verl_tests.py --changed-paths verl/trainer/config/ppo_trainer.yaml tests/test_base_config_on_cpu.py
```

The helper accepts `--from-file` for newline-separated changed paths and `--json` for machine-readable output.

## Required Boundaries

- Do not propose a pure code-agent PR; a human submitter must understand and review every line.
- Do not proceed with duplicate or trivial busywork PRs; fail closed with the missing duplicate-check or scope information.
- Do not edit `AGENTS.md` or linked agent guides until the editing guide has been read and its checklist applied.
- Do not tell agents to run `tests/kill_github_tests.sh`; it is intentionally excluded from this skill.
