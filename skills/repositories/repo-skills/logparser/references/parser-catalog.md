# Parser catalog

## Purpose

Use this table to choose the right parser family, confirm the import path, and
remember which sub-skill owns the parser-specific guidance.

## Core parser family

These parsers follow the ordinary `LogParser` pattern and are owned by
`sub-skills/parsing/`.

| Parser | Import path | Constructor summary | Typical outputs | Notes |
| --- | --- | --- | --- | --- |
| Drain | `from logparser.Drain import LogParser` | `LogParser(log_format, indir='./', outdir='./result/', depth=4, st=0.4, maxChild=100, rex=[], keep_para=True)` | `*_structured.csv`, `*_templates.csv` | Best default route for custom log parsing. |
| AEL | `from logparser.AEL import LogParser` | `LogParser(indir, outdir, log_format, minEventCount=2, merge_percent=1, rex=[], keep_para=True)` | `*_structured.csv`, `*_templates.csv` | Uses anonymize/tokenize/categorize/reconcile steps. |
| IPLoM | `from logparser.IPLoM import LogParser` | `LogParser(log_format, indir='../logs/', outdir='./result/', maxEventLen=200, step2Support=0, PST=0, CT=0.35, lowerBound=0.25, upperBound=0.9, rex=[], keep_para=True)` | `*_structured.csv`, `*_templates.csv` | Iterative partitioning workflow. |
| LKE | `from logparser.LKE import LogParser` | `LogParser(log_format, indir='../logs/', outdir='./results/', split_threshold=4, rex=[], seed=1)` | `*_structured.csv`, `*_templates.csv` | Weighted edit-distance clustering. |
| LFA | `from logparser.LFA import LogParser` | `LogParser(indir, outdir, log_format, rex=[])` | `*_structured.csv`, `*_templates.csv` | Token-frequency abstraction. |
| LogSig | `from logparser.LogSig import LogParser` | `LogParser(indir, outdir, groupNum, log_format, rex=[], seed=0)` | `*_structured.csv`, `*_templates.csv` | Requires the desired number of clusters. |
| LenMa | `from logparser.LenMa import LogParser` | `LogParser(indir, outdir, log_format, threshold=0.9, predefined_templates=None, rex=[])` | `*_structured.csv`, `*_templates.csv` | Length-based template extraction. |
| LogMine | `from logparser.LogMine import LogParser` | `LogParser(indir, outdir, log_format, max_dist=0.001, levels=2, k=1, k1=1, k2=1, alpha=100, rex=[])` | `*_structured.csv`, `*_templates.csv` | Uses n-gram style pattern recognition. |
| Spell | `from logparser.Spell import LogParser` | `LogParser(indir='./', outdir='./result/', log_format=None, tau=0.5, rex=[], keep_para=True)` | `*_structured.csv`, `*_templates.csv` | Streaming LCS-based parser. |
| Logram | `from logparser.Logram import LogParser` | `LogParser(log_format, indir='./', outdir='./result/', doubleThreshold=15, triThreshold=10, rex=[])` | `*_structured.csv`, `*_templates.csv` | n-gram dictionary parser. |
| Brain | `from logparser.Brain import LogParser` | `LogParser(logname, log_format, indir='./', outdir='./result/', threshold=2, delimeter=[], rex=[])` | `*_structured.csv`, `*_templates.csv` | Bidirectional tree parser. |
| ULP | `from logparser.ULP import LogParser` | `LogParser(log_format, indir='./', outdir='./result/', rex=[])` | `*_structured.csv`, `*_templates.csv` | Uses learned grouping and frequency logic; keep workflow notes in the parsing sub-skill. |

## Specialized parser family

These parsers need the specialized sub-skill because they have extra imports,
import shims, compiler steps, CUDA/torch runtime behavior, or API credentials.

| Parser | Import path | Constructor summary | Typical outputs | Notes |
| --- | --- | --- | --- | --- |
| LogCluster | `from logparser.LogCluster import LogParser` | `LogParser(indir, log_format, outdir, ..., rsupport=None, ...)` | `*_structured.csv` | Perl-backed wrapper; structured CSV is the main output. |
| MoLFI | `from logparser.MoLFI import LogParser` | `LogParser(indir, outdir, log_format, rex=[], n_workers=1)` | `*_structured.csv`, `*_templates.csv` | Requires `deap`; evolutionary workflow. |
| NuLog | `from logparser.NuLog import LogParser` | `LogParser(indir, outdir, filters, k, log_format)` | `*_structured.csv` plus model checkpoint | Needs `torch` / `torchvision` / `keras_preprocessing`; tiny runs require `outdir` to end with `/`. |
| SHISO | `from logparser.SHISO import LogParser` after a `sys.path` shim that adds the installed `logparser/SHISO` directory | `LogParser(log_format, formatTable=None, indir='./', outdir='./results/', maxChildNum=4, mergeThreshold=0.1, formatLookupThreshold=0.3, superFormatThreshold=0.85, rex=[])` | `*_structured.csv`, `*_templates.csv` | The package import is not fully relative; use the bundled shim helper. |
| SLCT | `from logparser.SLCT import LogParser` | `LogParser(indir, outdir, log_format, support, para_j=True, saveLog=False, rex=[])` | `*_structured.csv`, `*_templates.csv` | C helper compile needs relaxed GCC warning handling on this host. |
| DivLog | `from logparser.DivLog import ModelParser` | `ModelParser(log_path, result_path, map_path, dataset, emb_path, cand_ratio, split_method, order_method, permutation, warmup, subname, evaluate)` | result CSVs, map JSON, optional benchmark CSV | API-backed flow; needs OpenAI credentials and `openai`/`tiktoken`/`matplotlib`/`plotly`/`tenacity`. |
| logmatch | `from logparser.logmatch import RegexMatch` | `RegexMatch(outdir='./result/', n_workers=1, optimized=False, logformat=None)` | `*_structured.csv`, `*_templates.csv` | Matches logs to existing templates rather than learning new ones; the bundled matcher helper patches the legacy whitespace replacement in `logloader.py` for current `regex` builds. |

## Cross-cutting notes

- The ordinary parser family is easiest to use through the `parsing` sub-skill.
- The benchmark/evaluation flow is separate from parser selection; use the
  `benchmarking` sub-skill for metric and dataset guidance.
- If a parser row mentions a quirk, the troubleshooting reference should carry
  the concrete recovery steps.
