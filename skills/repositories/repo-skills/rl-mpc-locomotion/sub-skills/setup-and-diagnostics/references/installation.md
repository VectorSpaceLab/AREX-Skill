# Installation and verification

This guide is the public, reproducible installation contract for the project.
Use a current project/package copy supplied by the user and keep the
environment isolated; do not mutate a base environment or rely on the files
that contain this skill.

## Baseline

The declared baseline is:

| Component | Required baseline | Why it matters |
|---|---|---|
| Python | 3.8 | the project documentation and environment target this era |
| PyTorch | 1.10.0 | controller/RL tensor code and the recorded CUDA smoke |
| CUDA runtime | 11.3 toolkit build | the documented PyTorch build and GPU pipeline |
| NumPy | 1.20.0-era | declared by the environment and native extension headers |
| Hydra / OmegaConf | 1.1.0 / 2.1 | training configuration composition |
| inputs | 0.5 | gamepad reader import and optional physical input |
| setuptools | 59.5.0 | old extension build assumptions |
| pip | `<24.1` in the environment specification | limits incompatibilities with the old dependency set |

The project also declares SciPy, PyYAML, TensorBoard, and pybind11. TensorBoard
is a logging convenience; pybind11 is used by the native binding. Isaac Gym is
not part of the environment specification: it is a separate NVIDIA Preview 4
dependency.

## Ordered setup

Set variables to paths owned by the user. They are placeholders, not paths to
the skill bundle:

```bash
PROJECT_COPY=/path/to/current/project-copy
RSL_RL_REPO=/path/to/current/rsl_rl-repository
```

1. Obtain the current public project/repository copy and initialize its
   declared submodules or other native inputs according to its public install
   instructions. Confirm the expected revisions in
   [dependency-matrix](dependency-matrix.md). Do not replace a pinned native
   input with a floating latest checkout.
2. Create an isolated environment using the supplied project's environment
   specification. Use an explicit environment invocation rather than relying
   on shell activation:

   ```bash
   conda env create -f "$PROJECT_COPY/environment.yml"
   conda run --name rlmpc python -c "import sys, torch; print(sys.version); print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
   ```

   If the environment name already exists, use a new environment or obtain
   explicit approval before changing it. Do not install into base.
3. Verify the foundation before adding the editable RL library, always using
   the selected environment's Python:

   ```bash
   conda run --name rlmpc python -c "import sys, torch; print(sys.version); print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
   ```

   The expected result is Torch 1.10.0, CUDA build 11.3, and `True` on a
   suitable CUDA host. A CPU-only result can support CPU-side inspection but
   cannot prove the configured GPU simulation path.
4. Install the pinned RSL-RL source in editable mode with dependency
   resolution disabled:

   ```bash
   python -m pip install --no-deps -e "$RSL_RL_REPO"
   ```

   This is intentional. Its metadata asks for an unconstrained modern-enough
   Torch (`torch>=1.4.0`) and a torchvision range; a normal editable install
   can replace the documented Torch 1.10/CUDA 11.3 environment. If pip reports
   a missing compatible companion package, select the companion release from
   the same PyTorch 1.10 release family rather than allowing an unconstrained
   resolver upgrade.
5. Install the current project copy through its public package metadata:

   ```bash
   python -m pip install -e "$PROJECT_COPY"
   ```

   This compiles the native MPC binding when the supplied copy exposes the
   editable build. It is the required local extension step, not a system-wide
   solver installation.
6. Verify the installation without launching Isaac Gym. Run these commands
   from the installed `setup-and-diagnostics` directory:

   ```bash
   python scripts/check_environment.py --pip-check
   python scripts/check_mpc_extension.py --strict
   python scripts/validate_config.py
   ```

   The package probes work without a project copy. To validate the current
   project's YAML, assets, and pinned native layout, add
   `--repo-root "$PROJECT_COPY"` to the relevant command; this is an explicit
   integrity check, not a dependency of package diagnostics.

## Isaac Gym gate

Isaac Gym Preview 4 is a closed-source external package and is required by the
project's RL, simulation, and interactive-controller package routes. Install it
into the same isolated Python environment only from an authorized SDK
distribution and according to its vendor instructions. No package in this
project can substitute for it.

After installation, from the installed `setup-and-diagnostics` directory, use:

```bash
python scripts/check_environment.py --require-isaacgym --strict --pip-check
```

A missing `isaacgym` import is a **required-backend block** for training and
simulation. Do not report those workflows as installed merely because
`torch.cuda.is_available()` is true or an NVIDIA device is visible. If the SDK
is unavailable, continue only with CPU-side package, configuration, and MPC
checks and carry the block forward.

## Public entry-point checks

- Use the current project's published console command or Python module for a
  parser-only check. Do not open or execute a checkout-local script from this
  skill.
- Install the current project copy with the public package command above before
  invoking its training or controller route. Use the entry point documented by
  that package/repository and pass `--disable-gamepad` when the controller
  route supports that option and no physical gamepad is available.
- Run training only after the strict Isaac Gym check passes. Use the RL sibling
  skill's Hydra override contract and a user-owned working/run directory; do
  not rely on a default directory from any source checkout.
- Check a user-supplied checkpoint before policy evaluation. Pass its absolute
  path to the bundled validator or the installed public command. A checkpoint
  file is not proved compatible merely by its `.pt` or `.pth` suffix.
- The user-supplied project copy must provide the URDF and mesh tree for the
  selected `Aliengo`, `A1`, or `Go1` task. `mini_cheetah` is present as an
  asset in the inspected source but is not a supported runtime selection in
  the simulation helper.

## Verification interpretation

`pip check` detects broken declared requirements but does not prove CUDA,
Isaac Gym, asset loading, or native symbol compatibility. The extension check
must import `mpc_osqp` and expose the recorded binding names. The config check
is intentionally static and does not resolve Hydra interpolations or start a
viewer. Use the sibling operating skills for runtime trials after these gates.
