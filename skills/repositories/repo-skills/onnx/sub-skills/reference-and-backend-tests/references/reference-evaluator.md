# ONNX ReferenceEvaluator Reference

The `ReferenceEvaluator` provides a pure-Python implementation of ONNX operator semantics for debugging and expected-value checks.

## Verified signature

```python
from onnx.reference import ReferenceEvaluator

ReferenceEvaluator(
    proto,
    opsets=None,
    functions=None,
    verbose=0,
    new_ops=None,
    optimized=True,
)
```

## Minimal use

```python
import numpy as np
from onnx.reference import ReferenceEvaluator

sess = ReferenceEvaluator(model_or_path)
result = sess.run(None, {"X": np.array([1, 2], dtype=np.float32)})
```

- `proto` may be a model-like artifact accepted by ONNX's loader path, not just a `ModelProto` object in a ready-to-run form.
- `verbose=1` or higher can help trace intermediate values during debugging.
- Use the ONNX spec and reference implementation as the ground truth when a backend disagrees.

## Practical notes

- The reference evaluator covers most of the repository's backend test cases, but not every operator or optional dependency path.
- If a model uses an operator implemented only through optional reference extras, install `onnx[reference]` to bring in the matching dependency.
- Mismatches can mean either a backend bug or a repo spec/reference issue; diagnose both before deciding which side to change.
