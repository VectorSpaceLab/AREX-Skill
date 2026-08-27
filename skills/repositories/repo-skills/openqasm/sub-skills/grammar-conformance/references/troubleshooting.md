# Grammar-conformance troubleshooting

Start with the public helper in strict mode, reduce the source, and classify the
failure before changing flags or dependencies.

## Fast triage

```text
python scripts/check_syntax.py --help
python scripts/check_syntax.py --source 'OPENQASM 3.1; qubit q;'
printf 'OPENQASM 3.1;\nqubit[ q;\n' | python scripts/check_syntax.py --json
```

The helper's exit codes are:

| Code | Meaning |
|---:|---|
| 0 | strict parser accepted and any requested normalization succeeded |
| 2 | command-line or input-read error |
| 3 | `openqasm3` parser dependency/import error |
| 4 | `QASM3ParsingError` rejection |
| 5 | unexpected parser/printer failure |

The helper never resolves includes, accesses a network, runs a compiler, or
executes a program.

## `parse` is missing or parser import fails

### Symptom

- `openqasm3` imports, but `openqasm3.parse` is absent;
- importing `openqasm3.parser` says parsing is unavailable;
- a missing `antlr4` module is named.

### Cause

The base `openqasm3` AST package can be installed without parser dependencies.
The top-level package only exposes parser functions when the ANTLR Python
runtime is available.

### Action

Install the parser extra in the environment that will run the check:

```text
python -m pip install 'openqasm3[parser]'
```

Then verify in a clean process:

```text
python -c "import openqasm3.parser; from openqasm3 import parse; print('parser import ok')"
```

If installation policy forbids modifying that environment, create a separate
ordinary Python environment and install the parser extra there. Do not make a
conformance claim from an AST-only installation.

## No generated parser or missing ANTLR variant

### Symptom

Import fails with one of:

```text
No ANTLR-generated parsers found.
Missing ANTLR-generated parser for version '4.x'. Available versions: ...
```

### Cause

`openqasm3` selects pre-generated modules using the installed
`antlr4-python3-runtime` major/minor. The package does not contain the matching
variant, or generated modules were omitted from the installation.

### Action

1. Show the runtime distribution version:

   ```text
   python -c "from importlib.metadata import version; print(version('antlr4-python3-runtime'))"
   ```

2. Reinstall a complete `openqasm3[parser]` artifact whose generated variants
   include that runtime minor, or pin the runtime to a generated variant listed
   in the import error.
3. In grammar-development environments, regenerate with the exact same full
   ANTLR version as the Python runtime and place output in the consumer's
   expected variant package.
4. Start a new Python process and rerun one valid and one lexical-negative
   fixture.

At the verified baseline, generated variants cover ANTLR minors 4.7 through
4.13. Do not infer that future or older minors are compatible.

## Generated code and runtime mismatch

### Symptoms

- deserialization or serialized-ATN errors;
- missing runtime methods or changed constructor signatures;
- parser imports but fails before reading the OpenQASM input;
- behavior changes after only `antlr4-python3-runtime` was upgraded.

### Cause

ANTLR generated Python code is version-sensitive. Package selection by
major/minor does not justify generating with one arbitrary patch and running
with another. The verified workflow matches the generator and Python runtime
full versions.

### Action

Pin both sides to one version, for example:

```text
# Generate with antlr-4.9.2-complete.jar
python -m pip install 'antlr4-python3-runtime==4.9.2'
```

Regenerate lexer/parser/listener/visitor together; do not mix files from two
generation runs. Clear only disposable generated/build caches, start a clean
process, and confirm the runtime version before parsing.

The verified full versions represented at this baseline are `4.7.2`, `4.8`,
`4.9.2`, `4.10.1`, `4.11.1`, `4.12.0`, and `4.13.0`.

## Same package version, different behavior

The verified parser distribution reports `openqasm3` 1.0.1, but current source
at the verified repository baseline contains material changes relative to an
older published artifact with the same version. A version string alone is not
sufficient provenance.

When results disagree:

1. record the exact installed artifact and parser API signatures;
2. record the OpenQASM source baseline or package build provenance;
3. reduce the disagreement to one fixture;
4. prefer the verified current-source baseline for this skill's claims;
5. do not silently merge behavior from two same-version artifacts.

Runtime guidance here uses the verified signatures
`parse(input_, *, permissive=False, ignore_version=False)`,
`parse_version(prog)`, and `get_comments(input_)`.

## Unsupported or malformed versions

### Supported policy

The package declares specification versions `3.0` and `3.1`, while strict
`parse` accepts version tuples from `(3,)` through `(3, 1)`. Consequently,
`OPENQASM 3;`, `3.0`, and `3.1` parse at this baseline.

### Common failures

| Input | Preliminary result | Strict result |
|---|---|---|
| `OPENQASM 2.0;` | detects `(2, 0)` | unsupported version |
| `OPENQASM 4.0;` | detects `(4, 0)` | unsupported version |
| `OPENQASM 3.1.2;` | detects `(3, 1, 2)` | version may have only major or major.minor |
| `OPENQASM invalid;` | detects nothing | lexer/grammar rejection |
| header after another statement | detects nothing | grammar rejection at misplaced `OPENQASM` |
| no header | detects nothing | parser accepts with AST version `None` |

Use `parse_version` only to report a candidate. It does not prove header grammar
or support. Do not “repair” an unsupported version by relabeling the source
without reviewing language-feature compatibility.

## `ignore_version=True` appears to fix the input

`ignore_version=True` skips the parser's supported-version gate and attempts the
current grammar. It does not switch grammar versions and gives no guarantee
that the AST is syntactically or semantically valid for the reported version.

