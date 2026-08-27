# LinearRNA Build and Troubleshooting

Use this reference when LinearFold or LinearPartition imports fail, a CMake extension build fails, or a user asks how to repair a missing `linear_rna` extension.

## What Must Exist

LinearRNA is a compiled pybind11 extension, not a pure Python module. A working environment needs:

- Python compatible with the PaddleHelix installation being used.
- Base Python dependencies such as `numpy`, `pandas`, `networkx`, and `scikit-learn`.
- CMake `>=3.6` for extension configuration.
- A C++ compiler compatible with C++11, with the original developer guidance calling out `g++ >=4.8`.
- pybind11 source available to CMake, normally through the `third-party/pybind11` submodule.
- A CMake build backend such as Ninja, Make, or an explicitly selected generator.
- The compiled `linear_rna` pybind module installed or discoverable in the package/build output; source-layout `pahelix` import alone does not prove the extension is available.

## Import Symptoms

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pahelix.toolkit.linear_rna'` | Package installed without the compiled extension, or Python cannot see the package installation. | Run the bundled checker to confirm import failure, then verify the package install/build logs. |
| `ModuleNotFoundError: No module named 'linear_rna'` when testing a build tree | The build directory does not contain the compiled pybind module or is not on `PYTHONPATH`. | Rebuild the extension or point the checker at the build/package root with `--repo-root`. |
| `ModuleNotFoundError: No module named 'c.pahelix.toolkit.linear_rna.linear_rna'` | Developer-style build output is not importable from the current working directory. | Prefer installed-package import, or add the build root only for diagnosis. |
| Import succeeds but API call returns `('', 0)` | Invalid RNA sequence, invalid constraints, or no valid constrained fold. | Validate sequence and constraints with `scripts/check_linear_rna.py` before retrying. |
| `TypeError` for `no_sharpe_turn` | README typo copied into code. | Use keyword `no_sharp_turn`; that is what the pybind module exports. |

## Safe Build Guidance

The original repository's setup and developer scripts build LinearRNA through CMake and pybind11. Future agents should avoid running repository-mutating scripts unless the user explicitly wants to build or repair a checkout.

A safe build diagnosis sequence is:

1. Confirm the user wants a local build, because preparing pybind11 submodules and compiling C++ mutates/builds a checkout.
2. Check for CMake and compiler availability with read-only version commands.
3. Check whether a `third-party/pybind11` tree already exists before adding or updating submodules; the original preparation script creates that directory and adds a git submodule, so it is not read-only.
4. Install `scikit-learn` directly rather than relying on the deprecated `sklearn` package name. If a legacy install path still requires `sklearn`, use the compatibility environment variable only as a short-term workaround.
5. If the build chooses Ninja automatically and fails with no build program, install Ninja or set `CMAKE_GENERATOR` to a generator available on the machine.
6. Rebuild the extension, then run the bundled checker on a toy sequence before using user data.

## Distilled Build Route

The developer build route consists of these concepts:

- Prepare pybind11 under `third-party/pybind11` if it is missing.
- Configure from the repository root with CMake.
- Build the C++ extension target.
- Ensure Python can import the resulting extension module from the installed package namespace, developer build namespace, or direct pybind module name.

Do not bundle or blindly run the original shell scripts as runtime helpers: one script adds/updates a git submodule and the other creates a build directory and compiles the checkout. Those actions are useful for a maintainer, but they are not safe default behavior for a skill helper.

## CMake and pybind11 Failures

| Failure text | Meaning | Fix |
| --- | --- | --- |
| `CMake missing` or `cmake: command not found` | CMake is not installed or not on `PATH`. | Install CMake for the current environment and rerun the build. |
| `add_subdirectory(third-party/pybind11)` fails | pybind11 submodule/source tree is missing. | Initialize or provide pybind11 only after user approval for checkout mutation. |
| `pybind11_add_module` unknown | CMake did not load pybind11's CMake helpers. | Verify the pybind11 tree and CMake include path before retrying. |
| `No CMAKE_CXX_COMPILER could be found` | No usable C++ compiler. | Install a compiler toolchain before rebuilding. |
| `ninja: not found` or CMake selected Ninja but cannot run it | Setup selected Ninja automatically for non-MSVC builds. | Install Ninja or set `CMAKE_GENERATOR` to an available generator before build. |
| Compilation fails in C++ sources | Toolchain or source compatibility issue. | Capture compiler version, Python version, CMake generator, and the first real compiler error; avoid hiding it behind repeated rebuilds. |

## Dependency Caveats

- Modern pip rejects the deprecated `sklearn` dependency package by default. Install `scikit-learn` directly; only use `SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True` for legacy compatibility when the user accepts that workaround.
- PaddlePaddle, PGL, and RDKit are important optional dependencies for many PaddleHelix workflows, but they were intentionally outside the minimal LinearRNA inspection environment. Do not install broad GPU/model dependencies just to diagnose `linear_rna` import errors.
- Avoid downloading benchmark datasets such as ArchiveII or RNAcentral for import/API smoke checks. Toy sequences are enough to prove the extension works.

## Input Troubleshooting

Use `scripts/check_linear_rna.py` for input-side failures before blaming the extension:

- Invalid sequence characters: normalize `T` to `U`, then accept only `A`, `C`, `G`, `U` for reliable LinearRNA usage.
- Constraint length mismatch: make the constraint exactly as long as the sequence after normalization.
- Unbalanced constraint parentheses: every `(` must close later with a `)` and nesting must be proper.
- Non-canonical forced pairs: constrained pairs must be AU, UA, CG, GC, GU, or UG.
- No valid constrained fold: try a smaller set of constraints, verify forced pairs, then consider `no_sharp_turn=False` only when the task specifically allows sharp turns.
- Oversized partition output: raise `bp_cutoff` to keep base-pair probability output readable.

## Minimal Validation Commands

```bash
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GGGAAACCC --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model c
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence UGAGUUCUCGAUCUCUAAAAUCG --partition --bp-cutoff 0.2 --model v
python sub-skills/linear-rna/scripts/check_linear_rna.py --sequence GAAAC --constraint '(...)'
```

If these commands fail only at import time, the inputs are likely fine and the environment/build needs attention.
