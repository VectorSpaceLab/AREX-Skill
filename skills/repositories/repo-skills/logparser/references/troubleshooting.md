# Troubleshooting

## Purpose

Use this when Logparser installs, imports, compiles, or runs with the wrong
parser-specific dependency set.

## Installation and import issues

### `pip check` fails or imports resolve to the wrong package

**Symptoms**
- `pip check` reports conflicts.
- `import logparser` succeeds, but a parser import fails.
- A module resolves from the source checkout instead of the intended install.

**Likely causes**
- The editable install is incomplete.
- Optional dependencies from the repo requirements were skipped.
- Another checkout or environment is shadowing the target package.

**Recovery**
1. Run `scripts/check_install.py`.
2. Reinstall the editable package and the repo requirements.
3. Verify the import from the environment Python with `-I`.

### SHISO import fails

**Symptoms**
- `ModuleNotFoundError: No module named 'SHISO'`
- `import logparser.SHISO` fails even though the package tree is present.

**Likely cause**
- `logparser/SHISO/__init__.py` uses a non-relative import and needs the
  installed `logparser/SHISO` directory on `sys.path`.

**Recovery**
- Use `sub-skills/specialized-parsers/scripts/run_shiso_with_import_shim.py`.
- If you are experimenting manually, prepend the installed `logparser/SHISO`
  directory to `sys.path` before importing `logparser.SHISO`.

## Dependency and backend issues

### SLCT compile error on modern GCC

**Symptoms**
- The parser prints `Compile error! Please check GCC installed.`
- GCC emits warnings about format strings or overflow and the wrapper stops.

**Likely cause**
- The legacy C helper is compiled with warning settings that are too strict on
  newer toolchains.

**Recovery**
- Use `sub-skills/specialized-parsers/scripts/run_slct_safe.py`.
- Compile the helper with relaxed warning handling such as `-Wno-error`.
- Confirm `gcc` is available before running the wrapper.

### NuLog fails with NumPy or pandas API errors

**Symptoms**
- `AttributeError: np.unicode_ was removed in the NumPy 2.0 release`
- `AttributeError: module 'pandas' has no attribute 'value_counts'`

**Likely cause**
- NuLog still depends on older NumPy/pandas APIs.

**Recovery**
- Use the pinned environment that keeps NumPy below 2 and pandas in the 1.x
  line.
- Re-run the bundled NuLog smoke after downgrading the packages.

### NuLog output files are missing

**Symptoms**
- The parse completes, but the expected files are not in the output directory.

**Likely cause**
- The parser concatenates paths directly, so `outdir` should end with `/`.

**Recovery**
- Pass an `outdir` with a trailing slash or use the bundled NuLog helper.

### DivLog import or parse fails

**Symptoms**
- Missing-module errors for `matplotlib`, `plotly`, or `tenacity`.
- OpenAI API errors or empty parsing results.

**Likely causes**
- The API-backed workflow needs the extra visualization and retry packages.
- No API key or network access is available.

**Recovery**
- Install the DivLog extras and use the bundled install-check script.
- Verify the key and network before attempting the live parse.
- If credentials are unavailable, keep DivLog in import/inspection mode only.

### LogCluster or SHISO path surprises

**Symptoms**
- The parser runs, but a file is written to an unexpected location.
- A parser needs a specific working directory layout.

**Likely causes**
- Legacy helper code uses relative paths for compiled binaries or temporary
  files.

**Recovery**
- Use the bundled helpers instead of running the source demo directly.
- Prefer the skill-owned script wrappers, which create the needed temp layout.

## Data and configuration issues

### `logformat` does not match the input file

**Symptoms**
- Rows are skipped or the parser reports a low loading rate.
- `EventTemplate` output looks like raw content or all wildcards.

**Likely causes**
- The format string does not match the actual columns.
- Regex pre-processing is too aggressive.

**Recovery**
- Re-read `references/data-formats.md`.
- Start from the bundled tiny Drain smoke and adapt the format string.

### `logmatch` cannot find a template file

**Symptoms**
- `RegexMatch.match` fails because the template CSV is missing.

**Likely cause**
- `logmatch` expects a prebuilt templates CSV from a prior parsing run.

**Recovery**
- Run a parser first, then feed the generated templates CSV into `logmatch`.

### `logmatch` fails with `bad escape \s`

**Symptoms**
- The matcher raises `regex._regex_core.error: bad escape \s` while building the log-format regex.

**Likely cause**
- The repository's legacy `logloader.py` replacement string is not compatible with the current `regex` package behavior.

**Recovery**
- Use `sub-skills/parsing/scripts/match_templates.py`, which patches `LogLoader` at runtime.
- If you are calling `RegexMatch` manually, monkey-patch `logparser.utils.logloader.LogLoader._generate_logformat_regex` so it emits `r"\\s+"` instead of a bare `"\\s+"` replacement string.

## When to stop

Stop and reassess if the failure needs a private API key, a different Python
version, or a parser-specific source patch that is not already bundled here.
