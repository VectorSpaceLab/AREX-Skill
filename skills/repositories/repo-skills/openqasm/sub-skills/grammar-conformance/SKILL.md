---
name: grammar-conformance
description: "Reason about OpenQASM 3 lexical and syntactic conformance, parser
  acceptance, diagnostics, and fixture design without conflating parsing with
  semantic or execution validity."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Grammar conformance

Use this sub-skill when the question is **is this valid syntax**, **which grammar
rule accepts this**, an ANTLR parse error, a parser accept/reject dispute, or a
conformance fixture. This is the grammar-and-parser boundary for the OpenQASM 3
reference implementation.

## Route before acting

- Use [grammar-guide.md](references/grammar-guide.md) for tokens, lexer modes,
  parser rules, precedence, lists, annotations, and calibration blocks.
- Use [conformance-workflows.md](references/conformance-workflows.md) for
  positive/negative fixtures, exact-tree assertions, diagnostics, and ANTLR
  generation/runtime matching.
- Use [syntax-semantics-boundary.md](references/syntax-semantics-boundary.md)
  before classifying a failure. A successful parse is not a type check,
  include resolver, compiler validation, or provider execution.
- Use [troubleshooting.md](references/troubleshooting.md) for dependency,
  version, mode, diagnostic, and calibration failures.
- Run [scripts/check_syntax.py](scripts/check_syntax.py) for a bounded public
  `openqasm3` parse check. It reads exactly one path, `--source`, or stdin.

If the question is about the meaning of a language construct or how to author a
useful OpenQASM program, route to [language-authoring](../language-authoring/SKILL.md).
If it is about Python AST classes, visitors, transformers, or printing, route to
[python-ast-tooling](../python-ast-tooling/SKILL.md).

## Boundary

Own lexical rules, parser-rule acceptance, diagnostics, and conformance fixture
methodology. Do not use this sub-skill for normative source design, complete
semantic/type checking, lowering, optimization, execution, provider
compilation, or generated-parser release/maintenance workflows. Those later
layers may consume a syntax result but must not be inferred from it.

## Known parser contract

The public Python parser exposes:

```text
parse(input_: str, *, permissive=False, ignore_version=False) -> Program
parse_version(prog: str) -> Optional[Tuple[int, ...]]
get_comments(input_: str) -> List[dict]
```

The inspected package is `openqasm3` 1.0.1. Its declared supported versions
are `3.0` and `3.1`. `parse` returns an AST `Program`, not an ANTLR concrete
syntax tree. `parse_version` only detects a potential first `OPENQASM` header;
it can return a version for input that later fails parsing or version policy.

## Bounded conformance workflow

1. **State the layer.** Decide whether the claim concerns a token, grammar rule,
   parser contextual check, semantic/type rule, include resolution, or provider
   execution. Record the layer in the fixture or diagnosis.
2. **Minimize the input.** Reduce to one header, statement, expression, list,
   annotation, pragma, or calibration block. Preserve the exact line endings
   when testing line-mode constructs.
3. **Check the header separately.** Call `parse_version` first. A valid-looking
   header must be the first non-comment construct. With normal parsing,
   unsupported versions and more than two version components are rejected;
   `ignore_version=True` is only a diagnostic experiment.
4. **Parse strictly.** Use `parse(source)` or the helper with default strict
   behavior. Capture success, exception class/message, line, and column. Do
   not use `permissive=True` to prove conformance.
5. **Inspect the result at the right depth.** For AST shape or `dumps`, route to
   the Python AST sub-skill. For exact ANTLR rule acceptance, compare the
   expected rule path/tree in a grammar harness generated from the same grammar
   and runtime minor.
6. **Add a paired negative.** Change only the suspected token or delimiter and
   assert rejection. Keep lexical, grammar, contextual-parser, and semantic
   cases in separate fixture groups.
7. **Report limits.** Say explicitly whether includes were resolved, types were
   checked, a compiler accepted the program, or a provider executed it. The
   grammar parser does none of those jobs.

## High-value decisions

- `include "name";` and `defcalgrammar "name";` require a non-empty quoted
  string token, but parsing does not open or resolve that name.
- A bare `OPENQASM 3;` or `OPENQASM 3.0;` header is accepted. No header is also
  accepted by this parser and produces an AST with no version; it is not proof
  that a downstream tool accepts headerless input.
- Comments are hidden from the parser tree but are available through
  `get_comments`. Newlines normally separate tokens only where grammar needs
  them; annotations and pragmas explicitly consume the rest of their line.
- Trailing commas are intentionally accepted in the list rules documented in
  the grammar guide. An empty item before a comma is not thereby accepted.
- `cal` and `defcal` bodies are opaque to the OpenQASM grammar except for
  balanced braces. Their payload is not pulse-language validation.
- Some failures after grammar recognition are raised while building the AST:
  for example, `break;` outside a loop, a pragma outside global scope, a
  non-unitary operation in a gate, or invalid built-in argument counts. Label
  these parser-context checks, not grammar rejection.

## Fixture acceptance checklist

A useful conformance fixture has a stable id, minimal source, expected layer,
expected accept/reject result, and expected observation. Positive grammar
fixtures should name the top rule (for example `expressionStatement`,
`includeStatement`, `gateStatement`, or `calStatement`) and, where useful, the
nested rule path. Negative fixtures should identify the first deliberately
invalid token or delimiter and avoid relying on an unstable full ANTLR error
string. Diagnostic tests may assert line/column and a stable message fragment.

Do not copy generated parser files into this runtime skill. Do not add native
test output, reports, caches, or review artifacts here; place only reusable
routing material, references, and the bounded helper in this subtree.
