# Dependency and backend matrix

Use this matrix to decide whether a requested workflow is ready, optional, or
blocked. A version match is evidence for a package environment, not a promise
that a closed-source simulator or a GPU driver will work. The related
installation and recovery procedures are in [installation](installation.md)
and [troubleshooting](troubleshooting.md).

## Core installation groups

| Group | Declared or observed requirement | Required for | Verification | Status rule |
|---|---|---|---|---|
| Python foundation | Python 3.8-era environment | all project imports | `check_environment.py` | warn outside 3.8; investigate before relying on old Hydra/build behavior |
| Tensor runtime | PyTorch 1.10.0 with CUDA 11.3 build | CUDA policy and training; CPU MPC can inspect without CUDA | import Torch, print `torch.version.cuda`, allocate a CUDA tensor when available | exact/pinned family; CUDA unavailable blocks GPU workflows |
| Numeric/config stack | NumPy 1.20-era, SciPy, PyYAML, Hydra 1.1.0, OmegaConf 2.1 | config and RL workflows; NumPy also feeds native build | package imports and static config check | missing required package fails the matching workflow |
| Gamepad package | `inputs==0.5` | launcher module import and physical gamepad mode | import `inputs`; no device is required for `--disable-gamepad` | package is required by the current import graph; hardware is optional |
| Logging | TensorBoard | viewing training summaries only | import or `tensorboard --help` | optional for controller and training execution |
| Editable RL library | `rsl_rl` at `2ad79cf0caa85b91721abfe358105f869a784121` | training and policy loading | `rsl_rl` import and optional revision check | install with `--no-deps` to preserve Torch |
| MPC package | editable current project package plus `mpc_osqp` | CPU-side MPC, controller modes, policy bridge | `pip check`, package imports, extension symbols | required for MPC; a failed extension build stops native controller use |

## Native build inputs

The inspected public repository's build consumes these source inputs. They are
implementation inputs, not instructions to install vendor code system-wide.
When a source-layout check is needed, pass the path of a current project copy
to the bundled extension script.

| Input | Recorded checkout commit | Role |
|---|---|---|
| RSL-RL repository | `2ad79cf0caa85b91721abfe358105f869a784121` | Python RL runner and policy API |
| pybind11 headers | `ffa346860b306c9bbfb341aed9c14c067751feb8` | C++/Python binding headers |
| Eigen headers | `02f420012a169ed9267a8a78083aaa588e713353` | linear-algebra headers |
| qpOASES sources | `268b2f2659604df27c82aa6e32aeddb8c1d5cc7f` | QP solver sources compiled into the extension |
| OSQP source tree | root-tree source input; not one of the four declared Git submodules | OSQP C sources and QDLDL/AMD headers used by `mpc_osqp` |

If a declared native input is empty, detached at another revision, or missing
its headers, initialize or restore it in the supplied current project copy
before rebuilding. Do not silently accept a floating latest revision: native
APIs and the RL dependency constraints are version-sensitive.

## Isaac Gym and hardware

| Capability | Dependency | Probe | Decision |
|---|---|---|---|
| CPU-side controller | Python packages, compiled `mpc_osqp`, NumPy | extension and package probes | may proceed without Isaac Gym |
| GPU tensor smoke | NVIDIA driver, PyTorch CUDA 11.3 build, visible GPU | `torch.cuda.is_available()` and a small allocation | pass is useful but does not prove simulation |
| Isaac Gym simulation | external Isaac Gym Preview 4, compatible driver, CUDA device, assets | `import isaacgym`; then a bounded backend smoke | missing import is a hard block for simulation |
| RL training/evaluation | Isaac Gym, `rsl_rl`, Hydra/OmegaConf, Torch, task YAML, checkpoint as applicable | strict environment probe plus sibling RL checks | do not start if Isaac Gym remains blocked |
| Headless simulation | same Isaac Gym/PhysX backend, no viewer | strict Isaac Gym probe | headless removes display pressure, not backend requirements |

The recorded preparation had PyTorch/CUDA, A100 allocation, package imports,
`rsl_rl`, `mpc_osqp`, and `pip check` passing. Isaac Gym was not importable and
no usable SDK distribution was available. Keep that state visible until a new
strict probe passes.

## Optional solvers and packages

- The compiled `mpc_osqp` binding is the default path used by the MPC
  controller; it is not the same thing as importing the optional Python `osqp`
  package.
- Python `osqp` may be useful for independent solver experiments but is not a
  substitute for the compiled binding's symbols.
- CVXOPT is an optional alternate Python solver referenced by the solver notes;
  install it only when a workflow explicitly selects it.
- MOSEK is optional and requires a separately obtained license; a missing
  license is not an installation failure for the OSQP path.
- OSQP Eigen and system-wide CMake install examples in the solver notes are
  reference material, not prerequisites for the checked-in Python extension.
  Do not run their `sudo` or system-prefix commands as part of this workflow.

A package is **optional** only when the selected route does not import or call
it. Do not label Isaac Gym, Torch, or `mpc_osqp` optional for their respective
simulation, GPU, and MPC workflows.

## Resolver hazard

The RSL-RL package metadata declares `torch>=1.4.0` and `torchvision>=0.5.0`
without the repository's exact Torch upper bound. A plain editable install can
therefore replace Torch 1.10/CUDA 11.3 with a newer build. The safe order is:

1. create the isolated environment from the current project's specification;
2. verify pinned Torch/CUDA;
3. install the user-supplied RSL-RL repository with
   `python -m pip install --no-deps -e "$RSL_RL_REPO"`;
4. install the current project package and compile `mpc_osqp`;
5. run the import, CUDA, and `pip check` probes.

If `pip check` reports an unmet companion dependency, add a release compatible
with the pinned Torch family explicitly, then re-run all probes. Never accept a
successful pip command as proof that the pinned runtime survived.
