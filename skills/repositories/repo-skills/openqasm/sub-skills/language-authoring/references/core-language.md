# Core language

This reference covers source meaning and authoring patterns for the core
OpenQASM 3.0/3.1 language. A parser can accept a construct before a semantic
checker or target compiler can validate its types, scopes, widths, or runtime
support.

## Program envelope and names

- Comments are `//` to end of line or `/* ... */` blocks.
- The first non-comment statement may be `OPENQASM 3;`, `OPENQASM 3.0;`, or
  `OPENQASM 3.1;`. Treat the selected version as part of the program contract.
  Do not put a second version statement later.
- Identifiers begin with an ASCII letter, `_`, or an eligible Unicode letter;
  later characters may also be decimal digits. Do not use reserved words or
  built-in names for user declarations.
- Symbols must be declared before use. There is no forward declaration or
  mutual recursion for gates and subroutines.
- `include` textually extends the global scope at its location. OpenQASM does
  not define a namespace for included files, so declaration order and name
  collisions matter. File lookup is an implementation concern; parse success
  alone does not establish that an include can be resolved.

A portable starting envelope is:

```qasm
OPENQASM 3.1;
include "stdgates.inc";

qubit q;
bit result;
reset q;
h q;
result = measure q;
```

The include is a reference to an implementation-provided standard library, not
an instruction to ship a replacement file with a program.

## Scope and declaration order

Global scope contains qubits, arrays, gates, subroutines, calibration grammar
selection, and global directives. Classical variables declared in a block are
visible through that block and nested control-flow blocks, subject to shadowing
rules. Gate bodies have their own parameter/argument scope and can only use
those arguments plus visible compile-time constants and previously declared
gates. Subroutine arguments and local classical variables are scoped to the
subroutine. A `for` iteration variable is scoped to its loop body; each
`case`/`default` body of `switch` creates a block scope.

Qubits and arrays are global declarations. Do not declare either inside a
`gate`, `def`, `switch` case, or ordinary control-flow block. A classical local
may shadow an outer variable in an inner block, but duplicate declarations at
the same scope are not a repair for a shadowing problem. `const` values, gates,
and subroutines remain visible in nested scopes where ordinary runtime values
may not be visible inside gate/subroutine definitions.

Use this scope checklist before diagnosing a type error:

1. Was the name declared earlier in the same effective global/include scope?
2. Is the use inside the declaration's lifetime and visibility region?
3. Is a gate body trying to access a global runtime variable or index its
   formal qubit argument?
4. Is a declaration placed where only statements are allowed?
5. Is a `break`/`continue` actually nested in a `for` or `while`?

## Quantum and classical declarations

### Qubits

```qasm
qubit q;              // one virtual qubit
qubit[4] data;        // fixed virtual register, indices 0..3
const uint N = 2;
qubit[N] ancilla;     // width is compile-time constant
```

Virtual qubits begin in an undefined state; use `reset` when a known `|0>`
state is required. Registers cannot be resized. `$0`, `$1`, and so on denote
physical qubits supplied by a target topology. Physical qubits are global
references and must not be declared; they cannot be used as formal arguments
inside a `gate`. A source that mixes `q` and `$0` may be syntactically valid but
is a partially constrained, non-physical circuit and requires target-specific
acceptance.

### Classical values

The scalar/register forms most useful in portable source are:

- `bit` and `bit[n]` for measurement values; `bit` is distinct from `bit[1]`.
- `bool` for byte-aligned Boolean values.
- `int[n]` and `uint[n]` for signed and unsigned fixed-width integers; width
  may be omitted for target machine precision.
- `float[n]` for floating-point values; width may be omitted.
- `angle[n]` for modulo-`2*pi` angle representations.
- `complex[float[n]]` for complex values, with `real()` and `imag()`.
- `duration` and its stretch subtype for timing, as described in the timing
  reference.

Declare one variable at a time; comma-separated declarations are not the
portable form. An uninitialized classical variable is undefined. Arrays use a
classical base type and fixed dimensions, for example:

```qasm
bit[4] flags = "0000";
int[16] count = 0;
float[64] angle_value = pi / 4;
angle[32] phase = pi / 2;
array[int[16], 3] weights = {2, 4, 8};
array[float[32], 2, 2] matrix = {{1.0, 0.0}, {0.0, 1.0}};
```

`bit`, `bit[n]`, `stretch`, and quantum types are not valid array base types.
Arrays are global, static, non-resizable, and non-reshapable. A dimension may
be zero, but a zero-sized array cannot be indexed. Array dimensions are at most
seven in the language specification.

## Constants, literals, and expressions

`const T name = expression;` requires an initialized compile-time expression.
Every scalar literal is `const`. Widths for `qubit[n]`, `bit[n]`, integer,
float, angle, and array dimensions require compile-time unsigned/integer values
where the type rules demand them.

