# `lbs` QA Assets

LangBot's `skills/` directory contains a local QA CLI and structured assets for
agent-facing UI/e2e workflows.

## Asset Types

- `skills/skills/*`: reusable LangBot agent skills.
- `cases/*.yaml`: individual QA paths.
- `suites/*.yaml`: ordered case groups.
- `fixtures/`: deterministic fixture readiness metadata.
- `troubleshooting/*.yaml`: reusable failure knowledge.
- `schemas/`: JSON schemas for asset validation.
- `skills/src/`: TypeScript implementation of the `lbs` CLI.

## Common Commands

```bash
cd skills
bin/lbs validate
bin/lbs index --check
bin/lbs env show
bin/lbs env doctor
bin/lbs fixture check
bin/lbs case list --ready
bin/lbs case list --machine-ready
bin/lbs test plan <case-id>
bin/lbs suite plan <suite-id>
```

Run `npm run bootstrap` in `skills/` if `bin/lbs` is missing.

## UI Evidence Rule

For UI/browser testing, API/curl checks are diagnostic only. A UI case passes
only after required UI evidence is collected and preconditions are checked in
the same run.

## Readiness Terms

- `ready`: machine inputs and fixtures are available.
- `machine-ready`: machine inputs exist but manual preconditions may remain.
- `manual_check`: the agent must explicitly verify preconditions before passing.
- Missing env/automation env/fixture readiness means the case is blocked or the
  environment must be fixed first.
