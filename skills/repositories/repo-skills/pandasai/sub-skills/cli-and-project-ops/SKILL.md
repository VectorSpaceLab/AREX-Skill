---
name: cli-and-project-ops
description: "Guides the PandasAI pai CLI, login and dataset-create commands,
  API-key validation, project-root behavior, and lightweight repo maintenance
  operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI and Project Ops

Use this sub-skill when a task involves the `pai` command, PandaBI API-key
login, guided CLI dataset creation, project-root/datasets layout, or maintainer
commands for a PandasAI checkout.

## Fast route

1. Verify the CLI is importable and visible:

   ```bash
   pai --help
   pai dataset --help
   ```

2. For login, validate the key format before writing `.env`:

   ```bash
   pai login PAI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

3. For interactive dataset creation, run from the intended project root because
   `.env` and `datasets/` paths are resolved relative to project-root discovery.
4. For programmatic schema creation or debugging, route to
   [`../semantic-layer/SKILL.md`](../semantic-layer/SKILL.md).
5. For source-code edits or tests, use the maintainer notes and choose focused
   tests instead of all extension targets unless the user needs them.

## Read next

- [`references/cli-reference.md`](references/cli-reference.md) for command
  syntax, prompts, and validation behavior.
- [`references/project-layout.md`](references/project-layout.md) for project root,
  `.env`, and `datasets/` placement.
- [`references/maintainer-notes.md`](references/maintainer-notes.md) for Poetry,
  Makefile, and focused test-selection guidance.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing
  CLI dependencies, invalid keys, interactive prompt issues, and existing
  datasets.
- [`scripts/pai_cli_smoke.py`](scripts/pai_cli_smoke.py) for a safe no-credential
  CLI diagnostic.

## Boundaries

- Route `pai.create`, `pai.load`, schemas, views, and transformations to
  [`../semantic-layer/SKILL.md`](../semantic-layer/SKILL.md).
- Route LLM/provider setup and `.chat()` failures to
  [`../conversational-analysis/SKILL.md`](../conversational-analysis/SKILL.md).
- Route sandbox choices to [`../sandbox-and-security/SKILL.md`](../sandbox-and-security/SKILL.md).

## Safe validation

```bash
python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --show-help
python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --check-api-key PAI-59ca2c4a-7998-4195-81d1-5c597f998867
python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --isolated-login-smoke
```

The smoke uses Click's isolated runner and a fake valid-format key. It never
uses real credentials.

## Common gotchas

- CLI import can fail if `click` is missing from the active environment.
- `pai login` writes or updates `PANDABI_API_KEY` in `.env` under the detected
  project root and preserves unrelated variables.
- `pai dataset create` is interactive. Automate it only with an isolated test
  runner or a deliberate input stream.
- Dataset path validation is the same lowercase hyphenated `organization/dataset`
  contract used by the semantic layer.
- Full extension tests can install many optional packages; prefer focused tests
  when validating a small source change.