Literal families include decimal/hex/octal/binary integers, decimal or
scientific floats, `true`/`false`, bit strings such as `"0101"`, and timing
literals such as `100ns`, `2us`, `1ms`, `1s`, or backend-dependent `8dt`.
Underscores improve readability inside numeric and bit-string literals. Complex
imaginary literals use a numeric component followed by `im`, for example
`1.5 + 2im`.

Built-in compile-time constants are `pi`/`π`, `tau`/`τ`, and
`euler`/`ℇ`. Compile-time mathematical functions include `sin`, `cos`, `tan`,
`arcsin`, `arccos`, `arctan`, `sqrt`, `exp`, `log`, `floor`, `ceiling`,
`mod`, `popcount`, `rotl`, and `rotr`, subject to their input overloads and
compile-time arguments. Do not assume a target supports the same functions on
runtime values.

Assignment uses `=` and compound assignments such as `+=`, `-=`, `*=`, `/=`,
`%=`, `**=`, bitwise `&=`, `|=`, `^=`, `<<=`, and `>>=` where the operand types
support them. Comparison operators are `>`, `>=`, `<`, `<=`, and `==`; logical
operators are `&&`, `||`, and `!`. Integer/bit/angle operations also include
bitwise `~`, shifts, `&`, `|`, and `^`. Use parentheses around mixed arithmetic
when the intended precedence is not obvious.

`bit` and `bool` are interchangeable in expression contexts, but `bit[n]` is
a register and is not `bit`. Register comparisons, broadcast shapes, and
switch controlling values must use the required scalar/register type rather
than relying on a same-width assumption.

## Casts and type repairs

Use a type name as an explicit cast: `int[16](value)`, `uint(value)`,
`float[64](value)`, `angle[32](value)`, `bit[8](value)`, or `bool(value)`.
Constness propagates through a cast only when the input is `const`; a call to a
user `def` or `extern` is not a compile-time constant.

Portable high-value rules:

- Standard arithmetic types (`bool`, `int`, `uint`, `float`, `complex`) follow
  promotion/conversion rules similar to C99. In mixed expressions the lower
  rank is promoted to the higher rank where an allowed promotion exists.
- Scalar `bit` and `bool` interoperate. `bit[n]` to/from integer or angle keeps
  the specified width; if widths differ, slice explicitly rather than assuming
  truncation or extension.
- Integer-to-Boolean means nonzero; integer-to-floating conversion follows
  ordinary numeric conversion, with target-width loss potentially
  implementation-specific.
- Floating-point to `angle[n]` rounds to the nearest representable modulo
  `2*pi` value, with the documented tie behavior. NaN and infinities are not
  valid angle values.
- `duration` is not cast to or from ordinary numeric types. Dividing one
  duration by another produces a machine-precision float; use this only when
  that ratio is intended.
- Qubits are not classical values and cannot be cast.

When an assignment fails, first inspect both exact widths and special types;
do not repair it by adding a broad cast that changes bit ordering or runtime
precision. Use `int[n](bit[n])` for a deliberate little-endian bit-pattern
reinterpretation and use a slice when the widths do not match.

## Indexing, slicing, aliasing, and references

Quantum and bit registers support scalar indexing and index sets:

```qasm
qubit[6] q;
bit[6] b;
let endpoints = q[{0, 5}];
let middle = q[1:4];       // inclusive range
let reverse = q[5:-1:-1];
let joined = q[0:2] ++ q[3:5];
```

Ranges are inclusive and use `start:stop` or `start:step:stop`; a step of zero
is invalid. Index sets may be runtime-dependent where the target and operation
allow it. A register slice is a reference to its original register. Physical
qubits cannot be aliased because they are not declarations. Do not concatenate
a register with part of itself.

Arrays use integer indices, negative indices from the end, and comma-separated
multi-dimensional access such as `matrix[0, 1]`. Array slices preserve array
shape and assignments require matching type and shape. Array concatenation
copies values rather than creating a quantum-style view; materialize a named
array before passing a concatenation to a subroutine.

Only array parameters use explicit reference qualifiers in a subroutine or
extern signature:

```qasm
def sum_first(readonly array[int[16], #dim = 1] values) -> int[16] {
  int[16] total = 0;
  for int i in [0:1] {
    total += values[i];
  }
  return total;
}
```

A `readonly` reference cannot update the caller's array; `mutable` can update
it. Multiple overlapping mutable references are forbidden even when a compiler
cannot always detect the overlap. `sizeof(values)` and `sizeof(values, dim)`
query array dimensions; a specified-shape reference can produce a `const uint`,
while an unspecified-shape reference produces a runtime `uint`.
