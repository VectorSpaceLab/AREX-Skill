# Data formats

## Purpose

Read this when you need the repository's log-format syntax, output CSV shape,
dataset layout, or the differences between parser outputs.

## Log-format strings

Most parsers use a format string with angle-bracket placeholders such as:

```text
<Date> <Time> <Level> <Content>
```

The parser converts the format string into a regex and then extracts the named
columns from each input line. Common rules:

- Literal whitespace in the format string is usually converted into `\s+`.
- Fields wrapped in `<...>` become named capture groups.
- Regex preprocessing via `rex` or `regex` arguments happens before template
  extraction.
- If your log line layout is inconsistent, fix the format string before tuning
  parser thresholds.

## Common output columns

The ordinary parsers and `logmatch` usually write a structured CSV with some or
all of these fields:

- `LineId`
- original log-format columns such as `Date`, `Time`, `Level`, `Component`,
  `Content`, or `Pid`
- `EventId`
- `EventTemplate`
- `ParameterList`

The companion templates CSV usually contains:

- `EventId`
- `EventTemplate`
- `Occurrences`

## Parser-specific output notes

- `Drain`, `AEL`, `IPLoM`, `LKE`, `LFA`, `LogSig`, `LenMa`, `LogMine`,
  `Spell`, `Logram`, `Brain`, `ULP`, and `logmatch` write both structured and
  template CSVs.
- `LogCluster` writes the structured CSV; the parser-catalog reference explains
  the expected workflow.
- `NuLog` writes the structured CSV and a model checkpoint file such as
  `model_parser_<logname><epoch>.pt`; it does not create a templates CSV in the
  tiny smoke run.
- `DivLog` writes result CSVs and lookup-map JSON files instead of the ordinary
  parser pair.
- `SLCT` and `SHISO` follow the ordinary structured/template pattern once their
  backend-specific import or compile steps are satisfied.

## Dataset layout

The repository uses these data locations:

- `data/test_log/unknow.log` — tiny sample for smoke checks.
- `data/loghub_2k/` — benchmark corpora used by the benchmark scripts.
- `data/loghub_2k_corrected/` — corrected benchmark labels noted in the docs.

## Helper modules

### `logparser.utils.logloader.LogLoader`

- Constructor: `LogLoader(logformat, n_workers=1)`
- `load_to_dataframe(log_filepath)` reads a log file, parses it according to
  the format string, and returns a DataFrame with `LineId` plus the extracted
  columns.
- Useful when you want to inspect the parsed rows before running a benchmark or
  a custom helper.

### `logparser.utils.evaluator.evaluate`

- Signature: `evaluate(groundtruth, parsedresult)`
- It reads both CSVs, compares `EventId`, and prints precision, recall,
  `F1_measure`, and `Parsing_Accuracy`.
- It expects the ground-truth and parsed CSVs to line up row-for-row after any
  invalid ground-truth IDs are removed.

## Gotchas

- If a parser writes only a structured CSV, do not expect a templates file to
  appear.
- Some parsers are sensitive to the output directory format; NuLog expects an
  `outdir` value that ends with `/` when using its default save logic.
- If a parser needs a matching template file, use the bundled parsing helper or
  run the parser first and then feed the resulting templates into `logmatch`.
