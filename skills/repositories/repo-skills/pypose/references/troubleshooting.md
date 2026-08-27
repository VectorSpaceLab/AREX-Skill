# PyPose Troubleshooting

Read this for failures that cross more than one PyPose workflow. For a
workflow-specific issue, use the nearest sub-skill's `references/troubleshooting.md`.

## Install and import

**Symptom:** `ModuleNotFoundError: No module named 'pypose'`.

- Install the public package into the same Python that will run the experiment:
  `python -m pip install pypose`.
- Verify with `python scripts/check_pypose_env.py` from the `pypose` skill
  directory. Avoid an unqualified `pip` from a different environment.

**Symptom:** import fails with a PyTorch version assertion or a missing torch
module.

- PyPose 0.9.5 declares `torch==2.*` in its runtime requirements and checks
  that the imported PyTorch is at least 2.0. Install a compatible PyTorch build
  for the desired CPU/CUDA/ROCm platform before reinstalling PyPose.
- Check `python -c "import torch; print(torch.__version__, torch.version.cuda)"`
  and then retry the root diagnostic. Do not copy a CUDA wheel command from a
  different driver/platform.

**Symptom:** an optional `bae` import fails while ordinary `import pypose` is
expected to work.

- BAE is not needed for base LieTensor, modules, dense optimization, or
  geometry. Remove the sparse-only path or install a version compatible with
  the current PyTorch/CUDA toolchain.
- Read the optimization sparse reference before repairing the environment.
  Do not make ordinary package import depend on an optional backend.

## Device and dtype

**Symptom:** `Expected all tensors to be on the same device` or a CUDA runtime
error.

- Choose one `torch.device` and move the model, LieTensors, covariances,
  intrinsics, targets, and inputs together. A CPU tensor hidden in `Q`, `R`,
  `weight`, or a target is a frequent cause.
- For CUDA, check `torch.cuda.is_available()` and allocate a tiny tensor before
  running a large workflow. A visible GPU does not prove that the active
  process has free memory; retry on a free device or reduce the fixture.
- Keep related values in one floating dtype. Use float64 for geometry and
  numerical optimization when the problem is sensitive; use float32 only after
  checking the tolerance and backend support.

**Symptom:** a sparse path reports CUDA unavailable, `cusparse` errors, or out of
memory.

- Sparse LM is CUDA-only and has no CPU substitute. Run
  `sub-skills/optimization/scripts/sparse_lm_smoke.py --check-only` from the
  skill directory to distinguish missing prerequisites from a numerical run.
- If readiness passes but a real graph fails, reduce the graph and factor block
  size, select a free CUDA device, and confirm `bae==0.2.1` plus the matching
  PyTorch/CUDA build. Keep the task dense if sparse readiness cannot be proven.

## Shape and type failures

**Symptom:** `ltype` is missing, group composition fails, or a final dimension
is rejected.

- `.tensor()` returns an ordinary tensor and removes LieTensor semantics. Rewrap
  it with the correct `pp.SO3`, `pp.SE3`, `pp.se3`, or another matching alias
  before using manifold methods.
- Distinguish storage embedding dimensions from local manifold dimensions:
  SE3 stores 7 values but has a 6-dimensional tangent; SO3 stores 4 but has a
  3-dimensional tangent. Preserve batch dimensions before the final embedding.
- Use `@` for matching group composition and point action. Check whether the
  point is Euclidean (`...,3`) or homogeneous (`...,4`) and whether batches
  broadcast as intended.

**Symptom:** filters, controls, or optimizers run but produce wrong shapes or
non-finite values.

- Make state, input, observation, residual, and matrix trailing dimensions
  explicit. Check that `Q`/`R` are square in the intended spaces and that
  residual targets have the same structure as model output.
- Test a tiny deterministic fixture and assert finite outputs, covariance
  symmetry, decreasing loss, or geometric round-trip error before loading real
  data.

## Data, configuration, and external artifacts

**Symptom:** an example asks for a dataset, downloads a file, or opens a plot.

- The generated skill intentionally does not require original example files or
  external datasets. Use its synthetic helper first. Network/download/plot
  paths are evidence-only and should be run only with explicit data, storage,
  and runtime approval.
- Validate camera intrinsics, positive depth, point counts, timestamp ordering,
  and frame direction before a geometry or metric run. Validate IMU units,
  positive time intervals, and reset semantics before integrating a sequence.

**Symptom:** a metric or evaluation symbol cannot be imported as `APE` or `RPE`.

- PyPose exposes trajectory metrics as lower-case functions such as
  `pp.metric.ape` and `pp.metric.rpe`; the detailed helper implementation also
  provides `StampedSE3`, `associate_traj`, and `compute_error`. Read the
  geometry-evaluation metric reference instead of guessing class names.

## Escalation

If a failure persists, capture the package version, PyTorch version, device
availability, requested workflow, input/target trailing shapes, and the first
exception. Do not include private paths, credentials, or full environment
activation commands in a research artifact. If the public API or optional
backend contract changed, refresh the skill from the newer package evidence.
