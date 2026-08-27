# Ecosystem boundaries

Use this reference when deciding whether the `openqasm` skill owns a request or
only one stage of it.

## What this skill owns

- Authoring and reviewing OpenQASM 3.0/3.1 source.
- Explaining reference grammar acceptance and designing conformance fixtures.
- Using the `openqasm3` Python AST, parser, printer, visitor, transformer,
  source spans, comments and version metadata.
- Diagnosing package/parser/ANTLR compatibility and the boundary between a
  parse result and later validation.

## What needs another implementation

| Requested result | Use this skill for | Additional system required |
|---|---|---|
| Parse a QASM 3 program | Syntax, AST and diagnostics | None beyond `openqasm3[parser]` |
| Resolve `include` files | Understand the include contract | Compiler/toolchain include search path and library files |
| Type-check names, widths and operations | Identify relevant language rules and parser limits | A specification-aware semantic analyzer/compiler |
| Optimize or lower a circuit | Preserve source/AST intent | Compiler IR and target-specific passes |
| Simulate measurement results | Prepare/validate source | Simulator that supports the used OpenQASM subset |
| Execute on a QPU | Express program and physical/calibration intent | Provider SDK, mapping, calibration, credentials and hardware access |
| Validate `cal`/`defcal` payload | Check balanced outer syntax and boundaries | The selected calibration grammar implementation |
| Use OpenPulse waveforms/ports/frames | Explain language concepts and target assumptions | Provider-supported OpenPulse grammar and hardware model |
| Convert OpenQASM 2 to 3 | Explain the destination language | A migration workflow/tool with explicit source-semantics tests |

## Selection rules

Choose `openqasm` when the request names OpenQASM, QASM 3, `stdgates.inc`,
`defcal`, OpenPulse, QASM source syntax, the reference ANTLR rules, or the
`openqasm3` Python package. It also fits unnamed tasks whose artifacts contain
`OPENQASM 3;`, `$0` hardware qubits, QASM gate modifiers, `durationof`, or an
`openqasm3.ast.Program`.

Do not choose it as the only skill when the requested deliverable is execution,
backend compilation, device calibration, complete semantic checking, or a
provider-specific circuit object. In those cases, use this skill only for the
QASM/AST boundary and select the implementation that owns the downstream
result.
