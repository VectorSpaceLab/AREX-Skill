# PandasAI CLI Reference

## Purpose

Use this for the `pai` console entry point, API-key login, and guided dataset
creation prompts.

## Console entry point

Package metadata exposes:

```text
pai = pandasai.cli.main:cli
```

Expected top-level commands:

```bash
pai --help
pai dataset --help
pai login PAI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
pai dataset create
```

`pai --help` should show a root group with `dataset` and `login` commands.
`pai dataset --help` should show a `create` command.

## `pai login`

```bash
pai login PAI-59ca2c4a-7998-4195-81d1-5c597f998867
```

Behavior:

- Validates a PandaBI-style key format: `PAI-` followed by five hexadecimal
  groups with hyphen separators.
- If invalid, prints an invalid-format message and exits without writing a key.
- If valid, writes or replaces `PANDABI_API_KEY=...` in `.env` under the detected
  project root.
- Preserves unrelated `.env` variables.

Do not put a real API key in examples or logs.

## `pai dataset create`

The guided create command prompts in this order:

1. dataset path in `organization/dataset` format;
2. dataset name, defaulting to the dataset slug;
3. dataset description;
4. source type, currently `mysql` or `postgres` in the prompt;
5. table name;
6. host, default `localhost`;
7. port;
8. database name;
9. username;
10. password, hidden input.

It writes `schema.yaml` under `datasets/<organization>/<dataset>/` in the
project root. If that schema already exists, it prints an existing-dataset error.

For programmatic schema generation or non-interactive workflows, prefer the
semantic-layer APIs and references.

## Safe CLI smoke

Use the bundled helper instead of real credentials:

```bash
python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --show-help
python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --isolated-login-smoke
```

The isolated smoke uses Click's `CliRunner` and writes only inside a temporary
directory.
