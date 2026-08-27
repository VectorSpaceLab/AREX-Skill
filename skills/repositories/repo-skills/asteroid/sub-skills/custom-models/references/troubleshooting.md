# Custom model troubleshooting

## Constructor mismatches

- If `DPRNN.__init__()` rejects `n_blocks`, use `n_repeats` instead; Asteroid's DPRNN constructor repeats `DPRNNBlock` internally.
- Check `inspect.signature(...)` against the installed Asteroid package when adapting examples across releases.

## Shape and axis mistakes

- Asteroid models usually expect time-last waveform tensors.
- Many block helpers accept `[batch, features, time]` tensors and hide the reshaping internally.
- If a helper unexpectedly returns the wrong shape, compare it against the corresponding test in `tests/masknn/` or `tests/dsp/`.

## Serialization issues

- `BaseModel.serialize()` and `from_pretrained()` are the quickest round-trip check.
- If `get_model_args()` merges filterbank and mask-network config keys, make sure the keys do not collide.
- If a custom class cannot be reloaded, check whether it was actually registered.

## Registry issues

- `register_model(...)`, `register_norm(...)`, `register_activation(...)`, and `register_optimizer(...)` all reject duplicate names.
- When a lookup fails, confirm the class name, casing, and whether the module was imported before registration.

## JIT issues

- Trace the smallest possible synthetic input first.
- If eager and traced outputs differ, inspect unsqueeze/reconstruction helpers and any control flow that depends on the input type.

## Complex-number issues

- `asteroid.complex_nn` mixes PyTorch complex tensors with helper functions that convert to/from real representations.
- Use the dedicated complex helpers rather than trying to improvise with real-valued layers.

## Useful smoke checks

- `python -I -c "from asteroid.models import ConvTasNet; ..."`
- `python -I -c "from asteroid.masknn import TDConvNet, DPRNN; ..."`
- `pytest tests/masknn -q`
- `pytest tests/dsp -q`
- `pytest tests/jit -q`
