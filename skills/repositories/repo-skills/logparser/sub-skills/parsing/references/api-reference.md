# Parsing API reference

## Purpose

Use this reference for the constructor knobs and method names that matter when
parsing raw logs or matching templates.

## Common entry points

| API | Signature summary | Notes |
| --- | --- | --- |
| Drain | `LogParser(log_format, indir='./', outdir='./result/', depth=4, st=0.4, maxChild=100, rex=[], keep_para=True)` / `parse(logName)` | Best default parser and the easiest smoke target. |
| AEL | `LogParser(indir, outdir, log_format, minEventCount=2, merge_percent=1, rex=[], keep_para=True)` / `parse(logname)` | Uses merge percentage rather than Drain-style tree depth. |
| IPLoM | `LogParser(log_format, indir='../logs/', outdir='./result/', maxEventLen=200, step2Support=0, PST=0, CT=0.35, lowerBound=0.25, upperBound=0.9, rex=[], keep_para=True)` / `parse(logname)` | Good when you need iterative partitioning controls. |
| LKE | `LogParser(log_format, indir='../logs/', outdir='./results/', split_threshold=4, rex=[], seed=1)` / `parse(logname)` | Uses weighted edit-distance clustering. |
| LFA | `LogParser(indir, outdir, log_format, rex=[])` / `parse(logname)` | Minimal parser surface. |
| LogSig | `LogParser(indir, outdir, groupNum, log_format, rex=[], seed=0)` / `parse(logname)` | Requires the cluster count up front. |
| LenMa | `LogParser(indir, outdir, log_format, threshold=0.9, predefined_templates=None, rex=[])` / `parse(logname)` | Threshold-driven template extraction. |
| LogMine | `LogParser(indir, outdir, log_format, max_dist=0.001, levels=2, k=1, k1=1, k2=1, alpha=100, rex=[])` / `parse(logname)` | Exposes distance and level controls. |
| Spell | `LogParser(indir='./', outdir='./result/', log_format=None, tau=0.5, rex=[], keep_para=True)` / `parse(logname)` | Streaming LCS-based parser. |
| Logram | `LogParser(log_format, indir='./', outdir='./result/', doubleThreshold=15, triThreshold=10, rex=[])` / `parse(log_file_basename)` | n-gram dictionary parser. |
| Brain | `LogParser(logname, log_format, indir='./', outdir='./result/', threshold=2, delimeter=[], rex=[])` / `parse(logName)` | Tree-based parser with a slightly unusual constructor order. |
| ULP | `LogParser(log_format, indir='./', outdir='./result/', rex=[])` / `parse(logname)` | Simpler constructor than many older parsers. |
| `logmatch.RegexMatch` | `RegexMatch(outdir='./result/', n_workers=1, optimized=False, logformat=None)` / `match(log_filepath, template_filepath)` | Matches logs to an existing templates CSV instead of learning new templates. |

## Shared method behavior

- `parse()` usually takes a log file name relative to `indir`.
- `rex` lists are applied before template extraction.
- Output paths are often concatenated directly, so keep `outdir` normalized and
  create the directory first when a parser expects it.
- Parsers typically write `*_structured.csv` and `*_templates.csv`, while the
  `logmatch` matcher writes the same pair after matching.

## Use this with the script helpers

- `scripts/parse_tiny_drain.py` shows the minimal end-to-end path.
- `scripts/match_templates.py` shows how to reuse a templates CSV.
