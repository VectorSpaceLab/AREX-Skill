# LAMMPS Deployment and Interface Guidance

Use this reference when a user wants to run a trained SchNetPack force model from LAMMPS. This skill provides deployment and configuration guidance, not default LAMMPS build automation.

## Safety Boundary

Do not compile LAMMPS, patch an external source tree, download CUDA/cuDNN, or mutate cluster build files unless the user explicitly asks and approves environment changes. SchNetPack's upstream LAMMPS patch helper changes a LAMMPS source checkout by editing CMake files and copying or symlinking pair-style sources, so treat that workflow as reference-only in normal agent workflows.

Safe actions by default:

- Explain compatibility requirements and build constraints.
- Inspect an existing input file or deployed model metadata if the user provides it.
- Run help for the bundled deployment script.
- Convert a compatible local model to TorchScript with `scripts/deploy_for_lammps.py` only when the user supplies model paths and accepts local file creation.

Unsafe-by-default actions:

- Running `patch_lammps.sh` against an external source tree.
- Building LAMMPS or changing CMake/linker configuration.
- Installing CUDA, cuDNN, PyTorch-CUDA, MKL, or compiler stacks.
- Running nontrivial LAMMPS MD.

## Deployment Script

Use the bundled script in this sub-skill:

```bash
python scripts/deploy_for_lammps.py best_model deployed_model --device cpu
```

The script preserves SchNetPack's `spkdeploy` behavior:

- Loads the Python model with `torch.load(..., weights_only=False)` on the requested device.
- Removes `CastTo32` and `CastTo64` postprocessors because casting postprocessors can break TorchScript/LAMMPS execution.
- Converts `AddOffsets.mean` to float for JIT compatibility.
- Scripts the model with `torch.jit.script`.
- Saves TorchScript with `_extra_files={"cutoff": ...}` metadata read from `jit_model.representation.cutoff.item()`.

Compatibility checks before deployment:

- The model should be a SchNetPack atomistic model with `postprocessors` and `representation.cutoff`.
- LAMMPS support is designed for force models that predict forces through automatic differentiation/response modules.
- Models that directly emit forces without the expected response path, lack `representation.cutoff`, or have unsupported postprocessors may fail at TorchScript conversion or at LAMMPS runtime.
- Use `--device cpu` unless the host has a compatible CUDA/PyTorch stack and the user requested GPU conversion.

## LAMMPS Pair Style Inputs

A SchNetPack-enabled LAMMPS input uses:

```lammps
pair_style schnetpack
pair_coeff * * deployed_model 6 1 8
```

Interpretation:

- `deployed_model` is the TorchScript model created by `deploy_for_lammps.py` or compatible `spkdeploy`.
- The numbers after the model path map LAMMPS atom types to atomic numbers.
- The example `6 1 8` means atom type 1 is carbon, atom type 2 is hydrogen, and atom type 3 is oxygen.
- Provide exactly one atomic number for each LAMMPS atom type in the data file.
- The pair style reads cutoff metadata from the deployed model and uses it to define neighbor interactions.

Review checklist for user-provided input files:

- Verify `pair_style schnetpack` appears once in the relevant force-field section.
- Confirm `pair_coeff * * <model> <Z...>` has the right number and order of atomic numbers for the LAMMPS data file.
- Confirm the deployed model file exists relative to the LAMMPS run directory or use an explicit path.
- Confirm units are consistent with the trained model and the LAMMPS input. The interface does not magically fix incompatible unit systems.
- Avoid changing a working LAMMPS input to use SchNetPack unless the user provides the intended atom-type mapping.

## Build Constraints

The repository's LAMMPS guide was written around a specific stack: CUDA 11.7, cuDNN, Python 3.9, SchNetPack 2.0, PyTorch 1.13, and `mkl-include`. Current installed-package facts for this generated skill are SchNetPack 2.2.0 on Python >=3.12 with CPU PyTorch sufficient for API/CLI inspection. Treat the upstream build recipe as historical/reference guidance, not proof that a local host can build the LAMMPS interface unchanged.

If the user explicitly asks for a build plan, include these checks:

- Confirm LAMMPS source checkout and version.
- Confirm C++ compiler compatibility with LAMMPS, Torch C++ libraries, and CUDA if GPU is desired.
- Confirm PyTorch CMake prefix path with `python -c 'import torch; print(torch.utils.cmake_prefix_path)'`.
- Confirm MKL include path when required by the build.
- Ensure standalone CUDA and PyTorch-CUDA versions match if building GPU support.
- Keep a backup or clean git checkout before running any patch script.

## Reference Pair-Style Behavior

The SchNetPack pair style source:

- Selects CUDA if `torch::cuda::is_available()`, otherwise CPU.
- Loads the TorchScript model with extra file metadata containing `cutoff`.
- Uses the `cutoff` metadata to set neighbor cutoffs.
- Builds SchNetPack input tensors for positions, neighbor indices, offsets, cell, atom counts, and atomic numbers.
- Stores total energy and forces back into LAMMPS data structures.

This means deployment metadata and atom-type mapping are critical. If cutoff metadata is absent or nonnumeric, LAMMPS cannot reliably configure the pair style.

## Recommended Agent Response Pattern

When a user asks for LAMMPS usage:

1. Ask for the trained model path, LAMMPS data/input files, atom-type-to-element mapping, and whether they want guidance only or authorized build/deployment actions.
2. If only deployment is needed, run or suggest `python scripts/deploy_for_lammps.py MODEL DEPLOYED --device cpu`.
3. If input editing is needed, update `pair_style`/`pair_coeff` with explicit atom-type mapping and point to the deployed model.
4. If build work is requested, call out external mutation and toolchain risks before making changes.
5. Never run long LAMMPS simulations as a verification default; suggest a small user-approved smoke run after build success.
