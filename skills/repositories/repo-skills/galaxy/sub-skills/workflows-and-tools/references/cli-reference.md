# CLI Reference

## Installed Package Surface

The `galaxy-tool-util` package exposes developer CLIs for formatting tool XML, validating test files, running tool tests against a Galaxy server, upgrade advice, and mulled helper commands. The verified package version for this skill generation was `26.1.dev0`; future agents should check the local installation before assuming a command is available.

Use the bundled helper for a safe local inventory:

```bash
python scripts/inspect_tool_util.py --check-imports --help-checks
```

## Safe Local Commands

These commands are local by default and do not require credentials or a running Galaxy server:

```bash
python -m galaxy.tool_util.format --diff path/to/tool.xml
python -m galaxy.tool_util.format path/to/tool.xml
python -m galaxy.tool_util.validate_test_format path/to/tests.yml
python -m galaxy.tool_util.upgrade.script path/to/tool.xml --profile-version 24.2
python scripts/inspect_tool_util.py --tool-xml path/to/tool.xml --test-file path/to/tests.yml
mulled-hash 'samtools=1.3.1,bedtools=2.26.0'
```

`galaxy-tool-format` rewrites XML unless `--diff` is supplied. Prefer `--diff` during diagnosis and ask before modifying user files if that was not requested.

`validate-test-format` checks the Planemo/Galaxy test model shape only. It does not verify that every named input or output exists in the referenced tool or workflow.

`galaxy-tool-upgrade-advisor` reads a tool XML file and reports profile upgrade advice. Use `--json` when a machine-readable report is useful; note that human-readable advice is usually easier for quick repair work.

`mulled-hash` computes image names from package targets. It is safe for deterministic naming, unlike build/search/list/update commands that may contact external systems or require container tooling.

## Server-Backed Tool Testing

`galaxy-tool-test` runs tool tests against a Galaxy server:

```bash
galaxy-tool-test \
  --galaxy-url http://localhost:8080 \
  --key "$GALAXY_API_KEY" \
  --tool-id TOOL_ID \
  --test-index 0 \
  --output-json tool-test-results.json
```

Important options:

- `--galaxy-url`: target Galaxy URL, defaulting to `http://localhost:8080`.
- `--key` / `--admin-key`: user or admin API key; never invent or expose keys.
- `--tool-id`: target tool ID; use `*` behavior only when the user asks to run broad test sets.
- `--tool-version`: test a specific version or `*` for all versions.
- `--test-index`: run one zero-based test index; omit for all tests.
- `--output`: directory for downloaded outputs.
- `--output-json`: JSON metadata report.
- `--parallel-tests`, `--retries`, `--page-size`, `--page-number`: useful for larger suites.
- `--with-reference-data` / `--skip-with-reference-data`: include or skip tests that use data tables or `.loc` files.
- `--test-data`: add local test data search paths.

Because this command can create histories, upload data, execute jobs, and use credentials, ask for an explicit target and approval unless the user already requested it.

## External Dependency Management Commands

Treat these commands as non-default because they may use conda metadata, BioContainers, container engines, registries, or network access:

```bash
mulled-build ...
mulled-build-channel ...
mulled-build-files ...
mulled-build-tool ...
mulled-list ...
mulled-search ...
mulled-update-singularity-containers ...
```

Galaxy marks unit tests that interact with Conda, container registries, or BioContainers with an `external_dependency_management` marker. Follow the same principle in agent workflows: describe requirements, ask before network/container actions, and prefer deterministic local checks first.

## Reference-Only Repository Scripts

The repository's tool XML validation shell script is reference-only for this generated skill. It assumes a Galaxy checkout layout, activates a project virtual environment, uses the repository XSD, sets `PYTHONPATH`, and calls `xmllint`. The generated skill therefore provides `scripts/inspect_tool_util.py` as a portable inspection helper instead of bundling the harness-specific shell script.

The CWL conformance update shell script is also reference-only because it downloads external archives, unpacks them, deletes and rewrites conformance test directories, and then regenerates test cases. Do not run that path unless the user explicitly requests conformance-suite refresh work.
