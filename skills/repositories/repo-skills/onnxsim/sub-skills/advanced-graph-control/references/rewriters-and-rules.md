# Rewriters, FunctionProto rules, and custom schemas

This reference covers advanced graph-control inputs to `onnxsim.simplify`:
Python callbacks via `custom_rewriter`, binding-portable FunctionProto rules via
`function_rewrite_rules`, and custom ONNX schema import. For ordinary model
simplification options, use the Python simplification sub-skill.

## Relevant `simplify()` parameters

Advanced graph-control parameters are keyword-only in the public Python API:

```python
onnxsim.simplify(
    model,
    *,
    inline_functions=False,
    import_custom_schemas=True,
    target_opset_version=None,
    custom_rewriter=None,
    function_rewrite_rules=None,
    skipped_optimizers=None,
    check_n=0,
    check_rtol=1e-4,
    check_atol=1e-5,
    input_fill="random",
)
```

Important constraints:

- `model` can be a path or `onnx.ModelProto`.
- `custom_rewriter` and `function_rewrite_rules` share one native rewriter slot;
  passing both raises `ValueError`.
- The rewriter runs inside onnxsim's fixed point, interleaved with shape
  inference, optimizer passes, and constant folding.
- Use `skipped_optimizers=[...]` when a built-in optimizer would hide whether
  your rule fired.
- Use `inline_functions=True` when local model-defined functions should be
  flattened before simplification; schema-defined built-in functions are not
  inlined by that option.

## Custom Python rewriter contract

`custom_rewriter` is a Python callable:

```python
Callable[[onnx.ModelProto], onnx.ModelProto | bool | None]
```

Return choices:

| Return value | Meaning | When to use |
| --- | --- | --- |
| `onnx.ModelProto` | Use this rewritten model for the current fixed-point round. | Your rewriter returns a new object or a serialized/deserialized output from a library. |
| `None` | The callable mutated the input `ModelProto` in place; use that object. | Hand-written graph edits over `model.graph.node`, initializers, or attributes. |
| `False` | Nothing changed this round; keep the current model and skip copy-back. | A matcher ran and found no match, especially in the final no-op round. |

Do **not** return arbitrary truthy/falsey objects. `False` is a sentinel for
"unchanged"; `None` means "use the mutated input model".

### Plain Python example

```python
import onnx
import onnxsim


def relu_to_sigmoid(model: onnx.ModelProto):
    changed = False
    for node in model.graph.node:
        if node.op_type == "Relu":
            node.op_type = "Sigmoid"  # schema-valid in common ONNX opsets
            changed = True
    return None if changed else False

model_simp, ok = onnxsim.simplify(model, custom_rewriter=relu_to_sigmoid)
onnx.checker.check_model(model_simp)
```

This structural example is not generally semantics preserving. Use `check_n` or
explicit test inputs only for rewrites that are meant to preserve semantics.

### onnxscript rewriter pathway (optional)

`onnxscript` is optional. When available, its pattern rewriter can drive
`custom_rewriter`:

```python
import onnxsim
from onnxscript.rewriter import pattern, rewrite


def matmul_add_pattern(op, x, w, b):
    return op.Add(op.MatMul(x, w), b)


def gemm_replacement(op, x, w, b):
    return op.Gemm(x, w, b)

rules = pattern.RewriteRuleSet([
    pattern.RewriteRule(matmul_add_pattern, gemm_replacement)
])
model_simp, ok = onnxsim.simplify(
    model,
    custom_rewriter=lambda m: rewrite(m, pattern_rewrite_rules=rules),
    check_n=1,
)
```

For better fixed-point performance, prefer the onnx-ir `PassManager` form when
available and return `False` when no rule fired:

```python
from onnxscript import ir
from onnxscript.rewriter import RewritePass, pattern

rules = pattern.RewriteRuleSet([
    pattern.RewriteRule(matmul_add_pattern, gemm_replacement)
])
rewrite_pass = ir.passes.PassManager([RewritePass(rules)])


def apply_rules(model):
    model_ir = ir.serde.deserialize_model(model)
    result = rewrite_pass(model_ir)
    if not result.modified:
        return False
    return ir.serde.serialize_model(result.model)

model_simp, ok = onnxsim.simplify(model, custom_rewriter=apply_rules)
```

Use the pass result's `modified` flag, not byte comparison: IR round-trips can
change serialization order even when no graph rewrite occurred.

## FunctionProto rewrite rules

`function_rewrite_rules` is a sequence of pure-data rules:

```python
Sequence[tuple[onnx.FunctionProto, onnx.FunctionProto]]
```

Each pair is `(pattern, replacement)`:

- Pattern inputs are wildcards that bind graph values.
- Pattern body nodes describe the connected subgraph to match.
- Pattern outputs identify the values that will be rewired.
- Replacement inputs use the same bound names as the pattern inputs.
- Replacement outputs replace the matched pattern outputs.
- Node attributes written as `@name` in ONNX text are ref-attribute wildcards;
  they bind the matched attribute and substitute it into the replacement.

