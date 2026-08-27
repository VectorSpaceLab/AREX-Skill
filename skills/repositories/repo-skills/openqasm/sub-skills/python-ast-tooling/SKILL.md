---
name: python-ast-tooling
description: "Use openqasm3 from Python to parse and print OpenQASM 3, construct
  and inspect its AST, traverse or conservatively transform nodes, and validate
  compiler-pass scaffolding with parse-print-reparse checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python AST tooling

Use this sub-skill when the task mentions `openqasm3`, Python AST nodes, `parse`,
`dumps`, source spans or comments, AST visitors, transformers, identifier
rewrites, or a small compiler-pass scaffold. It covers the reference Python
API, not a complete semantic compiler or a provider toolchain.

## Route the work

- For normative language design, language-level idioms, or practical program
  patterns, hand off to [language-authoring](../language-authoring/SKILL.md).
- For lexical rules, grammar acceptance, parser conformance fixtures, and the
  distinction between syntax and parser contextual checks, hand off to
  [grammar-conformance](../grammar-conformance/SKILL.md).
- Do not use this skill for simulator/QPU execution, provider compilation,
  OpenQASM 2 migration, semantic analysis frameworks, or repository maintenance.

Read the focused references before an expert workflow:

1. [api-reference](references/api-reference.md) for node families, dataclasses,
   enums, signatures, and version instability.
2. [parsing-and-printing](references/parsing-and-printing.md) for parser modes,
   spans, comments, normalized output, and round trips.
3. [visitors-and-transformers](references/visitors-and-transformers.md) for
   dispatch, context, mutation, deletion, splicing, and safe rewrites.
4. [troubleshooting](references/troubleshooting.md) when imports, generated
   parser files, versions, construction, or transformed output fail.

## Install and smoke-test

The AST and printer are available from the `openqasm3` package. Install the
parser extra for parsing text:

```bash
python -m pip install 'openqasm3[parser]'
```

Confirm the runtime rather than assuming a remembered API:

```python
import inspect
import openqasm3
from openqasm3 import ast, spec

print(openqasm3.__version__, spec.supported_versions)
print(inspect.signature(openqasm3.parse))
print(len(ast.__all__))
```

The current verified baseline is package version `1.0.1`, with specification
versions `3.0` and `3.1` supported by the parser. The AST API is explicitly
unstable; if a signature or node field differs, use the installed runtime's
introspection and then record the discrepancy.

## Standard workflow

1. **Acquire text safely.** Read a file or an in-memory string. Do not treat
   comments as AST nodes; collect them separately if they matter.
2. **Preflight the version.** Call `openqasm3.parse_version(text)` when choosing
   a parser or diagnosing a source. It returns an integer tuple or `None`.
3. **Parse strictly first.** Call `openqasm3.parse(text)` with defaults. Use
   `permissive=True` only for exploratory recovery, and treat any recovered AST
   as potentially invalid. Use `ignore_version=True` only for deliberate
   compatibility experiments, never as proof of conformance.
4. **Inspect or transform.** Use dataclass fields and `QASMVisitor`/
   `QASMTransformer`; do not assume a binding or semantic symbol table exists.
5. **Print and validate.** Use `openqasm3.dumps(program, ...)`, then parse the
   result again. Compare AST structure after deliberately ignoring spans when
   testing formatting-only changes. A successful reparse proves grammar/parser
   acceptance, not semantic or provider validity.
6. **Report boundaries.** Separate normative language meaning, grammar
   acceptance, parser contextual checks, semantic/compiler validity, and
   provider execution in the result.

## Smallest useful API map

- `openqasm3.ast`: dataclass AST nodes, enums, `Span`, and base classes.
- `openqasm3.parse` and `openqasm3.parser.parse`: text to `ast.Program`.
- `openqasm3.parse_version`: leading version probe.
- `openqasm3.parser.get_comments`: separate line/block comment extraction.
- `openqasm3.dump`/`dumps`: AST to normalized text.
- `openqasm3.printer.Printer`: configurable visitor-backed printer.
- `openqasm3.visitor.QASMVisitor`: read-only traversal base.
- `openqasm3.visitor.QASMTransformer`: in-place rewrite base.
- `openqasm3.properties.precedence`: expression precedence comparison only.

For repeatable inspection, use `scripts/inspect_program.py`. For a deliberately
narrow rename demonstration, use `scripts/rename_identifiers.py`; it refuses
obvious global collisions, reparses before success, and never silently
replaces the input file.

## Guardrails

- Constructors make structurally shaped nodes; they do not establish all
  language semantics or name binding.
- Parsed nodes normally have spans; newly constructed nodes normally do not.
  Spans are source metadata, not a concrete-syntax tree.
- Printing drops comments and normalizes whitespace/formatting. Preserve the
  original text separately when comments or exact formatting are requirements.
- A transformed AST can still be invalid, incomplete, or semantically wrong;
  always print/reparse and run the appropriate grammar/conformance and semantic
  checks owned by other workflows.
