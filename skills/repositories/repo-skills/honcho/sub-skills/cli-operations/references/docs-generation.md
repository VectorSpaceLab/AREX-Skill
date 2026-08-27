# CLI Docs Generation Helper

Honcho CLI command docs are generated from the Typer command tree instead of copied by hand. This sub-skill bundles an adapted generator that imports the installed `honcho_cli` package, walks the Click/Typer command graph, and emits either JSON inventory or Mintlify-style MDX.

## Bundled Script

```bash
python scripts/generate_cli_docs.py --format json
python scripts/generate_cli_docs.py --format mdx --output cli-commands.mdx
python scripts/generate_cli_docs.py --format mdx --check cli-commands.mdx
```

Requirements:

- The Python environment running the script must be able to `import honcho_cli.main`.
- It does not need the original repository checkout.
- It does not call the Honcho API and does not read credentials.

## What The Generator Emits

- One top-level section per root command, sorted by command name.
- Accordion sections for subcommands.
- Invocation lines with positional arguments.
- Parameter fields for arguments and command-specific options.
- Boolean flag negations, short aliases, default values, and simple type labels.
- Global scope/output flags are documented once elsewhere and stripped from per-command parameter lists:
  - `--workspace`
  - `--peer`
  - `--session`
  - `--json`

The JSON mode is better for programmatic checks; MDX mode is better for docs pages.

## Drift-Check Workflow

1. Run the generator against the intended CLI version:

   ```bash
   python scripts/generate_cli_docs.py --format mdx --output /tmp/cli-commands.mdx
   ```

2. Compare the generated file with existing docs.
3. If the existing file should match exactly, use:

   ```bash
   python scripts/generate_cli_docs.py --format mdx --check path/to/cli-commands.mdx
   ```

4. A failed check means the installed CLI command tree and the docs file differ. Update the docs or run against the correct CLI version.

## Source Helper Adapted

Adapted behavior from the repo's CLI docs helper:

- introspect the Typer app rather than maintaining a manual command table;
- preserve Mintlify-style `<AccordionGroup>`, `<Accordion>`, and `<ParamField>` output;
- escape MDX-sensitive `{}`, backslashes, `<`, and JSX attribute quotes;
- strip globally documented flags from individual command docs;
- support a `--check` mode that exits non-zero on stale docs.

Changes made for this runtime skill:

- no hard-coded repository root or docs output path;
- optional `--output` and stdout default;
- optional JSON inventory output;
- no dependency on any source checkout paths;
- errors are phrased for agents running against an installed CLI.

## Source Helpers Excluded

Do not bundle or invoke unrelated repository scripts for CLI docs or CLI operation:

- server provisioning, migration, JWT, embedding, cost-calculator, and benchmark scripts are outside CLI operation scope;
- docs build tooling is outside the runtime skill unless the task explicitly asks to build the website;
- native test files are verification evidence, not runtime helper scripts;
- examples that require external services or application-specific credentials should be used as evidence only, not copied into this sub-skill.

## When To Regenerate Docs

Regenerate command docs when any of these changes:

- a command group, command name, argument, option, default, or help string changes;
- global scope flags change;
- output contracts or error behavior are intentionally changed;
- a new command group is added to `honcho`;
- a downstream docs page fails a command-doc drift check.

After generation, spot-check at least:

```bash
honcho doctor --help
honcho peer --help
honcho session view --help
honcho conclusion create --help
```

Prefer the installed command help when a generated doc and live behavior disagree.
