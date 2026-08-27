---
name: cli-batch-processing
description: "Use Trafilatura's command line for stdin, URL/list, and local
  directory batch extraction with safe outputs, configs, backups, parallelism,
  and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Batch Processing

Use this sub-skill when the user wants Trafilatura from a shell or automation script rather than Python APIs: stdin extraction, `-u/--URL`, URL-list batches, local `--input-dir` batches, output directories, backups, `--keep-dirs`, output format flags, `--parallel`, `--config-file`, metadata filters, deduplication, precision/recall presets, and XML-TEI validation.

Do **not** use this sub-skill for direct Python function calls; route those requests to `python-extraction`. For feed/sitemap/crawl algorithms beyond the CLI flag invocation, route to `discovery-downloads`. For conceptual deduplication, corpus formats, and TEI quality details, route to `corpus-quality`.

## Start here

1. Confirm the CLI is reachable:
   ```bash
   trafilatura --version
   trafilatura --help
   # PATH fallback when the console script is unavailable:
   python -m trafilatura.cli --help
   ```
2. Choose exactly one primary input mode:
   - no input flag: read HTML bytes from stdin;
   - `-u/--URL`: download and extract one URL;
   - `-i/--input-file`: process a text file containing one URL per line;
   - `--input-dir`: walk local downloaded HTML files.
3. Choose output behavior:
   - no `-o/--output-dir`: print to stdout;
   - `-o DIR`: write result files, creating directories as needed;
   - `--backup-dir DIR`: keep gzipped raw HTML for URL downloads;
   - `--keep-dirs`: preserve local input paths, but only with `-o/--output-dir`.
4. Add extraction and format options deliberately: `--with-metadata`, `--only-with-metadata`, `--deduplicate`, `--precision`, `--recall`, `--xmltei --validate-tei`, `--json`, `--markdown`, etc.
5. For a no-network sanity check, run the bundled helper:
   ```bash
   python scripts/cli_fixture_runner.py
   python scripts/cli_fixture_runner.py --json
   ```

## References

- `references/cli-reference.md` — flag groups, input/output rules, format interactions, safe command construction, exit statuses.
- `references/batch-workflows.md` — ready-to-adapt stdin, URL-list, directory, backup, config, listing, and TEI recipes.
- `references/troubleshooting.md` — CLI-specific failure symptoms and recoveries.
- `scripts/cli_fixture_runner.py` — no-network smoke helper for installed CLI behavior.

## Safety checklist for generated commands

- Quote URLs and paths in shell examples; in Python, prefer `subprocess.run([...])` argument lists over shell strings.
- Keep network batches polite: start with `--parallel 1`, increase only when allowed, and use `SLEEP_TIME` in a config file for domain-level pacing.
- Separate discovery/listing from extraction: `--list` prints URLs only and ignores extraction/output-format expectations.
- Use a small fixture or sample directory before a large batch; verify output content and file names before scaling.
- Prefer relative `--input-dir` values when using `--keep-dirs`, so mirrored output paths stay inside the chosen output directory.

## Provenance

This sub-skill distills Trafilatura 2.2.0 CLI behavior from public package docs, CLI source, settings source, and selected CLI/download tests. Evidence labels include `docs/usage-cli.rst`, `docs/quickstart.rst`, `docs/installation.rst`, `docs/settings.rst`, `docs/troubleshooting.rst`, `trafilatura/cli.py`, `trafilatura/cli_utils.py`, `trafilatura/settings.py`, `trafilatura/settings.cfg`, `tests/cli_tests.py`, and selected `tests/downloads_tests.py` queue cases.
