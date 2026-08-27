# Core object troubleshooting

## Dimension and type mismatches

- `Qobj` errors that mention dimensions usually mean the subsystem tensor structure does not match across states and operators.
- Rebuild the objects with the same tensor order before trying again.
- Use `tensor(...)` and then inspect `dims` before multiplying objects.

## Measurement compatibility

Common measurement errors include:

- `op must be all operators or all kets`
- `state must be a Qobj`
- `measurement operators must sum to identity`
- `op and state dims should match`

These are almost always modeling mistakes, not solver bugs. Check the projector list and Hilbert-space dimensions first.

## Metrics and channel helpers

- Distance and fidelity helpers can return nonsense if the input is not a valid state or channel.
- Ensure the object is normalized when the metric assumes a state.
- For channel metrics, confirm that the object is really a superoperator or other supported channel representation.

## Random-object smoke checks

- Random states and operators are useful for quick API smoke tests, but they are not a substitute for a real physical model.
- If a random object fails, the problem is usually a package installation or dimension issue rather than a physics issue.
