# Specialized parser troubleshooting

## SHISO

**Symptom:** `ModuleNotFoundError: No module named 'SHISO'`.

**Recovery:** run `scripts/run_shiso_with_import_shim.py` or add the installed
`logparser/SHISO` directory to `sys.path` before importing `logparser.SHISO`.

## SLCT

**Symptom:** `Compile error! Please check GCC installed.`

**Recovery:** confirm `gcc` exists, then use `scripts/run_slct_safe.py`. The
helper compiles the C program with `-Wno-error` and creates the working layout
expected by the legacy wrapper.

## LogCluster

**Symptom:** `perl` command not found or no result from the Perl-backed helper.

**Recovery:** install or expose Perl, then rerun a tiny input before trying a
full benchmark. Treat a structured CSV without a templates CSV as expected for
this parser.

## MoLFI

**Symptom:** `ModuleNotFoundError: No module named 'deap'`.

**Recovery:** install the repository requirements or `deap`, then rerun a tiny
fixture. Avoid full benchmarks until the tiny parse succeeds.

## NuLog

**Symptoms:**
- `np.unicode_ was removed in the NumPy 2.0 release`
- `module 'pandas' has no attribute 'value_counts'`
- parse finishes but output files are missing

**Recovery:**
- Use NumPy `<2` and pandas `1.x`.
- Pass `outdir` with a trailing slash.
- Use `scripts/run_nulog_smoke.py` as the first check.

## DivLog

**Symptoms:** missing `matplotlib`, `plotly`, `tenacity`, API errors, or empty
LLM responses.

**Recovery:**
- Install DivLog extras.
- Confirm API key, model name, network, rate limit, and spend budget.
- Run import-only checks when credentials are unavailable.
