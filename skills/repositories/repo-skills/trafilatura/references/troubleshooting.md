# Trafilatura cross-cutting troubleshooting

Use this reference when the failure spans installation, routing, optional extras, configs, network/download setup, or several sub-skills. Use the nearest sub-skill troubleshooting file for workflow-specific details.

## Install or import fails

Symptoms:

- `ModuleNotFoundError: No module named 'trafilatura'`.
- `trafilatura: command not found`.
- Import works in one shell but not another.

Actions:

1. Verify the intended Python:
   ```bash
   python -c "import sys; print(sys.executable); print(sys.version)"
   python -m pip show trafilatura
   ```
2. Install into that Python:
   ```bash
   python -m pip install trafilatura
   ```
3. If the CLI is missing but import works, call it as a module or fix PATH:
   ```bash
   python -m trafilatura.cli --help
   python -m site --user-base
   ```
4. If compiled dependencies such as `lxml` fail to install, try a current Python version supported by published wheels and update packaging tools inside the active environment.

## Optional feature appears unavailable

Symptoms:

- `target_language` filtering has no effect or behaves unexpectedly.
- SOCKS proxy, `pycurl`, brotli/zstandard compression, or faster date/encoding behavior is missing.
- Benchmark/evaluation commands require many extra packages.

Actions:

- Install `trafilatura[all]` only when optional runtime features are needed.
- Install `trafilatura[eval]` only when the task is explicitly benchmark/evaluation work.
- When optional extras are not installed, keep the base workflow and state the limitation instead of silently promising language/backend/speed behavior.

## Extraction returns `None` or very little text

Likely causes:

- HTML is too short or malformed.
- The main text is outside article-like regions or hidden by page structure.
- `only_with_metadata=True`, `target_language`, `max_tree_size`, or strict config thresholds rejected the result.
- Comments/tables/links/formatting constraints changed the extraction path.

Actions:

1. Route to `sub-skills/python-extraction/references/troubleshooting.md`.
2. Verify input length and parseability with a local fixture.
3. Try `favor_recall=True`, remove overly strict constraints, or use `html2txt()` as a broad fallback.
4. If using the CLI, make sure stdin actually contains the HTML response body, not just a URL string.

## CLI command produces no files or wrong files

Likely causes:

- Missing `--output-dir` with a batch or `--keep-dirs` workflow.
- Confusing stdin, `-u/--URL`, `-i/--input-file`, and `--input-dir` modes.
- Output format flags conflict with expectations.
- Directory permissions or existing layout prevent writes.

Actions:

- Route to `sub-skills/cli-batch-processing/references/troubleshooting.md`.
- Start with a one-file local HTML smoke before adding batches.
- Use `--help` to confirm the installed version's flags.
- Treat `--list` as URL listing/discovery output, not extraction output.

## Live downloads fail but local extraction works

Symptoms:

- Timeout, SSL, proxy, status, or blocked-user-agent issues.
- `fetch_url()` returns `None`.
- CLI URL mode fails while piping saved HTML succeeds.

Actions:

1. Separate retrieval from extraction: save or supply HTML directly and confirm extraction.
2. Route download/debug work to `sub-skills/discovery-downloads/references/troubleshooting.md`.
3. Check proxies, `no_ssl`, timeouts, robots/politeness, optional `pycurl`, and predownloaded HTML alternatives.
4. Do not recommend aggressive retry loops or anti-bot bypass as a Trafilatura feature.

## Config files break behavior

Symptoms:

- A custom config changes extraction thresholds unexpectedly.
- CLI `--config-file` errors or silently changes download/extraction results.

Actions:

- Config files should provide the full expected settings structure, not just one key.
- For small one-off changes, prefer function arguments or `Extractor(...)` rather than a custom file.
- If a custom minimum output size or metadata requirement causes `None`, reduce strictness and retest on a tiny fixture.

## Corpus quality issues

Symptoms:

- Repeated boilerplate or duplicate pages pollute outputs.
- JSON/XML/CSV/TEI output fails downstream parsing.
- Benchmarks require many packages or large fixtures.

Actions:

- Route to `sub-skills/corpus-quality/SKILL.md`.
- Use `deduplicate=True` or `Extractor(dedup=True)` for extraction-time duplicate filtering.
- Use `content_fingerprint()` or `Simhash` for cross-run duplicate detection.
- Validate a representative sample before scaling.
- Treat benchmarks as optional, extra-dependent workflows rather than ordinary extraction checks.

## Which smoke script should run?

| Need | Script |
| --- | --- |
| Basic package/import/CLI/API/dedup sanity | `scripts/check_trafilatura_environment.py` |
| Python extraction API behavior | `sub-skills/python-extraction/scripts/extraction_smoke.py` |
| CLI stdin and local directory behavior | `sub-skills/cli-batch-processing/scripts/cli_fixture_runner.py` |
| Download/discovery imports and no-network helper behavior | `sub-skills/discovery-downloads/scripts/discovery_smoke.py` |
| Dedup/fingerprint/corpus-quality behavior | `sub-skills/corpus-quality/scripts/corpus_quality_smoke.py` |

All bundled scripts are designed to run without live network access.
