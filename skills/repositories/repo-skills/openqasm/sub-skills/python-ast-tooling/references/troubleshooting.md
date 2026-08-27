# AST tooling troubleshooting

Use the following order so an import problem is not misdiagnosed as a grammar
or transformation problem.

## 1. Package and parser-extra checks

First check the package and version:

```bash
python -c "import openqasm3; print(openqasm3.__version__)"
```

The AST-only install can import `openqasm3.ast`, visitors, and the printer, but
parsing text requires the parser extra:

```bash
python -m pip install --upgrade 'openqasm3[parser]'
```

If `openqasm3` imports but has no `parse` attribute, the optional parser pieces
were not initialized. If importing the package fails while loading parser
components, preserve the original exception: it often identifies a generated
parser/runtime problem.

## 2. Missing parser symbols

Symptoms include `ImportError` for `antlr4`, `qasm3Lexer`, `qasm3Parser`, or
`qasm3ParserVisitor`, or an error saying that generated parsers are absent. Do
not work around this by importing private generated modules in an application.
Reinstall the parser extra from a compatible package distribution and verify
that a tiny strict parse works. The generated parser files are an implementation
detail of the parser extra, not part of this sub-skill's public runtime files.

## 3. Generated-parser/runtime mismatch

The package selects generated ANTLR modules based on the installed ANTLR Python
runtime's major/minor version. A mismatch can report that no generated parser
matches the runtime, expose missing lexer/parser symbols, or fail during package
initialization. Inspect the installed `antlr4-python3-runtime` version, then
install a package distribution that bundles matching generated code and runtime;
do not mix arbitrary generated files with a different runtime. Retest in a
cleanly selected Python environment if another installation shadows the package.

## 4. Version and source/API skew

Use:

```python
import openqasm3
from openqasm3 import spec
print(openqasm3.__version__, spec.supported_versions)
print(openqasm3.parse_version(source))
```

A `QASM3ParsingError` saying that a reported version is unsupported is a
version gate, not automatically a malformed grammar. `ignore_version=True` is
an explicit experiment and does not establish support. Distributions reporting
the same package version can still expose different APIs. If a remembered
signature, field, or enum differs from the installed package, trust live
`inspect.signature`, `dataclasses.fields`, and `ast.__all__` for the current
runtime and treat the discrepancy as API instability.

## 5. Constructor and enum errors

`TypeError` during construction usually means a dataclass field is missing,
misnamed, passed positionally in the wrong order, or incorrectly supplied even
though it is `init=False` (notably `span` and statement `annotations`). Inspect
`inspect.signature(type(node))` and use keyword arguments.

`KeyError` from `ast.BinaryOperator['...']`, `ast.TimeUnit['...']`, or another
enum lookup means the symbolic member is not present in this package version.
Enum names are the bracket keys, including punctuation such as `'+'` and `'**'`;
this is not the same as constructing an enum from an assumed value.

## 6. `precedence` failures

`openqasm3.properties.precedence(node)` raises `ValueError` for unsupported
node categories. Call it only on known expression nodes. A malformed AST can
reach the printer before any parser catches it; inspect the field that was
rewritten and reparse a printed fixture. The numeric precedence values are
comparison keys only and can change between releases.

## 7. Visitor context surprises

`QASMVisitor.visit` and `generic_visit` pass context only when it is truthy.
Thus `{}`, `0`, `False`, and `[]` behave like no context. Use a non-empty
sentinel/container, store state on the visitor, or override the dispatch logic.
Also verify the method spelling is exactly `visit_<ClassName>`, such as
`visit_Identifier`.

## 8. Comments and formatting disappeared

This is expected when using the AST printer. `get_comments(source)` returns
separate dictionaries, but `parse` does not attach comments to normal nodes and
`dumps` does not automatically replay them. The AST is not a CST: spans do not
restore comments, whitespace, token spelling, or exact source layout. Preserve
original text and an explicit comment map when source fidelity is required.

## 9. Invalid transformed AST or failed reparse

A transformer can delete scalar fields, splice incompatible list values, leave
an unresolved name, or create a shape the printer cannot handle. Diagnose in
this order:

1. Reproduce from a tiny strict-parsed fixture.
2. Count/inspect the concrete node classes before and after the pass.
3. Check that required dataclass fields still exist and list elements have the
   expected node types.
4. Print to a string, then strict-parse that string before writing it anywhere.
5. Compare AST structure while ignoring spans; inspect the emitted line and
   `QASM3ParsingError.line`/`.column` on failure.
6. Route grammar acceptance questions to
   [grammar-conformance](../../grammar-conformance/SKILL.md) and semantic/name
   binding questions to the appropriate compiler workflow rather than treating
   a successful reparse as full validity.

For identifier renames, reject a target already present elsewhere in the AST,
avoid textual replacement, and remember that raw calibration bodies, comments,
and string literals are not `Identifier` nodes. The bundled rename helper uses
these conservative rules and will not silently overwrite an input path.
