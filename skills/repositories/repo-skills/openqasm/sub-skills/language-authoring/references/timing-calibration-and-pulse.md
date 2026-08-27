# Timing, calibration, and pulse concepts

Timing constructs express scheduling intent and calibration structure. They do
not by themselves provide measured gate durations, a device topology, a pulse
compiler, or executable provider definitions.

## Duration and stretch

`duration` values use SI units `ns`, `us`/`μs`, `ms`, and `s`, plus the
backend-dependent `dt` sample unit. Examples:

```qasm
duration readout_window = 400ns;
duration samples = 160dt;
duration combined = readout_window + 2 * 10ns;
duration calibrated = durationof({ x $0; });
```

Duration addition and subtraction combine durations; multiplication or
division by a constant scales a duration. Dividing two durations yields a
machine-precision float. Intermediate expressions may include a negative
component, but a resolved duration passed to a duration-bearing operation must
be non-negative. A duration is not a general numeric cast target.

A `stretch` is a non-negative, compile-time-resolved duration variable whose
value may grow to satisfy timing constraints:

```qasm
stretch slack;
delay[slack] q[0];
delay[2 * slack] q[1];
```

Do not claim a numerical value for a stretch before a scheduling compiler has
resolved it. A gate or instruction containing stretchable delays is itself
stretchy from the point of view of later timing constraints.

## Delay, box, barrier, and durationof

`delay[d] operands;` inserts an explicit scheduled identity interval on the
listed qubits. A multi-qubit delay synchronizes its operands to a common start
and end; it is not always equivalent to independent single-qubit delays.
Explicit delay constrains reordering on the listed qubits, unlike an implicit
idle gap.

`box` encloses a subcircuit while preserving its timing boundary:

```qasm
qubit[2] q;
stretch span;
box [span] {
  x q[0];
  delay[span] q[1];
}
```

A box can be assigned a hard duration. Use `nop` for a qubit that must enter and
leave the box synchronized but has no operation inside. A box is not a gate
definition: it constrains an occurrence in a larger circuit rather than
introducing a reusable unitary symbol.

`durationof({ ... });` asks for the resolved duration of a calibrated operation
or block. The referenced operation must be meaningful to the downstream
calibration/scheduling tool. A parser accepting the brace form cannot infer a
provider's calibration table.

`barrier` is an ordering boundary, not a measured duration. `nop` is an explicit
use/synchronization marker and has no ideal state change. Use these distinctions
when translating a circuit schedule: `barrier` preserves order, `delay` makes a
time interval explicit, `box` constrains a region, and `nop` marks participation.

## Calibration declarations

A calibration-aware program normally selects a grammar globally:

```qasm
OPENQASM 3.1;
defcalgrammar "openpulse";
```

`defcal` associates a pulse-level implementation with an instruction. Its
signature resembles a gate but may include parameter types, physical qubits,
and an optional classical return value:

```qasm
defcal x $0 {
  // Target-owned OpenPulse statements belong here.
}

defcal measure $0 -> bit {
  // Target-owned measurement and capture statements belong here.
}
```

Physical qubit operands such as `$0` specialize a calibration to fixed device
locations. A regular qubit identifier in a calibration may describe a
calibration valid for all physical qubits, commonly for a virtual operation;
interpret this only under a consumer that defines the mapping. The same
operation can have multiple calibrations, with more specific physical and
parameter matches taking precedence according to the consumer's calibration
rules.

`gate` and `defcal` communicate different information. A `gate` specifies
unitary meaning and can be decomposed or rewritten. A `defcal` supplies a
low-level implementation for a target. Defining one does not automatically
create the other.

`cal { ... }` contains calibration-level declarations/statements in the
selected grammar. Values declared there are available to other calibration
blocks or `defcal` declarations according to their scope rules. Keep provider
symbols in a provider-owned include or contract; do not invent port names,
frequencies, sample rates, waveform parameters, or calibration constants in a
portable example.

Calibration body restrictions are stronger than token acceptance. A `defcal`
body must have a definite, compile-time-resolvable duration. If it contains
branches, every selected branch must have an equivalent definite duration; a
loop must also resolve to a definite duration. A body containing a placeholder
or an unresolved capture is a parser illustration, not an executable
calibration.

## OpenPulse concepts

The OpenPulse grammar commonly models three resources:

- A `port` abstracts a target's transmit/receive hardware resource.
- A `frame` attaches a port to frequency, phase, and an implicit time cursor.
  `newframe(port, frequency, phase)` creates one; phase/frequency can be read or
  changed by `get_phase`, `set_phase`, `shift_phase`, `get_frequency`,
  `set_frequency`, and `shift_frequency`.
- A `waveform` is a sequence of complex samples or a target-supplied waveform
  template result. Its duration must be definite and realizable at the
  associated port's sample rate.

Typical target-supplied signatures look like this, but are not a universal
library:

```qasm
extern port drive;
extern frame drive_frame;
extern gaussian(complex[float[32]] amp, duration length,
                duration sigma) -> waveform;
```

`play(frame, waveform)` schedules a waveform and is normally legal only inside
`defcal` (the exact grammar may also allow it in a calibration block). A target
may define `capture` externs returning raw waveform data, complex samples, a
bit, or another classical value; capture is normally restricted to `defcal` or
`cal`. `barrier` can align frame clocks. Frame time advances through timing
operations such as `play`, `capture`, `delay`, and `barrier`.

Do not infer pulse semantics from names alone. The provider must define the
extern signatures, resource mappings, sample-rate quantization, allowed frame
operations, and calibration selection. Treat OpenPulse grammar as
implementation-dependent unless a named consumer has supplied that contract.

## Validation order for timing and calibration

1. Parse with the requested OpenQASM version and selected calibration grammar.
2. Check global placement of `defcalgrammar`, `cal`, includes, and directives.
3. Check duration types, unit compatibility, non-negative resolved durations,
   and compile-time resolvability of stretch/`durationof` constraints.
4. Check that `defcal` qubit operands are permitted physical references and
   that every provider-owned port/frame/waveform/extern name is defined.
5. Check definite and equivalent duration on every calibration control-flow
   path, then ask the target compiler/scheduler to resolve timing.
6. Only after target compilation should execution or hardware behavior be
   discussed.

A successful parse establishes none of steps 3-6.
