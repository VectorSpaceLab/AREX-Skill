# Specialized parser guide

## Purpose

Use this reference when the named parser has non-default runtime requirements
or package quirks.

## SHISO

SHISO's package `__init__.py` imports `SHISO` as a top-level module. In a normal
installed package import, that can raise:

```text
ModuleNotFoundError: No module named 'SHISO'
```

Use the bundled wrapper, which adds the installed `logparser/SHISO` directory to
`sys.path` before importing:

```bash
python scripts/run_shiso_with_import_shim.py
```

The verified constructor is:

```python
LogParser(log_format, formatTable=None, indir='./', outdir='./results/', maxChildNum=4, mergeThreshold=0.1, formatLookupThreshold=0.3, superFormatThreshold=0.85, rex=[])
```

## SLCT

SLCT wraps a legacy C helper. The stock helper can fail to compile on newer GCC
settings even when GCC is installed. Use the bundled wrapper, which creates a
safe temp working layout and compiles the helper with relaxed warning handling:

```bash
python scripts/run_slct_safe.py
```

The verified constructor is:

```python
LogParser(indir, outdir, log_format, support, para_j=True, saveLog=False, rex=[])
```

## LogCluster

LogCluster wraps a Perl script. Confirm `perl` is installed before running it.
The constructor has many optional tuning parameters, but a simple smoke usually
uses:

```python
from logparser.LogCluster import LogParser
parser = LogParser(indir, '<Date> <Time> <Level> <Content>', outdir, rsupport=1)
parser.parse('sample.log')
```

The tiny smoke wrote the structured CSV; do not assume a templates CSV is always
created by this parser.

## MoLFI

MoLFI uses `deap`. If the import fails, install the repo requirements or the
`deap` package before trying the parser. Its constructor is:

```python
LogParser(indir, outdir, log_format, rex=[], n_workers=1)
```

The algorithm is evolutionary, so avoid large benchmark-scale runs until a tiny
input works.

## NuLog

NuLog is torch-based and trains a small model during parsing. The verified
constructor and parse entry point are:

```python
parser = LogParser(indir, outdir, filters, k, log_format)
parser.parse(logName, nr_epochs=1, batch_size=1, pad_len=16, d_model=16, N=1)
```

Important quirks:

- Use NumPy below 2 and pandas 1.x; the old code path uses APIs removed from
  newer releases.
- Pass `outdir` with a trailing `/`.
- Expect a structured CSV and model checkpoint, not a templates CSV.
- Use `scripts/run_nulog_smoke.py` for a safe tiny check.

## DivLog

DivLog uses OpenAI API calls and embedding lookup maps. Import-only inspection
requires more than the parser's local requirements:

- `openai==0.27.8`
- `tiktoken==0.4.0`
- `matplotlib`
- `plotly`
- `tenacity`

Live parsing additionally requires a valid API key and network access. Do not
start a DivLog run until credentials and budget are explicit.
