# Example Gallery Map

## Purpose

This file shows where the public example gallery fits in the generated skill. Small examples are bundled as smoke scripts; large or heavy examples are kept as reference-only evidence and routed to the owning sub-skill.

| Example | Status | Owning route | Why |
| --- | --- | --- | --- |
| `examples/tanh.py` | bundled as `sub-skills/differentiation-core/scripts/differentiation_smoke.py` | differentiation-core | Small derivative demo that exercises control flow and repeated differentiation. |
| `examples/define_gradient.py` | bundled as `sub-skills/extend-primitives/scripts/custom_primitive_smoke.py` | extend-primitives | Concise custom-primitive example that shows staged VJP authoring. |
| `examples/rosenbrock.py` | bundled as `sub-skills/optimization-workflows/scripts/rosenbrock_minimize.py` | optimization-workflows | Tiny scalar objective for `value_and_grad` and SciPy minimize. |
| `examples/fixed_points.py` | bundled as `sub-skills/optimization-workflows/scripts/fixed_point_smoke.py` | optimization-workflows | Public fixed-point helper example with a clean scalar recurrence. |
| `examples/gmm.py` | reference-only in this skill | optimization-workflows | Demonstrates flattening and structured optimization, but the full example is larger than the bundled smoke. |
| `examples/neural_net.py`, `examples/bayesian_neural_net.py`, `examples/gaussian_process.py`, `examples/ica.py`, `examples/black_box_svi.py`, `examples/mixture_variational_inference.py` | reference-only | optimization-workflows | Useful as evidence for structured optimization, but too large to make default smoke helpers. |
| `examples/convnet.py`, `examples/rnn.py`, `examples/lstm.py`, `examples/variational_autoencoder.py`, `examples/generative_adversarial_net.py`, `examples/deep_gaussian_process.py`, `examples/fluidsim/*` | reference-only | numpy-scipy-primitives or optimization-workflows as relevant | These are long-running or plotting-heavy demos and are not bundled as safe helpers. |
| `examples/dot_graph.py`, `examples/print_trace.py` | reference-only | differentiation-core | Good debugging references, but not needed as default runtime helpers. |

## How to use this map

- If you want a quick runnable check, use the bundled smoke scripts instead of the full gallery.
- If you want a fuller example, use the reference-only example as evidence and adapt the bundled helper that already exists in the skill tree.
- Do not instruct future agents to open the original repository examples at runtime; the bundled scripts are the supported entry points.
