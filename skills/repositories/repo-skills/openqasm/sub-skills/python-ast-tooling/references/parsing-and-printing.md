# Parsing, spans, comments, and printing

## Parse entry points and version decisions

Install the parser extra before importing the parser interface:

```bash
python -m pip install 'openqasm3[parser]'
```

Then use the high-level entry point:

```python
import openqasm3
program = openqasm3.parse(source)
```

The verified signature is:

```python
parse(input_, *, permissive=False, ignore_version=False)
```

The default is strict parsing. `permissive=True` asks ANTLR to recover from
incorrect input; the resulting AST may be invalid if recovery generated
warnings. It is useful for exploration, not acceptance or compiler input.
`ignore_version=True` bypasses the package's supported-version gate and makes no
guarantee that the result is syntactically or semantically valid for that
version.

Use `parse_version(source)` as a cheap leading-header probe. It skips leading
space and comments, requires `OPENQASM` to be the first non-comment token, and
returns a tuple such as `(3, 1)`, including tuples longer than two components
when present. It returns `None` when no syntactically plausible leading version
statement is found. It is a probe, not full parsing or conformance validation.

`openqasm3.spec.supported_versions` lists `3.0` and `3.1`. The version gate
also accepts the major-only header `OPENQASM 3;`; preserve the program's exact
header string if that distinction matters. A source reporting an unsupported
version normally raises `QASM3ParsingError`; an explicit `ignore_version=True`
experiment changes that gate only. A source without a version header is parsed
using the parser's OpenQASM 3 fallback, while the returned `Program.version`
can remain `None`.

## Errors and contextual checks

`QASM3ParsingError` is the public parser error. Its string may include an
`L<line>:C<column>:` prefix, and its `.line`/`.column` attributes are useful for
CLI diagnostics. Strict parsing catches lexer and parser failures and the AST
visitor also performs some contextual checks, such as rejecting constructs that
are only legal globally or in particular scopes. Keep these categories distinct:

1. **Language semantics:** what a valid OpenQASM construct means.
2. **Grammar acceptance:** whether the grammar accepts the token sequence.
3. **Parser contextual checks:** restrictions enforced while building this AST.
4. **Semantic/compiler validity:** name binding, types, resource rules, and pass
   invariants not supplied by this reference AST package.
5. **Provider execution:** backend compilation, scheduling, and device behavior.

Parsing proves only the first implementation-level gate; it is not a semantic
compiler or provider check.

## Spans and comments

Parsed nodes carry `ast.Span` metadata when they originate from source. Lines are
1-based and columns are 0-based. A span records start/end locations; it does not
store the original token text or all formatting details. Manually constructed
nodes normally have `span=None`, and dataclass equality intentionally ignores
spans.

Comments are collected independently:

```python
comments = openqasm3.parser.get_comments(source)
```

The verified signature is `get_comments(input_) -> List[dict]`. Each dictionary
has `type` (`'line'` or `'block'`), `text` including its marker, and 1-based
`line`/0-based `column`. Comments are not attached to ordinary AST nodes by
`parse` and are not automatically emitted by the printer. Keep the original
source or an external comment map when comments matter.

The AST is not a CST. Do not promise exact source preservation, comment
round-tripping, token-level edits, or stable whitespace based on spans.

## Printing API and normalization

For normal use:

```python
text = openqasm3.dumps(program, **options)
with open('out.qasm', 'w', encoding='utf-8') as stream:
    openqasm3.dump(program, stream, **options)
```

The verified signatures are `dumps(node, **kwargs)` and
`dump(node, file, **kwargs)`. The lower-level printer is:

```python
from openqasm3.printer import Printer
printer = Printer(
    stream,
    indent='  ',
    chain_else_if=True,
    old_measurement=False,
)
printer.visit(program)
```

- `indent` is the string used for one nesting level; `''`, spaces, and tabs are
  accepted formatting choices.
- `chain_else_if=True` (default) flattens an `else` containing an `if` into an
  `else if` form where the AST shape permits it. `False` keeps nested blocks.
- `old_measurement=False` (default) emits assignment measurement such as
  `c = measure q;`; `True` emits the OpenQASM 2-style arrow form.

These options affect spelling and layout, not a general semantic conversion.
The printer emits normalized source, omits comments, and may normalize older
accepted spellings into the current AST printer's spelling. It is not a source
formatter with concrete-syntax preservation guarantees.

## Parse-print-reparse validation

Use this invariant for a formatting-only operation:

```python
before = openqasm3.parse(source)
printed = openqasm3.dumps(before, indent='  ')
after = openqasm3.parse(printed)
```

Compare the meaningful AST structure after intentionally ignoring `.span`
metadata. Do not compare the original text, comments, or spans as if they were
stable. If a transformation changes identifiers or operators, compare the
expected structural change plus a successful strict reparse. Test each
non-default printer option that your consumer relies on, especially
`old_measurement` and `chain_else_if`.

A print failure such as `ValueError` from `properties.precedence` usually means
that an expression-shaped field contains an unsupported or malformed node; it
is not evidence that a source program failed grammar parsing. See
[troubleshooting](troubleshooting.md) for a diagnostic sequence.
