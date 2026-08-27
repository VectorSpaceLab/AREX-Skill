# Parsing workflows

## Purpose

Use this reference when you want to parse raw logs into templates or match logs
against already extracted templates.

## Ordinary parsing flow

1. Choose a parser from the core family, usually Drain first.
2. Define the log format string with `<Field>` placeholders.
3. Add optional regex preprocessing rules through the parser's `rex` argument.
4. Set parser-specific thresholds such as `depth`, `st`, `support`, or
   `groupNum`.
5. Run `parse(<logname>)`.
6. Read the resulting structured CSV and templates CSV.

## Drain as the default example

Drain is the best starting point for custom log parsing because the API is
simple and the output is easy to inspect.

Typical pattern:

```python
from logparser.Drain import LogParser

parser = LogParser(
    '<Date> <Time> <Level> <Content>',
    indir='PATH_TO_INPUT_DIR',
    outdir='PATH_TO_OUTPUT_DIR/',
    depth=4,
    st=0.5,
    rex=[r'...'],
)
parser.parse('sample.log')
```

Expected output:

- `sample.log_structured.csv`
- `sample.log_templates.csv`

## Template matching flow

Use `logmatch` when you already have a templates CSV and want to match log lines
back onto those templates.

1. Parse a log file first and keep the resulting templates CSV.
2. Instantiate `RegexMatch` with the same log format.
3. Call `match(log_filepath, template_filepath)`.
4. Inspect the matched structured CSV and template frequency CSV.

Typical pattern:

```python
from logparser.logmatch import RegexMatch

matcher = RegexMatch(outdir='PATH_TO_MATCH_OUTPUT/', n_workers=1, logformat='<Date> <Time> <Level> <Content>')
matcher.match('sample.log', 'sample.log_templates.csv')
```

## Common parser families

The ordinary parser route also covers AEL, IPLoM, LKE, LFA, LogSig, LenMa,
LogMine, Spell, Logram, Brain, and ULP. Their constructor knobs vary, but the
core parse pattern is the same: define `log_format`, set the input/output
paths, tune one or two parser thresholds, and call `parse()`.

## Why this workflow matters

This is the route for the most common user request: turn unstructured logs into
structured rows and templates without thinking about compilers, GPUs, or API
keys.
