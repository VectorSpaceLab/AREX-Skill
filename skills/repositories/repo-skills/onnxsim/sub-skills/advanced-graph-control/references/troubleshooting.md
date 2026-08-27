# Troubleshooting advanced graph control

Use this reference when advanced rewriters, custom schemas, metrics, graph diff,
or profile traces fail. For ordinary input-shape/provider/external-data
simplification issues, route to the Python simplification sub-skill.

## Decision tree

1. Is the task only about invoking `onnxsim` or `onnxsim.simplify`? Use the
   Python simplification sub-skill.
2. Is the failure in a C/Rust/WASM build or binding invocation? Use the
   bindings-and-packaging sub-skill, then return here only for FunctionProto rule
   semantics.
3. Is a Python callback passed through `custom_rewriter`? Check the callback
   contract and schema validity.
4. Is a pure-data rule passed through `function_rewrite_rules`? Check matcher
   limits, FunctionProto parse validity, and competing built-in optimizers.
5. Is the task about metrics/profile output? Check shape inference warnings,
   optional dependencies, trace locations, and environment variables.

## `custom_rewriter` and `function_rewrite_rules` both passed

Signal:

```text
ValueError: custom_rewriter and function_rewrite_rules are mutually exclusive
```

Cause: onnxsim exposes one native rewriter slot in the simplification fixed
point.

Fix:

- Use `custom_rewriter=` for Python-only or predicate-heavy rewrite logic.
- Use `function_rewrite_rules=` for binding-portable pure-data FunctionProto
  rules.
- If both are needed, run two simplification passes and validate after each
  pass; do not pass both to one call.

## Python rewriter returns the wrong sentinel

Signals:

- Rewriter runs repeatedly and seems slow even after no rules fire.
- Type/assertion errors after the callback returns a non-model object.
- Earlier changes disappear because the callable returned the wrong value.

Fix:

- Return a rewritten `onnx.ModelProto` when you built a new model.
- Return `None` when you mutated the supplied model in place.
- Return exactly `False` when no rewrite happened in this fixed-point round.
- Do not use `False` after mutating the model in the same call; `False` means
  unchanged.

## Rewriter introduces invalid ops or invalid opsets

Signals:

- `onnx.checker.ValidationError`.
- Errors such as "No Op registered for ...".
- A model with a newer op, for example `Gelu`, fails under an older opset.

Fix:

- Keep replacement ops valid for the model's opset.
- Convert with `target_opset_version=` or `onnx.version_converter` before the
  rewrite if the pattern/replacement assumes a different opset.
- Register custom op schemas with Python ONNX and leave
  `import_custom_schemas=True` enabled.
- Call `onnxsim.import_onnx_schemas()` explicitly if you need to verify how many
  schemas were imported.
- If a CLI run must avoid schema import, use `--skip-schema-import` only when the
  model does not need Python-registered custom schemas.

## FunctionProto text does not parse

Signals:

- `onnx.parser.parse_function(...)` raises a parse error.
- A FunctionProto has missing domains, missing opsets, or malformed attribute
  syntax.

Fix:

- Include a function header with a domain and every required `opset_import`.
- Use ONNX text function syntax:

```text
<domain: "com.example", opset_import: ["" : 18]>
name (x, w, b) => (y)
{
    t = MatMul(x, w)
    y = Add(t, b)
}
```

- Use `@name` only for ref-attribute wildcards in node attributes, not for value
  inputs.
- Run the bundled FunctionProto smoke script to verify a known-good template:

```bash
python scripts/function_rule_smoke.py --help
python scripts/function_rule_smoke.py
```

## FunctionProto rule does not fire

Signals:

- Expected replacement op is absent.
- Op counts match a no-rule baseline.
- Built-in optimizer produced a similar result before the custom rule could be
  distinguished.

Fix:

- Skip competing optimizer passes while proving the rule, for example:
  `skipped_optimizers=["fuse_matmul_add_bias_into_gemm"]`.
- Check that the pattern is a connected DAG and that the candidate is in the
  top-level graph.
- Confirm op types, domains, opsets, attributes, and input/output arity match.
- For commutative matching, rely only on two-input binary commutativity; do not
  expect all permutations of larger expressions.
- If matching a `Constant`, ensure the tensor is byte-equal to the initializer or
  constant value in the graph.
- If an interior matched value is also consumed outside the pattern, onnxsim
  skips the rewrite to preserve graph validity. Broaden or change the pattern.

## Matcher limitation requires a richer rewriter

Use `custom_rewriter` rather than FunctionProto rules when you need:

- traversal or edits inside `If`, `Loop`, or `Scan` subgraphs;
- variadic/optional-input arity flexibility;
- more-than-two-operand commutative matching;
- arbitrary attribute predicates;
- attributes computed from the match;
- data-dependent graph analysis before rewriting;
- a third-party graph editor such as an onnxscript pattern pass.

Then validate with `onnx.checker`, `check_n`, and structural assertions.

## onnxscript optional dependency drift

Signals:

- `ModuleNotFoundError: onnxscript`.
- `onnxscript.rewriter.rules.common` missing.
- API differences around `RewritePass`, `ir.serde`, or `.to_function_proto()`.

Fix:

- For pure structural rules, avoid the dependency by authoring FunctionProtos
  directly with `onnx.parser.parse_function`.
- Treat onnxscript common-rule conversion as optional authoring convenience, not
  runtime requirement for `function_rewrite_rules`.
- If using `custom_rewriter` with onnxscript, pin or adapt to the installed
  onnxscript API and use the pass result's `modified` flag for the `False`
  sentinel.
