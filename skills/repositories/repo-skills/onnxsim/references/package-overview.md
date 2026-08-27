# Package Overview

Read this for the high-level ONNX Simplifier surface before choosing a sub-skill.

## Identity and install surface

- Distribution: `onnxsim`.
- Import package: `onnxsim`.
- Console script: `onnxsim`.
- Supported Python: `>=3.10`.
- Required runtime dependencies: `onnx`, `rich`.
- Optional extras:
  - `onnxsim[onnxruntime]` installs `onnxruntime >= 1.6.0` for the preferred constant-folding/checking backend.
  - `onnxsim[symbolic]` installs `sympy` so model metrics can preserve symbolic dynamic dimensions.

Minimal install and check:

```bash
python -m pip install -U onnxsim
python -c "import onnxsim; print(onnxsim.__version__)"
onnxsim --help
onnxsim --list-default-optimizers
```

If provider checks or constant-folding speed matter, install ONNX Runtime:

```bash
python -m pip install -U "onnxsim[onnxruntime]"
```

Use the bundled environment checker from the generated skill root when an installed environment is uncertain:

```bash
python scripts/check_onnxsim_env.py --help
python scripts/check_onnxsim_env.py --smoke --json
python scripts/check_onnxsim_env.py --providers CPUExecutionProvider --json
```

## Public Python API

Root exports:

```python
from onnxsim import simplify, import_onnx_schemas, main, __version__
```

`onnxsim.simplify(model, ...)` accepts either an ONNX file path or an in-memory `onnx.ModelProto` and returns `(simplified_model, check_ok)`. The full verified signature and option groups are in `../sub-skills/python-simplification/references/api-and-cli.md`.

Important supporting modules:

- `onnxsim.backend`: runs ONNX models through ONNX Runtime when installed, otherwise through ONNX's reference evaluator; also validates requested execution providers.
- `onnxsim.model_checking`: comparison and input-fill behavior for `check_n`.
- `onnxsim.model_info`: static op counts, model size, MACs/FLOPs, memory metrics, graph diff, and metadata annotation.
- `onnxsim.profile_merge`: merges ONNX Runtime per-operator traces into onnxsim's Chrome trace profile.
- `onnxsim.onnxsim_cpp2py_export`: compiled extension exposing the C++ simplification core to Python.

## Main workflows

| Workflow | Use | Route |
| --- | --- | --- |
| Simplify an ONNX model from CLI or Python | File-to-file conversion, `ModelProto` conversion, dynamic shape pinning, correctness checking, provider selection, external data, target opset, custom operator schema import | `../sub-skills/python-simplification/SKILL.md` |
| Author or debug graph-control hooks | Python `custom_rewriter`, pure-data `FunctionProto` rules, schema import, optimizer pass isolation | `../sub-skills/advanced-graph-control/SKILL.md` |
| Inspect metrics, diffs, and profiles | `ModelInfo`, `annotate_metadata`, `diff_graphs`, `--graph-diff`, `profile`, `ort_profile`, merged traces | `../sub-skills/advanced-graph-control/SKILL.md` |
| Build or package bindings | Python wheel/editable, CMake standalone/C API, Rust crates, WASM/npm/web demo, version sync | `../sub-skills/bindings-and-packaging/SKILL.md` |

## Runtime backend model

ONNX Simplifier's core loop alternates shape inference, optimizer passes, constant folding, and optional graph rewriting until a fixed point. Constant folding evaluates foldable subgraphs through a model executor:

- Python package path: uses a Python executor that calls the installed `onnxruntime` package when available and ONNX's reference evaluator otherwise.
- Default standalone C++/WASM/C API/Rust native-library path: can build/link ONNX Runtime into onnxsim when `ONNXSIM_BUILTIN_ORT=ON`.
- ORT-web WASM path: delegates folding to `onnxruntime-web` instead of compiling ONNX Runtime into the WASM module.

Do not confuse these paths: the Python wheel build deliberately passes `-DONNXSIM_BUILTIN_ORT=OFF` and does not compile vendored ONNX Runtime C++.

## Validation expectations

For ordinary user work:

1. Start with `onnxsim --help`, `onnxsim --list-default-optimizers`, or `python scripts/check_onnxsim_env.py --smoke`.
2. For model simplification, use `check_n > 0` or explicit validation inputs when correctness matters.
3. Treat `check=False`, provider validation errors, and custom-op schema failures as actionable signals, not harmless warnings.
4. Use `--graph-diff` or `onnxsim.model_info.diff_graphs` to understand structural changes.
5. Use optional provider, web, Rust, or C API workflows only when the caller selected that surface.
