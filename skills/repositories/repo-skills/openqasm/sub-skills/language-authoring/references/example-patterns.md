# Example patterns

These are compact patterns to adapt, not a replacement for a target
compiler. Each label states what the pattern proves.

## 1. Typed I/O, array reference, modifier, branch, and timing box

**Label: portable language pattern with standard-library assumption.** The source
uses the standard gate include, a global array, a readonly array reference, a
controlled gate, measurement feed-forward, and explicit timing intent.

```qasm
OPENQASM 3.1;
include "stdgates.inc";

input angle[32] theta;
output bit[2] result;

array[int[8], 2] samples = {1, 2};

def checksum(readonly array[int[8], #dim = 1] values) -> int[8] {
  int[8] total = 0;
  for int i in [0:1] {
    total += values[i];
  }
  return total;
}

int[8] total = checksum(samples);
qubit[2] q;

reset q;
rz(theta) q[0];
box [100ns] {
  ctrl @ x q[0], q[1];
  delay[10ns] q[0];
}

bit branch;
branch = measure q[0];
if (branch) {
  reset q[1];
} else {
  x q[1];
}

result = measure q;
```

Validation sequence:

1. Parse with version 3.1 and confirm the include is resolved to a compatible
   `stdgates.inc`.
2. Check that `samples` is global and `checksum`'s reference has one dimension;
   ensure `total` has the subroutine's declared return type.
3. Check the modifier's two operands and the `measure q` to `bit[2]` shape.
4. Ask a timing-aware compiler whether the `100ns` box can contain the
   operations and whether `10ns` is realizable. The box is timing intent, not
   evidence of execution.
5. Check typed input binding and output collection separately from parsing.

## 2. Teleportation-style measurement feed-forward

**Label: portable circuit pattern with standard-library assumption.** This
pattern demonstrates reset, entanglement, measurement destinations, and
classical correction. It does not claim a simulator or QPU result.

```qasm
OPENQASM 3.1;
include "stdgates.inc";

qubit[3] q;
bit[2] correction;

reset q;
// Prepare the input state on q[0] here before adapting this pattern.
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
correction[0] = measure q[0];
correction[1] = measure q[1];

if (correction[1]) {
  x q[2];
}
if (correction[0]) {
  z q[2];
}

// q[2] is the teleported output; measure it only if the caller wants bits.
```

The order of `correction[0]` and `correction[1]` is an author choice, but the
correction mapping must match the circuit convention. Validate it by tracing
which bit was assigned by each measurement. Do not replace the two scalar
measurements with a register measurement unless the destination shape and
correction interpretation are deliberately changed.

## 3. Ordered loop versus broadcast

**Label: portable language pattern.** Broadcasting is concise but promises that
the expanded operations may be reordered. Use a loop when the sequence order is
part of the algorithm.

```qasm
OPENQASM 3.1;
include "stdgates.inc";

qubit[4] data;
qubit control;

// Broadcast: four controlled-X operations; equal register length is required.
ctrl @ x control, data;

// Explicit ordered sequence, useful when each step depends on prior state.
for int i in [0:3] {
  rz(pi / 8) data[i];
  if (i == 2) {
    x data[i];
  }
}
```

A compiler may reorder the broadcasted operations under its broadcast promise;
the loop establishes a source-level order. Check target support for a runtime
loop condition separately.

## 4. Timing alignment with stretch, delay, box, and nop

**Label: portable timing-intent pattern; scheduling is target-dependent.**

```qasm
OPENQASM 3.1;
include "stdgates.inc";

qubit[3] q;
stretch span;

barrier q;
box [span] {
  x q[0];
  delay[span] q[1];
  nop q[2];
}
barrier q;
```

The source asks for a bounded, synchronized region. It does not give `span` a
numeric value. A timing compiler must resolve the stretch, verify that all
operations fit the box, and reject a negative or otherwise unrealizable final
duration. `nop q[2]` marks participation without specifying an operation.

For a calibrated duration query, use a target-aware context such as:

```qasm
OPENQASM 3.1;
duration x_time = durationof({ x $0; });
```

This is syntactically a language pattern but semantically depends on a
calibration for physical qubit `$0`; it is not portable execution evidence.

## 5. Calibration grammar boundary

**Label: parser-only illustration / implementation-dependent.** It shows the
boundary and physical operand shape without inventing a provider waveform.

```qasm
OPENQASM 3.1;
defcalgrammar "openpulse";

defcal x $0 {
  // A target must supply definite-duration OpenPulse operations here.
}
```

A real calibration must use the selected grammar, a target's physical mapping,
provider-defined ports/frames/waveforms, and a body with definite duration on
every control-flow path. The empty/comment-only body is intentionally not an
execution claim. To make it executable, obtain the consumer's calibration
include and validate resource names, sample-rate quantization, and duration.

## 6. Diagnostic source for mixed qubits, loop control, and includes

**Label: parser/context diagnostic fixture; do not execute as a complete
program.**

```qasm
OPENQASM 3.1;
include "stdgates.inc";

qubit q;
x q;
x $0;       // physical target reference; it is not declared
break;       // invalid: no containing for/while loop
```

Repair it by choosing one qubit model, placing `$0` only where the target's
physical circuit contract permits it, and removing `break` or moving it inside
a loop. Separately verify that the consumer resolves `stdgates.inc`; an
accepted include token does not prove that the file is found or that `x` is
provided by the selected version.

## Pattern review checklist

- Keep `OPENQASM` first after comments, and use one declared version.
- Resolve every include and check gate availability, rather than treating the
  include statement as a definition by itself.
- Check global-only declarations (`include`, arrays, `defcalgrammar`, and
  global directives) before checking ordinary statement flow.
- Compare exact `bit`/`bit[n]`, array shape, angle width, and qubit operand
  counts.
- Mark patterns that contain `$n`, `extern`, OpenPulse, `durationof`, or target
  directives as implementation-dependent unless the consumer contract is
  supplied.
- Parse first, then run semantic/type/timing validation, then compile or
  execute only with an explicitly supported consumer.