- Do not claim a FunctionProto rule supports onnxscript-only constructs such as
  predicates or attribute arithmetic.

## `check_n` fails after a rewrite

Signals:

- `check_ok` is `False`.
- CLI exits nonzero after simplification and prints a warning about failed
  checking.

Fix:

- Treat this as a correctness risk, not a harmless warning.
- Re-run with deterministic `input_data` or a stable `input_fill` such as
  `ones`, `zeros`, or `arange` to reproduce.
- Inspect whether the rewrite is only structural and not semantics preserving.
- If floating-point reordering is expected and validated externally, adjust
  `check_rtol`/`check_atol` deliberately and document the risk.
- If the rewriter is intended only for graph surgery, use `check_n=0` and do not
  present it as a semantic simplification.

## Metrics look too small or zero

Signals:

- `ModelInfo(...).macs == 0` for nodes expected to be compute-heavy.
- Memory access or footprint is `0`.
- Warnings mention shape inference failure or failed function-body expansion.

Causes:

- Required shapes or dtypes are absent.
- Shape inference failed or could not infer an intermediate.
- The op is outside the supported MAC counter set.
- Function body inlining or schema-function expansion failed.
- `sympy` is unavailable, so dynamic dimensions collapse to representative value
  `1`.

Fix:

- Run ONNX shape inference or simplify enough to populate `value_info`.
- Add concrete or named dimensions where possible.
- Install `sympy` if symbolic formulas are needed.
- Interpret metrics as best-effort lower bounds when shapes are unknown.
- For unsupported ops, report op counts and model size rather than invented MACs.

## Metadata annotation surprises

Signals:

- `annotate_metadata()` output lacks expected per-value keys.
- Original model appears unmodified.
- A checker failure follows manual metadata edits.

Fix:

- `annotate_metadata()` intentionally returns a copy; save or use the returned
  model.
- Per-value `onnxsim.bytes` exists only when shape and dtype are known.
- Values are strings, including numeric-looking metrics.
- Use a namespaced custom prefix ending in a separator, such as `mytool.`.
- Run `onnx.checker.check_model(annotated)` after annotation and before saving.

## Graph diff output is noisy or incomplete

Signals:

- Many remove/add entries after a tool renamed values.
- Attribute-only changes are not listed.
- Control-flow branch edits are missing.

Cause: `diff_graphs()` matches top-level nodes by output tensor names and reports
op/input changes, added/removed nodes, and added/removed values.

Fix:

- Preserve value names in transformations when diff readability matters.
- Use `changed_nodes` for same-output op/input changes.
- Use a full ONNX/protobuf diff if attribute-only differences matter.
- Inspect subgraphs separately if `If`, `Loop`, or `Scan` bodies are the target.

## `profile` did not write the expected trace

Signals:

- `profile.json` missing.
- Default `onnxsim_profile.json` appears in the current directory instead of the
  intended path.
- A trace file exists but lacks expected ORT details.

Fix:

- Pass an explicit path: `onnxsim.simplify(model, profile="profile.json")` or
  CLI `--profile profile.json`.
- Remember that an empty string or bare `--profile` uses
  `onnxsim_profile.json` in the current working directory.
- Check permissions and whether the process changed directories.
- `profile` traces onnxsim's pipeline; use `ort_profile` or
  `merge_ort_profile=True` for ONNX Runtime per-operator events.

## `ort_profile` did not write ORT session traces

Signals:

- No `<prefix>_<timestamp>.json` files appear.
- Only the onnxsim profile file exists.

Causes and fixes:

- ORT traces are created only when ONNX Runtime sessions actually run. If no
  constant-folding or checking session executed, there may be no ORT trace.
- The value is a prefix; search the working directory for JSON files rather than
  only the literal prefix filename.
- Confirm `onnxruntime` is installed if native session profiling is required.
- Use `check_n=0` to reduce correctness-check session noise, or `check_n > 0`
  intentionally when you want those sessions profiled too.

## `merge_ort_profile` lacks ONNX Runtime events

Signals:

- The unified `profile` trace exists but has no events with category
  `onnxruntime`.
- No temporary ORT traces remain after the run.

Causes:

- Constant folding did not run any ONNX Runtime sessions.
- ONNX Runtime version could not redirect profile output in the expected way.
- Merge is best effort and suppresses failures so simplification can still
  succeed.

Fix:

- First run with standalone `ort_profile="prefix"` to see whether ORT emits
  traces in this environment.
- Confirm the onnxsim trace has `OrtSession` spans; merge needs those anchors.
- If using the manual helper, ensure ORT trace files are readable JSON and are
  under the directory passed to `merge_ort_traces_into_profile(profile, ort_dir)`.
- Treat missing merged ORT events as a profiling limitation, not as a failed
  simplification result.

## Environment variable leakage

Profile-related environment variables:

- `ONNXSIM_PROFILE`
- `ONNXSIM_PROFILE_INTERVAL_MS`
- `ONNXSIM_ORT_PROFILE`
- `ONNXSIM_MERGE_ORT_PROFILE`

Python keyword arguments and CLI flags set and restore the first two profile path
variables for the call. Manually exported variables affect every binding and can
surprise later runs.

Fix:

```bash
unset ONNXSIM_PROFILE ONNXSIM_ORT_PROFILE ONNXSIM_MERGE_ORT_PROFILE
```

Keep `ONNXSIM_PROFILE_INTERVAL_MS` only when you intentionally need a different
memory sampling interval.
