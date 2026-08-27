# Conformance workflows

Use these workflows to turn a syntax claim into reproducible evidence. Keep
reference-grammar acceptance, Python AST-parser acceptance, semantic/compiler
validation, and provider execution as separate result fields.

## 1. Define the conformance claim

Before constructing a fixture, write a one-sentence claim with five fields:

| Field | Example |
|---|---|
| layer | grammar acceptance |
| construct | trailing comma in an `expressionList` |
| source baseline | OpenQASM specification 3.1 grammar |
| parser mode | strict, version checks enabled |
| expected observation | accept `f(1,);`, reject `f(,);` |

If the claim is about types, declaration legality beyond the Python parser's
context checks, symbol resolution, lowering, or hardware behavior, it is not a
pure grammar-conformance claim. Record the syntax result, then hand the later
layer off separately.

## 2. Positive exact-tree fixtures

A positive fixture should assert more than “no exception.” Use a minimal source
and a canonical parse-tree representation that contains rule names and terminal
text but excludes unstable object ids and token implementation details. A
portable fixture record can use this shape:

```yaml
id: expression-power-right-associative
source: |
  int x = 2 ** 3 ** 2;
expect:
  accepted: true
  root_rule: program
  exact_tree: |
    program
      statementOrScope
        statement
          classicalDeclarationStatement
            # continue with every rule/token in canonical order
      <EOF>
```

The exact tree should be generated from the ANTLR `program` rule, recursively
printing `Trees.getNodeText(node, parser.ruleNames)` with two spaces per level.
Compare the complete resulting string. This catches rule-choice and precedence
changes that a simple parse-success assertion misses.

Good exact-tree fixture families include:

- version and header placement;
- each named statement alternative;
- expression precedence and right-associative `**`;
- empty, one-item, multi-item, and trailing-comma lists;
- ranges and set indexes;
- annotation/pragma line payloads;
- nested calibration bodies;
- comments on the hidden channel alongside an otherwise unchanged parser tree.

Keep one concept per fixture. If a source contains several statements for
convenience, give each expected rule path an independent assertion so one
failure does not conceal another.

### Exact-tree harness discipline

For grammar-development work, generate a parser in an isolated temporary build
directory from the two grammar files. Do not import generated modules from an
unrelated installation or depend on an unrecorded module layout. A typical
Python generation command is:

```text
java -jar antlr-4.9.2-complete.jar \
  -Dlanguage=Python3 -visitor -o generated \
  qasm3Lexer.g4 qasm3Parser.g4
```

Use the same ANTLR full version for the generator and
`antlr4-python3-runtime`. The generated import layout depends on the output
directory, so add only that temporary generated directory to the test process's
module search path. Treat the generated files as disposable build products,
not runtime skill content.

When exact-tree output changes, first classify the change:

1. tokenization change;
2. parser-rule alternative change;
3. precedence/associativity change;
4. harmless generated-runtime formatting difference;
5. intended grammar change requiring fixture review.

Do not update the expected tree until the intended category is recorded.

## 3. Negative fixtures

A negative grammar suite is most useful when each source is one line or one
small block and changes exactly one feature from a paired valid source.
Recommended record:

```yaml
id: expression-list-empty-leading-item
layer: grammar
valid: "f(1,);"
invalid: "f(,);"
expect:
  accepted: false
  first_bad_line: 1
  first_bad_column: 2
  message_contains_any:
    - no viable alternative
    - mismatched input
    - parse failed
```

Assert a stable error category or message fragment, not a full ANTLR message,
unless generator/runtime versions are locked. The public parser may reduce some
ANTLR cancellation failures to `QASM3ParsingError("parse failed")` without
line/column. A missing position is not proof that the error is non-syntactic.

Separate negative groups by layer:

- **lexical:** illegal hardware-qubit spelling (`$a`), malformed numeric tokens,
  unterminated/non-empty-string violations;
- **grammar:** missing delimiters, wrong keyword order, empty list elements,
  missing required statement body;
- **parser context:** syntactically recognized but rejected by the AST visitor,
  such as `break;` outside a loop or a nested pragma;
- **semantic/compiler:** parses successfully and must be tested by the later
  compiler stage, such as an undeclared gate name.

Do not put a semantic reject case into a grammar-negative file. It encourages a
future parser implementation to overreach and reject text for the wrong reason.

## 4. Public Python parser workflow

Use the bundled helper for routine checks:

```text
python scripts/check_syntax.py program.qasm
python scripts/check_syntax.py --source 'OPENQASM 3.1; qubit q;' --json
printf 'OPENQASM 3.1;\nqubit q;\n' | python scripts/check_syntax.py -
python scripts/check_syntax.py --normalized program.qasm
```

`-` explicitly selects stdin; omitting both a path and `--source` also selects
stdin. The helper always uses strict parsing with version enforcement. It
reports:

- the version candidate found by `parse_version`;
- a header version derived from that candidate;
- `Program.version` after successful AST construction;
- accept/reject status and diagnostic information;
- optional normalized source from `openqasm3.dumps`.

For direct API work, preserve the same pattern:

```python
from openqasm3 import parse, parse_version
from openqasm3.parser import QASM3ParsingError

detected = parse_version(source)
try:
    program = parse(source)  # strict; version checks enabled
except QASM3ParsingError as exc:
    diagnostic = {
        "message": str(exc),
        "line": exc.line,
        "column": exc.column,
    }
else:
    result = {
        "detected_version": detected,
        "ast_version": program.version,
        "statement_count": len(program.statements),
    }
```

