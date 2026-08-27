# Troubleshooting: core API and autograd

Use this page when core tensor math, gradient extraction, or state handling does not behave the way you expect.

## 1. Shape mismatch or broadcasting failure

**Symptoms**
- `assert` failures during arithmetic or matrix multiply.
- The model works for one tensor shape but not another.

**Likely causes**
- The batch dimension was not what you thought.
- A scalar/row/column tensor was used where a vector was expected.
- Broadcasting happened in one place but not the place you expected.

**Next step**
- Print shapes before and after the failing op.
- If the trace is unclear, rerun under `jt.flag_scope(lazy_execution=0, trace_py_var=3)`.
- Keep the bundled smoke script around as a known-good shape baseline.

## 2. Dtype or construction surprise

**Symptoms**
- A tensor becomes integer-like when you expected floats.
- Gradients or reductions behave oddly after a conversion.

**Likely causes**
- The constructor you used inferred a different dtype than you intended.
- A NumPy array or Python literal was converted without an explicit dtype.

**Next step**
- Prefer explicit constructors such as `jt.float32(...)` or `jt.array(..., dtype=...)` when the dtype matters.
- Re-check the value with `var.dtype` and a synchronized read.

## 3. Random constructor dtype surprise

**Symptoms**
- `jt.rand(..., dtype='float64')` or `jt.random(..., dtype='float64')` still produces a `float32` Var.
- A dtype-sensitive assertion fails even though the shape is correct.

**Likely causes**
- In the verified package, random constructors returned `float32` for non-float32 dtype requests, while `jt.zeros` and `jt.ones` honored dtype.

**Next step**
- Use `jt.array(np_array, dtype=...)`, an explicit cast, or a constant constructor when the exact dtype matters.
- Check `var.dtype` after construction instead of assuming the requested dtype was honored.

## 4. `Var.data` or `numpy()` seems slow

**Symptoms**
- A loop is unexpectedly slow because values are read back every iteration.

**Likely causes**
- Host-side reads force synchronization.

**Next step**
- Keep synchronized reads outside the hot path when possible.
- Use the read only for logging, assertions, or smoke tests.

## 5. Gradients are missing or zero

**Symptoms**
- `jt.grad` returns unexpected zeros.
- A parameter does not change after an update.

**Likely causes**
- The target was not part of the loss path.
- The loss was not reduced to a scalar.
- The variable is stopping gradients by design.

**Next step**
- Confirm the parameter really participates in the forward computation.
- Reduce the loss before calling `jt.grad`.
- Check `stop_grad` or `no_grad` usage.

## 6. The graph keeps growing

**Symptoms**
- Memory usage rises every iteration.
- `state_dict` or loss logging holds onto old graph objects.

**Likely causes**
- A Python list or global variable still references graph outputs.
- A loop stores raw tensors instead of scalarized values.

**Next step**
- Keep only the information you need from each iteration.
- If you are debugging, call `jt.clean()` or `jt.gc()` in a controlled test after values are synchronized.

## 7. Save/load or `state_dict` mismatch

**Symptoms**
- Loading a saved state skips parameters or warns about mismatched names/shapes.
- A module reloads but the behavior is not the same.

**Likely causes**
- The module architecture changed.
- A layer name or parameter shape changed.

**Next step**
- Compare the `state_dict` keys from the source and target modules.
- Treat mismatched names or shapes as a real migration problem, not a warning to ignore.

## 8. The smoke script still fails

If `scripts/core_api_smoke.py` fails, the issue is usually not exotic. It is almost always one of:
- a broken install,
- a shape or dtype mismatch,
- or a confusion about lazy execution and synchronized reads.

Fix those first before opening lower-level source code.