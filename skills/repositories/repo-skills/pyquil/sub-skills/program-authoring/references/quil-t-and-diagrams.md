# Quil-T, pulse objects, and diagrams

Read this reference when authoring pulse-level Quil-T, inspecting definitions,
selecting calibration serialization, or producing LaTeX. It describes object
construction and text generation only. It does not prove hardware timing,
compiler support, QVM/QPU acceptance, or external rendering success.

## Quil-T object model

Quil-T adds time- and hardware-facing instructions to ordinary Quil. The
relevant Python objects are split across `quilatom`, `quilbase`, `gates`, and
`quiltwaveforms`:

| Layer | Objects and verified signatures | Output role |
|---|---|---|
| Frame identity | `Frame(qubits, name)` | Identifies the channel/frame used by pulse operations. |
| Frame definition | `DefFrame(frame, direction=None, initial_frequency=None, hardware_object=None, sample_rate=None, center_frequency=None, enable_raw_capture=None, channel_delay=None)` | Emits `DEFFRAME`; generic key/value attributes can also be changed via `set_attribute(name, value)`. |
| Waveform definition | `DefWaveform(name, parameters, entries)` | Emits `DEFWAVEFORM` with literal or symbolic entries. |
| Waveform invocation | `WaveformInvocation(name, parameters=None)` | References a named waveform in `PULSE`/capture operations. |
| Calibration | `DefCalibration(name, parameters, qubits, instrs, modifiers=None)` | Emits a `DEFCAL` for a gate instruction. |
| Measurement calibration | `DefMeasureCalibration(qubit, memory_reference, instrs)` | Emits a `DEFCAL MEASURE`; `qubit` may be `None`. |
| Pulse | `PULSE(frame, waveform, nonblocking=False)` | Adds `PULSE` or `NONBLOCKING PULSE`. |
| Frame controls | `SET_FREQUENCY`, `SHIFT_FREQUENCY`, `SET_PHASE`, `SHIFT_PHASE`, `SET_SCALE` | Adds frame-control instructions. |
| Capture | `CAPTURE(frame, kernel, memory_region, nonblocking=False)`; `RAW_CAPTURE(frame, duration, memory_region, nonblocking=False)` | Adds kernel or raw capture instructions. |
| Timing | `DELAY(*args)`; `FENCE(*qubits)` | Adds timing barriers/delays; call signatures are intentionally overloaded. |

A `Frame` can use fixed qubits, placeholders, or formal arguments. A
`WaveformInvocation` is a reference, not a sample array. `DefWaveform` entries
are Quil expressions; they are serialized, not automatically played.

## Template waveforms

`pyquil.quiltwaveforms` provides safe, local waveform invocation templates:

- `FlatWaveform(duration, iq, scale=None, phase=None, detuning=None)`
- `GaussianWaveform(duration, fwhm, t0, scale=None, phase=None, detuning=None)`
- `DragGaussianWaveform(duration, fwhm, t0, anh, alpha, scale=None, phase=None, detuning=None)`
- `HrmGaussianWaveform(duration, fwhm, t0, anh, alpha, second_order_hrm_coeff, scale=None, phase=None, detuning=None)`
- `ErfSquareWaveform(duration, risetime, pad_left, pad_right, scale=None, phase=None, detuning=None)`
- `BoxcarAveragerKernel(duration, scale=None, phase=None, detuning=None)`

Each is a `TemplateWaveform` invocation. `samples(rate)` computes a reference
NumPy array locally for supported templates; the implementation notes that
hardware ADC alignment can differ. Use this only for local waveform inspection,
not as a QPU waveform proof. `num_samples(rate)` uses the duration and ceiling
rule and raises if duration has a nonzero imaginary part.

Example:

```python
from pyquil.gates import PULSE
from pyquil.quilatom import Frame
from pyquil.quiltwaveforms import GaussianWaveform

frame = Frame([0], "rf")
pulse = PULSE(
    frame,
    GaussianWaveform(duration=1e-6, fwhm=4e-7, t0=5e-7),
)
print(pulse.out())
```

Do not use an invocation template as a replacement for a `DefWaveform` when a
self-contained Quil text artifact needs a named definition. Add a matching
`DefWaveform` or use a definition already present in the `Program`.

## Build a calibration-aware program

A robust inspection sequence is:

1. Build the `Frame` and add a `DefFrame` with only intended attributes.
2. Add a `DefWaveform` (or a `TemplateWaveform` invocation inside a definition).
3. Add `DefCalibration`/`DefMeasureCalibration` bodies made from typed
   instructions.
4. Add ordinary gate/measurement instructions.
5. Inspect `program.frames`, `program.waveforms`, `program.calibrations`, and
   `program.measure_calibrations`.
6. Serialize once with the default `program.out()` and once with
   `program.out(calibrations=False)`.
7. If needed, call `program.match_calibrations(instr)`,
   `program.get_calibration(instr)`, or `program.calibrate(instr)` to inspect
   matching/expansion behavior locally.

Calibration definitions with the same identifying name, parameters, and qubits
are replaced when a differing definition is added; PyQuil warns about a
redefinition. Do not interpret this as a hardware calibration update.

`out(calibrations=False)` removes `DefCalibration` and
`DefMeasureCalibration` definitions only. It retains `DEFFRAME`, `DEFWAVEFORM`,
`DEFGATE`, declarations, and body instructions. This makes it useful for
comparing gate/calibration metadata with a calibration-free gate-level view,
but it does not make a Quil-T program QVM-compatible. `remove_quil_t_instructions`
creates a separate program with all Quil-T instructions removed; check its
output and semantics rather than assuming definitions have been preserved.

## LaTeX source versus display

`pyquil.latex.to_latex(program, settings=None) -> str` creates a complete
LaTeX document using TikZ/Quantikz source. `DiagramSettings` defaults are:

```text
texify_numerical_constants=True
impute_missing_qubits=False
label_qubit_lines=True
abbreviate_controlled_rotations=False
qubit_line_open_wire_length=1
right_align_terminal_measurements=True
```

Useful local choices:

```python
from pyquil.latex import DiagramSettings, to_latex

source = to_latex(program, DiagramSettings(
    impute_missing_qubits=True,
    label_qubit_lines=True,
))
```

This does not require invoking a compiler, QVM, QPU, or external service. The
returned text may be saved by the caller, but the package does not promise that
an external TeX installation will compile every program.

`pyquil.latex.display(program, settings=None, **image_options)` is a separate
optional convenience. It imports IPython and checks for `pdflatex` and
ImageMagick `convert`, then invokes them in a temporary directory. It can fail
with `FileNotFoundError` for either executable or `RuntimeError` for a failed
conversion. It returns an IPython `Image`, not LaTeX source. The authoring
helper should use `to_latex`, not `display`, for deterministic headless checks.

The diagram builder intentionally rejects or warns on some programs:

- forked gates raise `ValueError` because the diagram renderer does not support
  `FORKED` modifiers;
- classical jumps and many classical arithmetic/logical instructions are
  unsupported;
- `LATEX_GATE_GROUP` must be paired with `END_LATEX_GATE_GROUP`, and nesting is
  not supported;
- measurement alignment can emit a `UserWarning` when group pragmas conflict
  with trailing measurements.

Treat a successful `to_latex` call as source generation only. A successful
`display` call, if the optional external toolchain exists, is rendering
observation only—not execution or device validation.
