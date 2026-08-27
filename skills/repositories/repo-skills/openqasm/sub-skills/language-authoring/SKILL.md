---
name: language-authoring
description: "Write, review, translate, and repair OpenQASM 3.0/3.1 programs,
  including circuit language, timing intent, calibration structure, typed I/O,
  and standard-library use."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenQASM language authoring

Use this sub-skill when the task is to write or explain OpenQASM 3.0/3.1
source, translate circuit pseudocode, select standard gates, or repair a
program involving classical control, timing, calibration, or pulse concepts.
The language baseline is OpenQASM 3.1. Keep the requested version explicit;
the reference Python parser commonly accepts both `3.0` and `3.1`.

## Choose the right boundary

- Use the rules and patterns in the bundled references for language meaning,
  source design, and author-level repairs.
- Route lexer/parser-rule questions, a parse failure, or a syntax-versus-
  context diagnosis to [grammar-conformance](../grammar-conformance/SKILL.md).
- Route Python `openqasm3` parsing, AST construction, visitors, transformers,
  printing, or helper-code questions to
  [python-ast-tooling](../python-ast-tooling/SKILL.md).
- Do not promise simulator or QPU execution, provider compilation, pulse
  calibration values, semantic compiler implementation, OpenQASM 2 migration,
  or release/governance work.

## Authoring contract

1. Ask for the target language version, intended consumer, virtual versus
   physical qubits, and whether the output must be portable source, a parser
   fixture, or a provider-specific program.
2. Start with comments, then an optional first non-comment `OPENQASM M.m;`
   statement. Use one version statement only. Put global `include`,
   `defcalgrammar`, and `pragma` statements at global scope.
3. Declare every symbol before use. Declare virtual qubits as `qubit` or
   `qubit[n]`; never declare physical `$n` qubits. Declare classical values one
   variable at a time and make width constants `const` when a type or index
   requires compile-time knowledge.
4. Separate the four checks: textual grammar acceptance, parser contextual
   checks, language semantic/type validity, and target/provider execution.
   Passing one does not prove the next.
5. Validate the smallest complete program first. Then add includes, custom
   gates, aliases, control flow, timing, and calibration one layer at a time.
   Preserve a versioned minimal reproducer when repairing a failure.

## Fast decision guide

- Need a unitary circuit operation? Use a standard gate or a preceding `gate`
  definition. A `gate` defines unitary meaning; it does not choose hardware
  implementation.
- Need classical feed-forward? Measure into `bit`/`bit[n]`, then use `if`,
  `while`, `for`, or integer-only `switch`. Use `break` and `continue` only
  inside a loop; use `end` for immediate termination.
- Need ordered multi-qubit circuit intent? Prefer an explicit `for` loop when
  order matters. Register gate broadcasting requires equal register lengths
  and promises commuting expanded operations.
- Need a view of registers? Use `let` aliases and index sets. Use `array` only
  for global, statically shaped classical data and pass it to `def`/`extern`
  with an explicit `readonly` or `mutable` reference contract.
- Need scheduling intent? Use `duration`, `stretch`, `delay[...]`, `box`,
  `barrier`, `nop`, and `durationof(...)`; these describe timing constraints,
  not a backend's measured gate durations.
- Need pulse-level work? Use `defcalgrammar`, `cal`, and `defcal` only with a
  target's calibration grammar and physical-qubit mapping. Keep provider
  names, waveform templates, and values outside portable claims.
- Need an opaque classical or pulse operation? Declare an `extern` signature;
  its implementation, linkage, latency, and runtime support are outside the
  language text.

## Compact review workflow

1. Normalize the goal and classify each requested construct as portable
   language, parser-only illustration, semantic/compiler-dependent, or
   provider-dependent.
2. Read the relevant bundled reference before editing. Check declaration order,
   scopes, types, register shapes, casts, qubit identity, and version/include
   assumptions.
3. Write a self-contained minimal source. Name every input/output and choose
   explicit measurement destinations. Avoid undefined implementation externs
   unless the example is intentionally marked dependent.
4. Run a parser check for grammar/context acceptance, then a semantic/compiler
   check if one is available. Check include resolution separately; parsing an
   `include` line does not prove that the named file exists or has the expected
   definitions.
5. For timing or calibration, record the required target assumptions and
   verify definite durations, physical operands, and provider-owned symbols.
   Never infer execution from a successful parse.
6. When repairing, report the first failing layer, the minimal change, and any
   remaining target-specific limitation. Use the troubleshooting reference for
   symptom-to-repair paths.

## Reference map

- [Core language](references/core-language.md): declarations, scope, types,
  literals, expressions, casts, arrays, aliases, and indexing.
- [Quantum workflows](references/quantum-workflows.md): gates, modifiers,
  broadcasting, measurement, reset, flow control, subroutines, and externs.
- [Timing, calibration, and pulse](references/timing-calibration-and-pulse.md):
  timing constructs, calibration boundaries, and OpenPulse concepts.
- [Directives, I/O, and standard library](references/directives-io-and-standard-library.md):
  pragmas, annotations, typed I/O, include contracts, and standard gates.
- [Example patterns](references/example-patterns.md): compact complete patterns
  with portability labels and validation assumptions.
- [Troubleshooting](references/troubleshooting.md): actionable diagnosis for
  scope, type, qubit identity, include, timing, calibration, and execution
  confusion.
