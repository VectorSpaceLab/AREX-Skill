---
name: onnxsim
description: "Repo skill for ONNX Simplifier: ONNX model simplification, graph
  rewriting, metrics, profiling, packaging, and bindings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX Simplifier (`onnxsim`)

Use this repo skill when a task involves ONNX Simplifier / `onnxsim`: simplifying
exported ONNX graphs, validating simplified models, controlling optimizer and
constant-folding behavior, using custom rewrite rules, inspecting model metrics
or profile traces, or maintaining the package's Python/C++/Rust/WASM bindings.

## Start here

- Read [package overview](references/package-overview.md) for package identity,
  install commands, backend model, and route selection.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) when the
  failure surface is unclear.
- Read [repository provenance](references/repo-provenance.md) before deciding
  whether this skill is current for a checkout or before running a refresh.
- `references/repo-routing-metadata.json` is structured metadata for managed
  repo-skill import; do not hand-edit router Markdown.

## Minimal installed-package check

```bash
python -m pip install -U onnxsim
python -c "import onnxsim; print(onnxsim.__version__)"
onnxsim --help
onnxsim --list-default-optimizers
```

If an environment may be broken, run the bundled checker from this skill root:

```bash
python scripts/check_onnxsim_env.py --help
python scripts/check_onnxsim_env.py --smoke --json
python scripts/check_onnxsim_env.py --providers CPUExecutionProvider --json
```

The checker imports `onnxsim`, verifies the compiled extension, reports optional
ONNX Runtime providers, probes the CLI optimizer list, and can run a tiny
in-memory simplification smoke.

## Route by task

| User task | Read |
| --- | --- |
| Simplify an ONNX file with the CLI, set input shapes, run correctness checks, choose CPU/CUDA providers, save external data, convert target opset, or use custom operator schemas | [`sub-skills/python-simplification/SKILL.md`](sub-skills/python-simplification/SKILL.md) |
| Call `onnxsim.simplify` from Python with `ModelProto` objects, inspect the full API signature, map CLI flags to parameters, or recover from model/check/provider errors | [`sub-skills/python-simplification/SKILL.md`](sub-skills/python-simplification/SKILL.md) |
| Author Python `custom_rewriter` callbacks, pure-data `FunctionProto` rewrite rules, or custom schema import logic | [`sub-skills/advanced-graph-control/SKILL.md`](sub-skills/advanced-graph-control/SKILL.md) |
| Use `ModelInfo`, MACs/FLOPs/memory metrics, `annotate_metadata`, `diff_graphs`, `--graph-diff`, `profile`, `ort_profile`, or merged ONNX Runtime traces | [`sub-skills/advanced-graph-control/SKILL.md`](sub-skills/advanced-graph-control/SKILL.md) |
| Install/build from source, diagnose missing submodules/nanobind/protobuf/CMake, build the C API, use Rust crates, build WASM/npm/web demo, or check release versions | [`sub-skills/bindings-and-packaging/SKILL.md`](sub-skills/bindings-and-packaging/SKILL.md) |

## Key operating facts

- `onnxsim.simplify(model, ...)` accepts an ONNX file path or an in-memory
  `onnx.ModelProto` and returns `(simplified_model, check_ok)`.
- CPU constant folding is the default. `onnxruntime` is optional for the Python
  package; without it, onnxsim can use ONNX's reference evaluator.
- Non-CPU execution providers require ONNX Runtime with the matching provider
  build. `--cuda` means `--providers CUDAExecutionProvider CPUExecutionProvider`.
- Custom operator schemas registered in Python ONNX are imported into onnxsim's
  registry by default; CLI users can disable that with `--skip-schema-import`.
- Python `custom_rewriter` callbacks and pure-data `function_rewrite_rules` are
  mutually exclusive in one `simplify()` call.
- FunctionProto rewrite rules are portable to C/Rust bindings because they are
  protobuf data matched in the C++ core.
- `ModelInfo` and `annotate_metadata` are static inspection tools; unknown shapes
  or missing optional `sympy` can make metrics best-effort or symbolic.
- The Python wheel/editable build uses `-DONNXSIM_BUILTIN_ORT=OFF`; it does not
  compile vendored ONNX Runtime C++. ONNX Runtime C++ builds belong to standalone
  CMake/C API/Rust native-library/default-WASM paths.

## Bundled scripts

- [`scripts/check_onnxsim_env.py`](scripts/check_onnxsim_env.py): installed
  package, provider, CLI, and tiny simplification smoke checker.
- [`sub-skills/python-simplification/scripts/simplify_tiny_model.py`](sub-skills/python-simplification/scripts/simplify_tiny_model.py): safe tiny model simplification helper.
- [`sub-skills/advanced-graph-control/scripts/function_rule_smoke.py`](sub-skills/advanced-graph-control/scripts/function_rule_smoke.py): pure-data FunctionProto rewrite smoke.
- [`sub-skills/advanced-graph-control/scripts/model_metrics_smoke.py`](sub-skills/advanced-graph-control/scripts/model_metrics_smoke.py): metrics, metadata, and graph-diff smoke.
- [`sub-skills/bindings-and-packaging/scripts/check_version_sync.py`](sub-skills/bindings-and-packaging/scripts/check_version_sync.py): read-only version metadata checker for a user-supplied source tree.

## Safe defaults

- Prefer a released wheel plus `onnxsim --help` / `--list-default-optimizers` for
  ordinary use.
- Use `check_n`, deterministic `input_fill`, and explicit `test_input_shapes`
  when correctness matters.
- Start optional provider and build investigations with help/version/smoke
  checks; do not install heavy CUDA/QNN/TVM/Halide/model-export stacks or launch
  long WASM/Rust/native builds unless the user explicitly selected that path.
- Treat `check_ok=False`, provider validation errors, and schema validation
  errors as blockers for deployment-style tasks until the user accepts the risk
  or the issue is fixed.
