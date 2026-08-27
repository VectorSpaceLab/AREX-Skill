# Compatibility and backend contract

## Historical metadata versus verified use

GradSLAM `0.1.0` declares Python above 3.6 and `torch>=1.6.0` together with
pinned `chamferdist==1.0.0` and `open3d==0.10.0.0`, plus Kornia, OpenCV,
ImageIO, NumPy, Natsort, Plotly, PyYAML, and related runtime packages. Those are
package declarations, not a guarantee that every modern resolver combination
has a compatible binary ABI.

A CPU construction environment successfully imported the package and exercised
its public APIs using Python 3.8, PyTorch 2.0 CPU, Open3D 0.10, and a
`chamferdist` extension rebuilt against the selected Torch. Treat this as a
verified example combination, not a universal lockfile. The exact machine,
private environment, and executable are intentionally not part of this runtime
skill.

## Backend classification

- **Required and verified:** CPU for package import, configuration, data
  utilities, geometry, structures, odometry/SLAM tiny fixtures, and selected
  native checks.
- **Optional and not certified by CPU:** CUDA device transfer and
  CUDA-parametrized behavior. A host may have a GPU while the active Python
  environment still has a CPU-only Torch build.
- **Excluded:** ROCm, MPS, and vendor accelerators; this source baseline does
  not provide enough evidence to claim them.

Keep `torch.cuda.is_available()`, the Torch build string, and the tensor device
as separate observations. Never translate `False` into a package bug until the
installed Torch variant and driver/runtime are checked.

## Installation strategy

1. Use an isolated environment with a Python version compatible with this old
   package and the selected dependency wheels.
2. Install one coherent Torch variant first.
3. Install the remaining runtime dependencies without allowing a resolver to
   silently replace Torch with another ABI.
4. Build or reinstall `chamferdist==1.0.0` against the final Torch when a
   prebuilt extension reports an undefined symbol.
5. Install GradSLAM, run `python -m pip check`, then run the bundled environment
   checker and one tiny sub-skill smoke.

Avoid broad upgrades. Kornia releases newer than the repository era may depend
on Torch APIs absent from historical Torch 1.6, while a `chamferdist` binary
built against one Torch release may import-fail against another. If solving
requires a different Torch build, rebuild dependent extensions after the final
selection.

## Claims the skill does not make

- No claim that every version satisfying `torch>=1.6.0` works with today's
  newest dependencies.
- No claim that editable/source installation is required for ordinary use.
- No claim that Open3D visualization works headlessly merely because its Python
  import succeeds.
- No claim that external dataset adapters pass without caller-supplied data and
  metadata.
- No claim that CPU numerical success establishes CUDA parity, performance, or
  differentiability across map-fusion control flow.
