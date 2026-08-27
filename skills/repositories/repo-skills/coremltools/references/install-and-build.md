# Install, Optional Dependencies, and Source-Build Notes

Read this when a task starts with installation, import failures, dependency selection, source builds, or repo-maintainer test commands.

## Public install path

For normal package use:

```bash
python -m pip install coremltools
python - <<'PY'
import coremltools as ct
print(ct.__version__)
print([unit.name for unit in ct.ComputeUnit])
PY
```

For a specific development release matching this skill snapshot:

```bash
python -m pip install coremltools==9.1.dev1
```

Use an isolated environment. Do not install every test/doc requirement just to convert a model; install only the optional source framework needed for the converter path.

## Minimal package requirements

The base distribution depends on NumPy, protobuf, sympy, tqdm, packaging, attrs, cattrs, and PyYAML/pyaml. Base install is enough for package import, MIL/source-independent inspection, spec utilities, and many non-framework APIs.

Optional source frameworks are separate:

```bash
# PyTorch conversion and coremltools.optimize.torch, choose a version compatible with your platform.
python -m pip install torch

# TensorFlow conversion, only when the target TensorFlow/Python pair is supported.
python -m pip install tensorflow

# Classic converters, install only what you need.
python -m pip install scikit-learn xgboost lightgbm libsvm
```

After installing optional dependencies, run the root diagnostic:

```bash
python scripts/check_coremltools_env.py
python scripts/check_coremltools_env.py --smoke
```

## Source checkout versus runtime wheel

A local editable checkout can expose the Python source but may not include native runtime libraries that packaged wheels provide. If `ct.convert(..., convert_to="mlprogram")` fails with `BlobWriter not loaded` or a missing `libmilstoragepython`, use one of these routes:

1. Install a compatible coremltools wheel for the same version/platform.
2. Build the source checkout with the repository build process and ensure the native libraries are on the package path.
3. If only MIL construction is being debugged, retry a neural-network conversion or `convert_to="milinternal"` to separate graph construction from ML Program package writing.

Linux wheels may still lack `libcoremlpython`; that is expected for prediction/runtime APIs. Use macOS for Core ML prediction, compiled model, compute device, and compute plan validation.

## Source-build script guidance

The repository includes maintainer scripts, but this generated skill does not copy them because they create environments, build wheels, or run broad test suites with side effects.

| Repo script family | Use case | Runtime-skill decision |
| --- | --- | --- |
| `scripts/build.sh` | Build coremltools from source with CMake and distribution outputs | Reference only; run from the repository only when intentionally building from source. |
| `scripts/env_create.sh`, `scripts/env_activate.sh` | Create/activate repo-specific conda development environments | Reference only; not needed for normal package operation. |
| `scripts/test.sh` | Full or focused repo unit-test launcher | Reference only; can be long-running and optional-dependency-heavy. |
| `scripts/build_docs.sh` | Build documentation | Reference only; maintainer docs workflow. |
| release/conda scripts | Release packaging | Excluded from runtime skill. |

If a user is contributing to the repository rather than operating the package as a library, treat these scripts as maintainer context and run only focused commands needed for the requested edit.

## Focused verification choices

- Package import: `python scripts/check_coremltools_env.py`.
- MIL package-writing smoke: `python scripts/check_coremltools_env.py --smoke`.
- PyTorch conversion smoke: `python sub-skills/convert-models/scripts/convert_torch_toy.py --output toy.mlpackage` after installing PyTorch.
- Artifact inspection: `python sub-skills/model-io-and-prediction/scripts/inspect_mlmodel.py Model.mlpackage --json`.
- Core ML optimization smoke: `python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --output optimized.mlpackage --compression linear`.
- Advanced MIL smoke: `python sub-skills/mil-and-debugging/scripts/mil_smoke.py --convert-to mlprogram --output mil_smoke.mlpackage`.

None of these helpers runs prediction by default. Add prediction checks only on a supported Core ML runtime.
