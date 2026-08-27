---
name: openqasm
description: "Use the OpenQASM 3 specification, reference grammar, and openqasm3
  Python AST toolkit to author, validate, inspect, transform, and troubleshoot
  quantum circuit intermediate-representation source."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenQASM 3

Use this repo skill when a task involves OpenQASM 3 source, QASM 3.0/3.1
syntax, quantum-circuit IR, the reference ANTLR grammar, or the `openqasm3`
Python AST/parser/printer/visitor package. It teaches authoring and reference
tooling; it does not execute circuits or replace a semantic compiler, simulator,
provider SDK, or QPU.

## Route the request

- **Write, explain, translate, or repair source**: read
  [language-authoring](sub-skills/language-authoring/SKILL.md), then its core,
  quantum, timing, directive, and example references.
- **Classify syntax or a parser failure**: read
  [grammar-conformance](sub-skills/grammar-conformance/SKILL.md),
  [grammar-guide](sub-skills/grammar-conformance/references/grammar-guide.md),
  and [syntax versus semantics](sub-skills/grammar-conformance/references/syntax-semantics-boundary.md).
- **Use Python AST APIs**: read
  [python-ast-tooling](sub-skills/python-ast-tooling/SKILL.md), then its API,
  parsing/printing, and visitor references.
- **Cross-surface workflow**: author a minimal program first, run the bundled
  syntax checker, inspect or transform it with the Python helpers, print and
  reparse, then obtain any independent semantic/compiler/provider validation.
- **Install or recover a broken environment**: read
  [troubleshooting](references/troubleshooting.md) and the nearest sub-skill
  troubleshooting reference before changing dependencies.

## Public package preflight

The language specification is useful without Python. For the reference Python
implementation, install the parser extra:

```bash
python -m pip install 'openqasm3[parser]'
```

For focused package tests, use `openqasm3[tests]`; avoid installing every extra
when only source authoring is needed. A minimal check is:

```bash
python -c "import openqasm3; from openqasm3 import spec; print(openqasm3.__version__, spec.supported_versions)"
```

The verified baseline is package `openqasm3` 1.0.1 with parser-supported
specification versions `3.0` and `3.1`. The package has no required GPU,
accelerator, simulator, or QPU backend. The API is explicitly unstable, so
inspect the installed runtime before relying on a field or signature. For a
richer, machine-readable check, run
[check_install.py](scripts/check_install.py).

## Reliable operating sequence

1. Normalize the target version, consumer, qubit model (virtual or physical),
   include/library assumptions, and whether the output is portable, parser-only,
   semantic/compiler-specific, or provider-specific.
2. Read the owning sub-skill. Keep the first non-comment version header,
   declaration order, scope, types, register shapes, and implementation
   assumptions explicit.
3. Validate a smallest complete source. Use
   [check_syntax.py](sub-skills/grammar-conformance/scripts/check_syntax.py)
   or `openqasm3.parse` with strict defaults. Parsing does not resolve includes
   or prove semantic/type correctness.
4. If using Python, inspect with
   [inspect_program.py](sub-skills/python-ast-tooling/scripts/inspect_program.py),
   apply only a conservative transformation, and use
   [rename_identifiers.py](sub-skills/python-ast-tooling/scripts/rename_identifiers.py)
   only when its lexical, non-binding-aware limits are acceptable.
5. Print and reparse normalized output. Preserve original text separately when
   comments or exact formatting matter. Obtain a semantic/compiler/provider
   check when the downstream target requires it.
6. Report the first failing layer and remaining limitations. Do not turn a
   successful parser result into a claim that a circuit can run on hardware.

## Important boundaries

- `include "stdgates.inc";` names an implementation-provided library; the
  reference parser does not resolve or execute it.
- `$0`-style physical qubits, calibration bodies, `extern` functions, timing
  values, and OpenPulse details need an implementation or target contract.
- The reference package constructs an AST and has an example visitor/transformer;
  it is not a complete name resolver, type checker, optimizer, or backend.
- For source/version alignment or a future refresh, read
  [repo-provenance](references/repo-provenance.md).
- For ecosystem fit and non-goals, read
  [ecosystem boundaries](references/ecosystem-boundaries.md).

## Runtime references

- [Cross-cutting troubleshooting](references/troubleshooting.md) covers
  installation, parser extras, ANTLR/runtime skew, source-version skew and
  validation boundaries.
- [Language authoring](sub-skills/language-authoring/SKILL.md) owns normative
  constructs and portable source patterns.
- [Grammar conformance](sub-skills/grammar-conformance/SKILL.md) owns lexer,
  parser, fixture, and syntax-layer analysis.
- [Python AST tooling](sub-skills/python-ast-tooling/SKILL.md) owns live API
  inspection, AST workflows, printing, visitors, transformers and helpers.
