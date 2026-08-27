# Circuits and devices troubleshooting

## `DeviceError` or unknown device

- Try `qp.device("default.qubit", wires=1)` first. If that works, the package is installed and the problem is a plugin/backend selection issue.
- Check the plugin package is installed in the same Python environment as PennyLane.
- For GPU or hardware devices, verify drivers, device visibility, and plugin-specific wheels before constructing the QNode.
- Do not rewrite a user circuit for another backend unless the user accepts that narrowed scope.

## Wire label errors

- Wires can be integers, strings, or other hashable labels.
- Use a consistent type. Integer `0` and a zero-dimensional array containing `0` are distinct labels.
- When custom labels are used in `qp.device(..., wires=[...])`, every operation must use labels from that set.

## Measurements fail under analytic/finite shots

- `qp.sample` and `qp.counts` need finite shots.
- `qp.state` and exact probabilities are analytic/device-dependent.
- If changing shots for one call, use `qp.set_shots`; if changing permanently, update or recreate the QNode/device.
- When sampling, use tolerances or distributional assertions.

## Unexpected return shapes

- A single measurement returns its native result; a tuple of measurements returns a tuple.
- `probs(wires=[0, 1])` returns length `2**len(wires)` for qubits.
- `counts` returns a mapping keyed by observed outcomes; use `all_outcomes=True` when absent outcomes should be explicit.
- Mixed-state or density-matrix returns use matrix shapes over the selected wires.

## Mid-circuit measurements and postselection

- If a circuit contains `qp.measure`, choose an explicit `mcm_method` only when default behavior is wrong for the device or shot mode.
- `postselect_mode` affects what happens to invalid shots. State the selected behavior in user-facing code.
- Device support differs; if a transform rewrites mid-circuit measurement behavior, inspect the drawn circuit at different levels.

## Drawing surprises

- `qp.draw` and `qp.draw_mpl` can show different levels: user, device, gradient, or transform-program levels.
- If decompositions or gradient transforms appear, the drawing is not necessarily the original Python function; change `level` to match the question.

## Device-test CLI failures

- Run `pl-device-test --help` first; if it is missing, the console script is not installed in the active environment.
- Use `--device` to name the plugin/device explicitly.
- Use `--device-kwargs KEY=VAL` for required constructor options.
- If operations fail but the plugin intentionally supports a subset, use `--skip-ops` and document the limitation.
