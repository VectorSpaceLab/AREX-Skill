# Language-authoring troubleshooting

Classify the failing layer before changing source:

1. **Lexical/grammar:** tokens, punctuation, or statement shape are invalid.
2. **Parser context:** the parser can recognize the shape but rejects placement,
   declaration order, version, or contextual constraints.
3. **Language semantics:** names, types, widths, scopes, qubit identity,
   control-flow legality, or timing meaning are invalid.
4. **Compiler/provider:** the source is meaningful but the consumer lacks a
   definition, backend feature, calibration, or runtime support.
5. **Execution:** only a successful target compilation and run can establish
   observed behavior.

Record the first layer and keep a minimal reproducer. Do not repair a provider
failure by changing a mathematically correct gate into a guessed vendor name.

## Headers, names, and scopes

| Symptom | Likely cause | Repair and validation |
|---|---|---|
| `OPENQASM` is rejected or version behavior is surprising | Version is not the first non-comment statement, has a second occurrence, or the consumer supports a different version | Put one `OPENQASM 3.0;` or `OPENQASM 3.1;` first; reparse with the requested version and inspect the consumer's supported versions |
| Name is undefined | Declaration comes after use, include was not resolved, or a gate/subroutine was assumed to be forward-declared | Move the declaration/include earlier; resolve the file separately; do not rely on forward declarations |
| Duplicate or reserved identifier error | Same-scope redeclaration, include collision, or a reserved/built-in name | Rename the local symbol or isolate a deliberate shadow in an inner block; check included names |
| `include`, `array`, `pragma`, or `defcalgrammar` rejected in a block | Global-only declaration/directive | Move it to global scope and check textual include order |
| Local variable disappears after a block/loop | Normal block or iteration-variable scope | Return or assign the value before leaving scope; declare a destination in the enclosing scope |
| Qubit/array declaration rejected inside `def`, `gate`, or `switch` case | Qubits and arrays are global; case bodies cannot declare globally scoped entities | Declare them globally before the control-flow construct; keep case-local classical scratch values only |

## Types, casts, arrays, and indexing

| Symptom | Likely cause | Repair and validation |
|---|---|---|
| Width expression rejected | Width uses a runtime value rather than a `const` compile-time integer | Declare `const uint SIZE = ...;` and use it; do not make a runtime size drive a type |
| `bit` and `bit[1]` do not assign | Scalar and one-element register are distinct | Use a scalar destination for a scalar measurement or explicitly choose the register form and matching measurement shape |
| Register assignment/measurement shape mismatch | Source and destination widths differ or scalar/register forms were mixed | Index or slice explicitly; verify inclusive range and exact resulting width |
| Cast from `float`/`bit`/`angle` is rejected | Special-type cast is not allowed, widths differ, or precision change needs a slice | Use an allowed explicit cast; slice before a width-changing bit/angle conversion; do not cast qubits or duration |
| `const` initialization fails | Expression contains a runtime value or a subroutine/extern result | Keep the expression literal/`const` and use only compile-time functions; make the destination non-const if runtime is intended |
| Array declaration fails | Invalid base type, non-global placement, negative dimension, or shape mismatch | Use a supported classical base (`int`, `uint`, `float`, `complex`, `angle`, `bool`, or `duration`), non-negative fixed dimensions, and a global declaration |
| Array element update fails | Negative index is outside the array, zero-sized dimension is indexed, or slice shape differs | Check bounds and dimensions; ensure assigned array/slice has identical type and shape |
| Array reference call fails | Missing `readonly`/`mutable`, wrong `#dim`, or a concatenation was passed inline | Add the reference qualifier and correct rank/shape; materialize a concatenation in a named array before the call |
| Alias cannot be formed | Physical qubit was used, index set is empty/invalid, or a register was concatenated with part of itself | Alias declared virtual registers only; check inclusive ranges, nonzero step, and distinct source regions |
| Runtime register indexing is rejected | Consumer requires `const` register indices | Use a compile-time index, or consult the consumer's explicitly supported dynamic-indexing semantics |

## Gates, operands, and measurements

