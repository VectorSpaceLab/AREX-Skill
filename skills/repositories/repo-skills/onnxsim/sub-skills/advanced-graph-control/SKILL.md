---
name: advanced-graph-control
description: "Advanced graph-control workflows for ONNX Simplifier: custom
  rewriters, FunctionProto rules, metrics, graph diffs, metadata, and
  profiling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# advanced-graph-control

Use this sub-skill when the task is not just "simplify this ONNX model", but
needs control over the simplification fixed point, graph rewrite rules, schema
registration, graph inspection, model metrics, metadata annotations, or profiling
traces.

## Route first

- Basic CLI/Python simplification, input shapes, correctness checks, providers,
  external data, target opset, constant folding, and ordinary optimizer skipping
  belong in sibling sub-skill path `../python-simplification/SKILL.md`.
- Python wheel/source builds, C API, Rust API, WASM/Node/npm, and binding build
  commands belong in sibling sub-skill path `../bindings-and-packaging/SKILL.md`.
- This sub-skill owns the semantics of FunctionProto rewrite rules; C/Rust users
  can use the same rule bytes, but binding-specific invocation belongs to the
  bindings sub-skill.

## Primary references

- Rewriter, FunctionProto, and custom schema contracts:
  [`references/rewriters-and-rules.md`](references/rewriters-and-rules.md)
- ModelInfo, MACs/FLOPs/memory metrics, graph diff, metadata, and profiling:
  [`references/metrics-and-profiling.md`](references/metrics-and-profiling.md)
- Advanced graph-control failure modes:
  [`references/troubleshooting.md`](references/troubleshooting.md)

## Bundled smoke scripts

Run these from any environment where `onnx` and `onnxsim` are importable; they do
not require the original repository checkout.

```bash
python scripts/function_rule_smoke.py --help
python scripts/function_rule_smoke.py
python scripts/model_metrics_smoke.py --help
python scripts/model_metrics_smoke.py
```

- [`scripts/function_rule_smoke.py`](scripts/function_rule_smoke.py) builds a
  tiny `MatMul + Add` model, applies a pure-data FunctionProto rule that rewrites
  it to `Gemm`, skips the built-in Gemm fusion so the rule is provably
  responsible, and asserts the rewritten graph contains `Gemm`.
- [`scripts/model_metrics_smoke.py`](scripts/model_metrics_smoke.py) builds a
  tiny model, reports `ModelInfo` metrics, annotates metrics into
  `metadata_props`, and prints a compact graph-diff summary.

## Workflow: custom Python rewriter

Use `custom_rewriter=` when the rewrite is Python-only or needs a richer matcher
than onnxsim's built-in FunctionProto matcher.

1. Build or load an `onnx.ModelProto`.
2. Define a callable that accepts `onnx.ModelProto` and either:
   - returns a rewritten `onnx.ModelProto`,
   - mutates the input model in place and returns `None`, or
   - returns `False` when this fixed-point round changed nothing.
3. Call `onnxsim.simplify(model, custom_rewriter=callable, check_n=...)`.
4. Validate both the ONNX checker and, when safe, `check_n > 0`.
5. If a rewriter introduces custom-domain or newer-opset ops, register schemas or
   convert the model to the expected opset before simplification.

Prefer returning `False` on no-op rounds; it is the no-change sentinel that
prevents unnecessary serialize/parse copies and helps the fixed point converge.

## Workflow: binding-portable FunctionProto rule

Use `function_rewrite_rules=` when a rule can be expressed as pure ONNX graph
data and should also be usable from C or Rust.

1. Express a `(pattern, replacement)` pair as `onnx.FunctionProto` objects,
   usually with `onnx.parser.parse_function`.
2. Treat pattern inputs as wildcards; pattern outputs are rewired to replacement
   outputs.
3. Use `@name` / `ref_attr_name` for attribute wildcards that bind from the
   matched node and substitute into the replacement.
4. Pass `function_rewrite_rules=[(pattern, replacement)]` to `onnxsim.simplify`.
5. If a built-in optimizer would perform the same rewrite, pass
   `skipped_optimizers=["that_optimizer"]` while validating the rule itself.

`custom_rewriter` and `function_rewrite_rules` are mutually exclusive in one
`simplify()` call.

## Workflow: custom schemas

If the model contains custom ops that should remain schema-valid:

```python
import onnx
import onnxsim

onnx.defs.register_schema(my_op_schema)
# simplify() imports registered schemas automatically by default.
model_simp, ok = onnxsim.simplify(model)
```

Call `onnxsim.import_onnx_schemas()` explicitly when you need an import count or
want to prime the onnxsim registry. Disable the automatic import only when you
know the model does not require Python-registered schemas:
`onnxsim.simplify(model, import_custom_schemas=False)` or CLI
`--skip-schema-import`.

## Workflow: metrics, metadata, graph diff

Use `onnxsim.model_info` for static inspection without running inference:

```python
from onnxsim.model_info import ModelInfo, annotate_metadata, diff_graphs

info = ModelInfo(model)
annotated = annotate_metadata(model)
diff = diff_graphs(original_model, simplified_model)
```

Metrics include operator counts, serialized model size, MACs, FLOPs, memory
access, peak memory footprint, and compute density. Some values are symbolic
when dynamic dimensions are named and `sympy` is installed; otherwise unresolved
dimensions are best-effort lower bounds.

## Workflow: profile simplification

Use profiling when a simplification is unexpectedly slow, memory-heavy, or when
constant folding/optimizer cost attribution matters.

```python
model_simp, ok = onnxsim.simplify(model, profile="profile.json")
model_simp, ok = onnxsim.simplify(model, ort_profile="ort_profile")
model_simp, ok = onnxsim.simplify(
    model, profile="profile.json", merge_ort_profile=True
)
```

CLI equivalents are `--profile`, `--ort-profile`, and `--merge-ort-profile`.
Open Chrome trace JSON files in `chrome://tracing` or Perfetto. Use a scratch or
user-selected output directory for traces; do not leave large trace files in a
runtime skill directory.

## Validation checklist

- Run the bundled `--help` checks before relying on a script in a new environment.
- For rewrite rules, assert the intended op counts and run `onnx.checker`.
- For semantic rewrites, use `check_n` or explicit `input_data`; use `check_n=0`
  only for structural or intentionally semantics-changing transformations.
- For metrics, document whether dynamic shapes made values symbolic or lower
  bounds.
- For profiling, confirm the expected trace files exist and that environment
  variables used for profiling are not unintentionally left set after the call.