Use it only for a labeled diagnostic comparison:

```text
strict: rejected unsupported version 4.0
ignore-version experiment: current grammar produced an AST
conclusion: no OpenQASM 4.0 conformance established
```

The bundled helper deliberately does not expose this flag.

## `permissive=True` appears to fix the input

Permissive mode lets ANTLR recover and can return an invalid AST while emitting
warnings. It is unsuitable for positive conformance assertions and can make a
negative fixture appear accepted.

For conformance:

- keep `permissive=False`;
- capture stderr as well as the exception;
- minimize the source;
- use a generated exact-tree harness if rule-level recovery behavior itself is
  the subject of a separate experiment.

The bundled helper deliberately does not expose permissive mode.

## Generic `parse failed` with no line or column

### Cause

Strict parsing uses ANTLR's bail strategy. Some parser cancellation paths are
translated into a generic `QASM3ParsingError("parse failed")` and do not carry
the original token position, while lexer errors and explicit AST-visitor
checks often include line/column.

### Action

1. Inspect the helper's captured `parser_stderr` diagnostic if present.
2. Reduce to the shortest failing statement or expression.
3. Add delimiters back one at a time: semicolon, closing bracket, parenthesis,
   or brace.
4. Compare against the nearest parser rule in
   [grammar-guide.md](grammar-guide.md).
5. If exact token position is required, run the same reduced fixture through a
   version-matched generated ANTLR harness with an explicit error listener.
6. Assert the stable reject category in ordinary fixtures; reserve exact full
   messages for a locked generator/runtime pair.

Do not convert a generic positionless grammar error into a semantic diagnosis.

## Line and column look off by one

`QASM3ParsingError.line` is one-based and `.column` is zero-based. Tabs count as
characters in ANTLR's column tracking rather than display-cell widths. Unicode
and normalized editor text can also make visual columns differ.

Report:

```text
line: 1-based
column: 0-based
source excerpt: exact, unexpanded text
```

Do not strip leading whitespace before reproducing a diagnostic. For annotation
and pragma failures, preserve line endings and trailing text exactly.

## Lexer diagnostic appears twice or leaks to stderr

ANTLR's default listener may write a diagnostic while the public parser also
raises `QASM3ParsingError`. The bundled helper redirects parser stderr and puts
it into `parser_stderr`, preserving valid JSON output.

If calling the API directly, use bounded stderr capture around `parse` when
machine-readable output matters. Do not suppress the exception itself, and do
not treat an empty stderr stream as acceptance.

## Include or `defcalgrammar` string fails

These keywords enter arbitrary-string mode. The next meaningful token must be a
non-empty single- or double-quoted string without a tab or line break, followed
by a semicolon.

Check for:

- empty `""` or `''`;
- missing closing quote;
- an unquoted number or keyword;
- an actual tab/newline in the quoted value;
- a missing semicolon.

A successful parse still does not prove that an include exists or a calibration
grammar is installed.

## Annotation or pragma consumes unexpected text

The lexer switches to line mode immediately after the annotation keyword or
pragma token. Everything after initial spaces through the line end is one
opaque `RemainingLineContent` token.

Consequences:

- `@first @second` on one line is one annotation whose command is `@second`;
- use separate lines for separate annotations;
- otherwise-invalid punctuation may be valid command text;
- an annotation applies to the next statement, not every statement on that
  line;
- a pragma command is required by the grammar and the Python parser only permits
  pragmas globally.

Reproduce with exact newlines. Do not normalize or `.strip()` a line-mode
fixture before diagnosis.

## Calibration block fails near a brace

`CAL_BLOCK` balances braces recursively but does not understand the inner
language. Every `{` and `}` in the payload participates in host-level balancing,
including characters that the inner language may regard as part of a comment
or string.

Troubleshooting sequence:

1. Verify the `cal` or `defcal` prelude reaches its first `{`.
2. Count braces in the exact payload, including apparent comments and strings.
3. Reduce nested payloads from inside out.
4. Keep one positive `cal { outer { inner } outer }` fixture.
5. Pair it with a missing-close negative.
6. Validate the inner calibration language separately after host parse success.

An empty body is accepted. Arbitrary non-brace characters are accepted. Neither
fact establishes inner-language validity.

## Trailing comma dispute

Trailing commas are accepted in expression, identifier, argument, operand,
extern, set, array-literal, and index list shapes where the grammar uses
`COMMA?`. They do not create empty elements.

Use paired checks:

```text
accept: f(1, 2,);
reject: f(,);
reject: f(1,,2);
accept: let s = q[{0, 2,}];
accept: array[int[8], 4, 3,] a;
```

If a formatter removes a trailing comma, compare AST/rule shape rather than raw
text. Deep parser/printer analysis belongs to the Python AST sibling.

## Normalized output differs from input

`--normalized` parses to the reference AST and prints that AST. It is not a CST
round trip. Formatting, optional commas, quote style, and comments may change
or disappear. Treat normalized output as a convenient parser/printer
observation, not source-preservation evidence.

For AST printing options and fidelity questions, use
[python-ast-tooling](../../python-ast-tooling/SKILL.md).

## Final diagnostic template

Report all known fields without guessing missing ones:

```text
status: accepted | rejected | dependency-error
layer: lexical | grammar | AST-parser-context | unresolved
input mode: path | literal | stdin
candidate header: <version or none>
AST version: <version, none, or unavailable>
exception: <class or none>
line: <1-based or unavailable>
column: <0-based or unavailable>
parser stderr: <captured text or empty>
semantic/type validation: not performed
include resolution: not performed
provider execution: not performed
```