| Symptom | Likely cause | Repair and validation |
|---|---|---|
| Gate name is undefined | Missing `stdgates.inc` or vendor include, wrong version, or call precedes definition | Include the correct library at global scope; check resolution and gate signature; move custom definition before use |
| Gate body rejects a declaration/measurement | `gate` is a unitary definition, not a general subroutine | Move classical/measurement logic to `def`; keep gate bodies to built-in or previously defined gates and allowed quantum loops |
| Gate formal is indexed in its body | Gate arguments are formal identifiers, not indexable registers in the definition body | Pass the desired element at the call site or use a subroutine with an appropriate argument |
| Modifier has wrong arity | `ctrl`, `negctrl`, or a chain prepended controls but the call still has the old operand count | Count controls plus base operands; use `ctrl(n)` only with a compile-time positive count |
| Broadcast call is rejected | Register operands have unequal length or expanded gates do not satisfy the broadcast promise | Make all broadcast registers equal length or replace the call with an explicit ordered `for` loop |
| `measure q -> b` fails | Destination and source are not both compatible register/scalar forms | Prefer `b = measure q;` and compare exact shapes; use a scalar bit for one qubit |
| `reset`/`barrier`/`nop` is treated as a gate | Non-unitary or ordering/synchronization instruction was put in a gate definition | Use it in the circuit or subroutine; reserve `gate` for unitary meaning |
| Physical/virtual operands are mixed unexpectedly | `$n` is a fixed hardware reference, while named qubits are virtual; only calibration signatures have special physical rules | Choose a fully virtual design or document a target-specific mixed intermediate; never declare `$n` or assume remapping |

## Control flow and subroutines

| Symptom | Likely cause | Repair and validation |
|---|---|---|
| `break` or `continue` rejected | No enclosing `for`/`while`; `switch` does not count as a loop | Remove it, use `end` if immediate termination is intended, or move it into the nearest actual loop |
| `switch` rejected | Controlling expression is not integer, no case exists, case labels are runtime/duplicated, or statements occur outside cases | Use an integer expression with constant labels, at least one case, optional one default, and put all statements in case/default bodies |
| `if` condition rejected | Condition is not Boolean-compatible | Compare values explicitly or cast an appropriate scalar; do not use a multi-bit register as if it were scalar without a defined conversion |
| Subroutine call aliases a qubit twice | Two formal qubit arguments refer to the same underlying qubit | Pass each qubit once; create separate aliases only when they refer to distinct elements |
| `return` type fails | Missing result, wrong result type, or a `void` declaration has a value return | Match the arrow type exactly; use `return;` only for a no-result `def` |
| Extern call parses but cannot compile/run | Declaration has no linked implementation or runtime support | Obtain the consumer's ABI/linkage contract and target support; treat the program as interface-only until linked |

## Timing and calibration

| Symptom | Likely cause | Repair and validation |
|---|---|---|
| `delay[...]` or `box[...]` type error | Duration expression uses an ordinary numeric type, has incompatible units, or resolves negative | Use a duration literal/variable or valid duration arithmetic; resolve stretches and verify non-negative final duration |
| Stretch has no value or box cannot be scheduled | Stretch is design intent, not a numeric runtime variable, or constraints are inconsistent | Let a timing compiler solve it; reduce conflicting hard constraints and ensure every boxed operation can fit |
| `durationof` fails | Referenced operation has no known calibration or physical mapping | Supply a target calibration contract and a physical operand; do not replace it with an invented duration |
| `defcal` rejects qubit operands | A calibration requires physical references or the target's general-physical convention differs | Use `$n` for a target-specialized calibration, or document the consumer's allowed generic calibration form |
| Calibration body parses but is rejected later | Body lacks definite compile-time duration, branches differ in duration, or loops are unresolved | Make every path equal and definite; remove runtime-dependent pulse lengths or obtain the target's supported resolution rules |
| `play`/`capture` is unavailable | Operation is outside a `defcal`/`cal` context or the selected grammar/provider does not define it | Move it to the proper calibration block and load the provider's grammar contract; do not treat OpenPulse names as universal |
| Frame/port/waveform is undefined | These are provider-owned resources, often provided by an include or extern declaration | Use only names and signatures supplied by the target; verify sample-rate and duration realizability |
| `barrier` is expected to consume a known time | Barrier is ordering/synchronization, not a duration declaration | Use `delay`, `box`, or a target-resolved calibrated duration when actual timing is required |

## Include and execution confusion

An include statement can be accepted at the grammar layer while all of the
following remain unknown: search-path resolution, versioned contents, symbol
collisions, provider-specific definitions, and hardware execution support.
Diagnose in this order:

1. Confirm the version statement and global placement.
2. Ask the consumer which include search path and versioned file it uses.
3. Confirm that every referenced gate/directive/extern is defined by that file.
4. Run semantic/type and target compilation checks.
5. Only then run the program and inspect measured results.

Likewise, a parser can accept physical `$n`, a `defcal` shell, a pragma, an
extern signature, or an OpenPulse body without proving device topology,
linkage, timing, calibration validity, or execution. Mark these cases as
parser-only or implementation-dependent in reviews and keep the unresolved
assumption explicit.
