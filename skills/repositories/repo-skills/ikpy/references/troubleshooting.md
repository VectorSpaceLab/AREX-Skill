# Cross-cutting IKPy Troubleshooting

Read this reference when a failure does not clearly belong to one sub-skill.
Always preserve the original exception and the model/backend/shape context.

## Install and import

- **`ModuleNotFoundError: ikpy`** — the executing Python differs from the one
  where the package was installed. Run `python -m pip show ikpy` and the
  minimal import check with the same interpreter; do not rely on shell
  activation.
- **`ModuleNotFoundError: matplotlib` or `graphviz`** — install the `plot`
  extra only for plotting/tree rendering. Core FK/IK and XML parsing do not
  need it.
- **`ModuleNotFoundError: jax` or `jaxlib`** — install `ikpy[jax]`, then rerun
  `ikpy.JAX_AVAILABLE`. A CPU JAX install is a valid optional baseline; do not
  claim CUDA acceleration unless the installed JAX runtime explicitly reports
  a CUDA backend.
- **Package/import mismatch** — confirm `ikpy.__version__` and the imported
  module's public symbols. Avoid mixing an editable checkout with a different
  installed release when comparing behavior.

## Shape and data validation

- **`Your joints vector length is ... but you have ... links`** — pass a full
  vector, including origin, inactive, and terminal entries. Use
  `[0.0] * len(chain.links)` as a starting shape and replace only intended
  active positions.
- **`Your target must be a 4x4 transformation matrix`** — use
  `inverse_kinematics` for position/orientation inputs or construct a valid
  homogeneous matrix for `inverse_kinematics_frame`. Keep the last row
  `[0, 0, 0, 1]`.
- **`active links mask length ...`** — make the mask exactly as long as
  `chain.links`; fixed origin/tip links should normally be false.
- **Unexpected fixed-link warnings** — a fixed link marked active is ignored
  as an actuator but indicates a mask mistake. Correct the mask rather than
  suppressing the warning.

## Solver and target failures

- **IK returns a plausible but inaccurate pose** — rerun FK, compute position
  and orientation residuals, and try a reachable target with a meaningful
  `initial_position`. Check bounds and frame units before changing tolerances.
- **`Unknown orientation mode`** — use `None`, `X`, `Y`, `Z`, or `all` exactly.
  For orientation-only optimization, provide an orientation mode and a valid
  initial full vector; optimizing neither position nor orientation is invalid.
- **Target is unreachable or solver stalls** — confirm the target frame and
  chain scale, start near a known pose, relax an overly narrow bound, or use a
  staged position-then-orientation solve. Do not interpret a solver result as
  proof of reachability.
- **`Unknown solver`** — NumPy IK accepts `least_squares` or the legacy
  `scalar` route. JAX-specific `scipy_*` arguments belong only to the JAX
  backend.

## Model and backend boundaries

- **Wrong imported path or link count** — inspect source names first, then set
  URDF alternating `base_elements` or MJCF body `base_elements` explicitly. A
  branch or missing root is a data-selection error, not an IK tolerance issue.
- **MJCF angle mismatch** — MJCF defaults to degrees unless its compiler says
  otherwise; IKPy converts hinge ranges and orientations to radians. Verify
  `compiler angle` and `eulerseq`.
- **JAX does not support a link** — use NumPy for `DHLink` or unknown custom
  link classes; JAX's parameter extraction has explicit link-type cases.
- **JAX first call is slow** — compilation is expected. Choose
  `jax_precompile=False` to defer it or precompile once when predictable first
  operation latency matters. Reuse the chain's cache within the process.
- **GPU warning/fallback** — a visible NVIDIA device is not enough. Check
  `jax.default_backend()` and installed `jaxlib`; use CPU explicitly for a
  portable check and do not install arbitrary CUDA wheels.

## Rendering and safety

- **Headless Matplotlib error** — set the `Agg` backend before importing
  `pyplot` or `ikpy.utils.plot`; save the figure and close it.
- **Graphviz render fails** — the Python `graphviz` package and the system
  `dot` executable are separate requirements. Inspect the returned DOT object
  first and use a no-render path if `dot` is unavailable.
- **Plot looks correct but motion is unsafe** — plots are diagnostics only.
  Validate collision, joint limits, controller conventions, timing, and
  hardware interlocks separately. Do not run indefinite robot-control loops
  from this skill.