Do not set `permissive=True` in a conformance assertion: ANTLR may recover and
produce an invalid AST while writing warnings. Do not set `ignore_version=True`
when proving version conformance. Both flags are useful only as labeled,
secondary diagnostic experiments.

## 5. Header and version matrix

At this baseline, the Python package declares `3.0` and `3.1` as supported.
Construct separate cases for:

| Source | Preliminary detection | Strict parse expectation |
|---|---:|---|
| `OPENQASM 3;` | `(3,)` | accept |
| `OPENQASM 3.0;` | `(3, 0)` | accept |
| `OPENQASM 3.1;` | `(3, 1)` | accept |
| no header | `None` | parser accepts with `Program.version is None` |
| `OPENQASM 2.0;` | `(2, 0)` | reject unsupported version |
| `OPENQASM 4.0;` | `(4, 0)` | reject unsupported version |
| `OPENQASM 3.1.2;` | `(3, 1, 2)` | reject too many components |
| statement before header | `None` | grammar rejects header in statement position |
| `OPENQASM invalid;` | `None` | grammar/lexer rejects malformed header |

The parser's acceptance of a headerless program is an implementation fact, not
a statement that every compiler or provider accepts it. For normative
source-authoring requirements, route to the language-authoring sibling.

## 6. Comments, annotations, and pragmas

### Comments

Test both the parser result and hidden-channel extraction:

```python
from openqasm3 import parse
from openqasm3.parser import get_comments

program = parse(source)
comments = get_comments(source)
assert all(set(item) == {"type", "text", "line", "column"} for item in comments)
```

Line and block comments should not add parser statements. `get_comments`
returns dictionaries with type `line` or `block`, source text including comment
markers, and one-based line/zero-based column positions.

### Annotations

Fixture dimensions:

- no command text (`@tag` followed by newline);
- opaque command text containing otherwise invalid OpenQASM punctuation;
- dotted keyword (`@namespace.name`);
- multiple annotations on separate lines;
- annotation inside a scope;
- one annotation followed by multiple statements on one later line, proving it
  attaches only to the next statement;
- two `@` sequences on one annotation line, proving the second is command text.

Preserve line endings exactly. Trimming a fixture can change mode termination.

### Pragmas

Both `pragma command` and `#pragma command` are lexed. A pragma requires a
non-empty remainder in the grammar, and the Python AST visitor requires global
scope. Its remainder is opaque to the ordinary OpenQASM token grammar. Test a
final newline and EOF termination as distinct transport cases when integrating
with editors or line-based preprocessors.

## 7. Calibration-block fixture matrix

Use paired cases that distinguish prelude parsing from body balancing:

| Case | Expected layer/result |
|---|---|
| `cal {}` | grammar accept; empty body |
| `cal { arbitrary !$ text }` | grammar accept; opaque payload |
| `cal { outer { inner } outer }` | grammar accept; balanced nesting |
| `cal { outer { inner }` | lexer/grammar reject; missing balancing brace |
| `defcal x $0 { ... }` | grammar accept if prelude tokens fit |
| malformed `defcal` argument list | grammar reject before body mode |
| brace inside inner comment/string | count as calibration-mode brace; test balance explicitly |

Do not claim that an accepted payload is valid in the selected calibration
language. The lexer only preserves a balanced opaque body.

## 8. ANTLR generation/runtime matching

The verified generated-parser set spans consecutive ANTLR 4 minors 4.7 through
4.13, represented by full generator versions `4.7.2`, `4.8`, `4.9.2`,
`4.10.1`, `4.11.1`, `4.12.0`, and `4.13.0`. The package chooses generated
Python modules by the installed runtime's **major and minor**. If that variant
is absent, importing the parser raises a clear “Missing ANTLR-generated parser”
error and lists available variants.

Use this sequence when maintaining or diagnosing a generated parser:

1. Choose one supported full ANTLR version.
2. Generate lexer, parser, listener, and visitor with that same version.
3. Install the exact same full `antlr4-python3-runtime` version.
4. Place generated package files in the layout expected by the consumer; for
   `openqasm3`, variant directories use `_4_<minor>` naming.
5. In a clean Python process, query the runtime distribution version and import
   `openqasm3.parser`.
6. Run one valid and one lexical-negative fixture before the full suite.
7. If multiple minors are shipped, repeat steps 3–6 for each supported minor.

A safe runtime probe is:

```text
python -c "from importlib.metadata import version; print(version('antlr4-python3-runtime')); import openqasm3.parser; print('parser import ok')"
```

Do not assume that “ANTLR 4” is sufficient compatibility. Do not let a package
manager silently select a different runtime version from the generator.
Project selection may be keyed by major/minor, but exact full-version matching
is the safest generation contract and avoids serialized-ATN/runtime drift.

## 9. Review checklist

A conformance change is ready for later integrated verification only when:

- every claim names its validation layer;
- every positive syntax change has an exact-tree or rule-path assertion;
- every negative fixture is minimal and paired where practical;
- strict public-parser checks pass without warning recovery;
- header/version behavior is explicit;
- line-mode and calibration-mode fixtures preserve exact text;
- ANTLR generator and Python runtime versions are recorded and matched;
- parse success is not reported as semantic, include, compiler, or execution
  success.