Because these rules are protobuf data and are applied in onnxsim's C++ core, the
same rule bytes can be used by C and Rust callers. Authoring can still happen in
Python.

### Author with ONNX text

```python
from onnx import parser
import onnxsim

pattern = parser.parse_function('''
<domain: "com.example", opset_import: ["" : 18]>
matmul_add_pattern (x, w, b) => (y)
{
    t = MatMul(x, w)
    y = Add(t, b)
}
''')
replacement = parser.parse_function('''
<domain: "com.example", opset_import: ["" : 18]>
gemm_replacement (x, w, b) => (y)
{
    y = Gemm(x, w, b)
}
''')

model_simp, ok = onnxsim.simplify(
    model,
    skipped_optimizers=["fuse_matmul_add_bias_into_gemm"],
    function_rewrite_rules=[(pattern, replacement)],
    check_n=1,
)
```

The skipped optimizer is important for validation: without it, the built-in
Gemm fusion might produce the same final graph before your rule proves itself.

### Attribute wildcard example

```python
pattern = parser.parse_function('''
<domain: "com.example", opset_import: ["" : 18]>
relu_leaky (x) => (y)
{
    t = Relu(x)
    y = LeakyRelu <alpha = @a> (t)
}
''')
replacement = parser.parse_function('''
<domain: "com.example", opset_import: ["" : 18]>
leaky (x) => (y)
{
    y = LeakyRelu <alpha = @a> (x)
}
''')
```

Here `@a` binds the matched `LeakyRelu` node's `alpha` attribute and copies it to
the replacement node.

### Author with onnxscript `@script` (optional)

When `onnxscript` is installed, structural executable functions can be converted
to FunctionProtos:

```python
from onnxscript import opset18 as op
from onnxscript import script

@script()
def matmul_add(a, b, c):
    return op.Add(op.MatMul(a, b), c)

@script()
def gemm(a, b, c):
    return op.Gemm(a, b, c)

rule = (matmul_add.to_function_proto(), gemm.to_function_proto())
model_simp, ok = onnxsim.simplify(model, function_rewrite_rules=[rule])
```

A Python-typed attribute parameter, such as `alpha: float`, compiles to an ONNX
ref attribute and becomes the same wildcard mechanism as `@alpha`.

`@script` is useful for structural patterns. It does not express matcher-only
constructs such as arbitrary predicates, value alternatives, or attributes
computed from the match. Use Python `custom_rewriter` for those.

## Built-in matcher capabilities

The native FunctionProto matcher supports:

- top-level graph matching;
- arbitrary connected DAG patterns with one or more outputs;
- commutative two-input binary ops such as `Add` and `Mul` in either operand
  order;
- exact attribute matching;
- ref-attribute wildcards (`@name` / `ref_attr_name`);
- matching a pattern `Constant` against a byte-equal initializer;
- batching independent non-overlapping matches in one round;
- skipping rewrites that would break an interior value used outside the match.

Known limits in this version:

- no traversal into `If`, `Loop`, or `Scan` subgraph bodies;
- no variadic or optional-input arity mismatch handling;
- no exhaustive permutations for more than two operands of a commutative op;
- no arbitrary predicate evaluation;
- no attribute arithmetic or attribute values derived by custom code;
- overlapping matches are resolved conservatively across fixed-point rounds.

When a rule needs a limit above, use a Python `custom_rewriter` or a richer
rewriter library and validate the output carefully.

## Custom operator schema import

onnxsim links its own ONNX C++ registry, separate from the Python `onnx` module.
If a model uses a custom op, register its schema with Python ONNX and let onnxsim
import it before validation:

```python
import onnx
import onnxsim

onnx.defs.register_schema(my_op_schema)
imported = onnxsim.import_onnx_schemas()  # optional, returns an import count
model_simp, ok = onnxsim.simplify(model)  # imports schemas automatically too
```

Operational facts:

- `import_custom_schemas=True` is the default for `simplify()`.
- CLI users can disable automatic import with `--skip-schema-import`.
- A schema with a type/shape-inference function is registered with a trampoline
  so shape inference can call back through Python ONNX.
- A schema without inference can still be imported; shape inference flows past
  the custom op.
- Introduced replacement ops must be valid at the model's target opset. Use
  `target_opset_version=` or pre-convert the model when your rule assumes a
  newer opset.

## Validation pattern for rewrite work

1. Run a no-rewrite baseline if you need to prove what onnxsim does by itself.
2. Skip competing built-in optimizers while proving a custom rule.
3. Assert graph structure with op counts and key input/output names.
4. Run `onnx.checker.check_model(model_simp)`.
5. Run semantic checks (`check_n`, explicit `input_data`, or downstream tests)
   for any semantics-preserving rule.
6. Keep rules pure-data if they must be portable to bindings; otherwise document
   that a Python callback is required.
