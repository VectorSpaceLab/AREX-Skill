# `openqasm3` API reference

This reference describes the verified Python API baseline. The package reports
version `1.0.1`; `openqasm3.spec.supported_versions` is `['3.0', '3.1']`, and
`openqasm3.ast.__all__` currently contains 82 public AST exports. The API is
explicitly unstable, so inspect the installed runtime when building reusable
code rather than treating these details as a permanent compatibility promise.

## Entry points

```python
import openqasm3
from openqasm3 import ast, spec
from openqasm3.parser import QASM3ParsingError

openqasm3.__version__       # '1.0.1' in the verified baseline
spec.supported_versions     # ['3.0', '3.1']
openqasm3.parse(text, permissive=False, ignore_version=False)
openqasm3.parse_version(text)
openqasm3.dump(node, file, **kwargs)
openqasm3.dumps(node, **kwargs)
```

`parse` returns an `ast.Program`. The parser extra is needed for parser imports;
AST construction, traversal, and printing should not be confused with parser
availability. `QASM3ParsingError` exposes `.line` and `.column` when the error
has a source position.

## Dataclass conventions

`QASMNode` is the base dataclass. Its `span` field is `init=False`, defaults to
`None`, and is excluded from dataclass equality (`compare=False`). `Span` has
four constructor fields:

```python
ast.Span(start_line, start_column, end_line, end_column)
```

The parser follows the ANTLR convention: lines start at 1 and columns at 0.
Parsed nodes generally receive spans; manually created nodes generally do not.
A span is metadata and does not preserve the original token stream, spacing, or
comments.

The verified `Program` signature is:

```python
ast.Program(statements, version=None)
```

Its dataclass fields include `span`, `statements`, and `version`; only the last
two are constructor fields. Prefer keyword arguments for nontrivial nodes and
use `dataclasses.fields(node)` or `inspect.signature(type(node))` when a pass
must support multiple package revisions.

A minimal manually constructed tree is:

```python
from openqasm3 import ast, dumps

program = ast.Program(
    statements=[
        ast.QubitDeclaration(
            qubit=ast.Identifier('q'),
            size=ast.IntegerLiteral(2),
        )
    ],
    version='3.1',
)
text = dumps(program)
```

`Statement.annotations` is an `init=False` list. Code constructing statement
nodes must not pass it to the generated constructor; set it after construction
only when annotations are intentionally part of the tree. Leaf classes such as
`BoolType`, `DurationType`, `StretchType`, `BreakStatement`, and
`ContinueStatement` are instantiated with no payload. Dataclass construction
checks Python field shape, not all OpenQASM semantic constraints.

## Useful node-family map

Use `isinstance` against these base classes or concrete classes rather than
matching repr strings:

- **Root and statements:** `QASMNode`, `Program`, `Statement`,
  `CompoundStatement`, `Pragma`, `Include`, declarations, assignments,
  branching/loop/switch statements, and `SubroutineDefinition`.
- **Expressions:** `Expression`, `Identifier`, unary/binary expressions,
  literals, `FunctionCall`, `Cast`, `IndexExpression`, `Concatenation`,
  `SizeOf`, and `DurationOf`.
- **Classical types and values:** `ClassicalType`, `IntType`, `UintType`,
  `FloatType`, `AngleType`, `BitType`, `BoolType`, `ComplexType`,
  `ArrayType`, `ArrayReferenceType`, `DurationType`, and `StretchType`.
- **Quantum operations:** `QuantumStatement`, `QuantumGate`,
  `QuantumGateDefinition`, `QuantumGateModifier`, `QuantumPhase`,
  `QuantumNop`, `QuantumMeasurement`, `QuantumCallExpression`,
  `QuantumMeasurementStatement`, `QuantumReset`, `QuantumBarrier`,
  `QubitDeclaration`, and `DelayInstruction`.
- **Declarations and control:** `ClassicalDeclaration`, `ConstantDeclaration`,
  `IODeclaration`, `ExternDeclaration`, `ClassicalArgument`,
  `QuantumArgument`, `ReturnStatement`, `ForInLoop`, `WhileLoop`,
  `BranchingStatement`, `SwitchStatement`, and `Box`.
- **Indexing and structural values:** `IndexedIdentifier`, `DiscreteSet`,
  `RangeDefinition`, `ArrayLiteral`, and `AliasStatement`.
- **Calibration/raw payloads:** `CalibrationDefinition`,
  `CalibrationGrammarDeclaration`, and `CalibrationStatement`. Their raw
  calibration bodies are strings, not recursively parsed ASTs.

The full export list is available at runtime as `ast.__all__`; the map above is
intended to guide workflows without freezing every constructor signature.
`QuantumCallExpression` is present as `ast.QuantumCallExpression` and produced
by the parser, but is not listed in `ast.__all__` in the verified baseline—an
example of why explicit imports and compatibility probes matter.

## Enums and construction

Enums are created with symbolic member names. Operator names include punctuation,
so use bracket lookup:

```python
ast.BinaryOperator['+']
ast.UnaryOperator['-']
ast.AssignmentOperator['+=']
ast.GateModifierName['ctrl']
ast.IOKeyword['output']
ast.TimeUnit['ns']
ast.AccessControl['readonly']
```

Do not assume that `ast.BinaryOperator('+')` is equivalent: enum value lookup
and member-name lookup are different operations here. If accepting user input,
validate the key and catch `KeyError`; unknown members are an API/version error,
not a semantic diagnosis.

Common field shapes include `Identifier.name: str`, literal `.value` fields,
`BinaryExpression(op, lhs, rhs)`, `UnaryExpression(op, expression)`,
`QuantumGate(modifiers, name, arguments, qubits, duration=None)`, and
`ClassicalAssignment(lvalue, op, rvalue)`. Indexed identifiers store a `name`
and a list of index elements; an index element can itself be a discrete set or a
list of expressions/ranges. Inspect the concrete node before recursively
assuming every child is a direct `QASMNode`.

## Precedence and API stability

`openqasm3.properties.precedence(node)` returns a comparable integer for
supported expression categories. The number itself has no stable meaning. It
raises `ValueError` for unsupported node categories, so call it only on
expressions whose printer behavior you understand. A malformed or newly added
expression category can therefore fail during printing even if Python
construction succeeded.

Treat node classes, field order, enum members, parser behavior, and printer
normalization as versioned implementation details. For a library pass, pin a
compatible package range, introspect at startup where useful, and keep a
parse-print-reparse smoke test in the consumer's own validation process.
