# In-Repo Skills and `lbs` Assets

The repository's `skills/` directory is the single source of truth for
LangBot-specific agent skills, cases, suites, fixtures, troubleshooting entries,
and the `lbs` TypeScript QA CLI.

## Existing Skill Catalog

The maintained catalog includes guidance for core development, plugin
development, deployment, testing, environment setup, MCP operations, Space MCP
operations, EBA adapter development, and skill maintenance.

When LangBot API/MCP behavior changes, update the matching agent-facing skill
or reference in the same pass so agents do not drift from the runtime surface.

## `lbs` Workflow

Typical commands from the `skills/` directory:

```bash
bin/lbs validate
bin/lbs index --check
bin/lbs env show
bin/lbs env doctor
bin/lbs case list --ready
bin/lbs test plan <case-id>
bin/lbs suite plan <suite-id>
```

Run `npm run bootstrap` inside `skills/` if the generated `bin/lbs` wrapper is
missing in a fresh checkout.

## QA Asset Rules

- Put reusable cases under `cases/`, suites under `suites/`, fixtures under the
  fixture manifest, and troubleshooting under narrow YAML entries.
- Do not store secrets, localStorage tokens, OAuth credentials, or local machine
  paths.
- UI/browser testing is the primary QA path for UI cases; raw API checks are
  diagnostic and cannot by themselves make a UI case pass.
- `manual_check` means machine inputs exist but the agent must verify declared
  preconditions in the same run before passing the case.
