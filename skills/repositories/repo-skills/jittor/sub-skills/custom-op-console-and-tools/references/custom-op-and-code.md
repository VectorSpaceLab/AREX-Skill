# Custom ops and `jt.code`

This reference covers public extension surfaces for advanced Jittor users. Keep the workflow CPU-first unless the user explicitly asks for CUDA-specific behavior and the runtime confirms CUDA support.

## Choose the smallest extension surface

| Surface | Use when | Avoid when |
| --- | --- | --- |
| Meta-operators (`reindex`, `broadcast_var`, reductions, elementwise ops) | The operation can be expressed as index remapping plus elementwise/reduction algebra. Jittor can fuse the resulting graph. | You need external C++ libraries, custom device code, or irregular side effects. |
| `jt.code` | A small inline kernel is enough and output shape/dtype are known from Python. Good for elementwise, reduction-like, or glue kernels. | The code becomes a reusable op class, needs many source files, or requires complex build flags. |
| `jt.compile_custom_op` | One custom op class can be provided as header/source strings. Good for a larger op while still drafting inside Python. | You already maintain multiple paired source files or need module-level exports. |
| `jt.compile_custom_ops` | Multiple paired `*_op.h`/`*_op.cc`/`*.cu` files should be compiled into one module. | You only need a few lines of inline code; start with `jt.code`. |
| `jt.numpy_code` | Python/Numpy or optional CuPy callback code is acceptable and performance is not the primary goal. | The user needs pure C++/CUDA deployment or deterministic JIT-compiled kernels. |

## `jt.code` API contract

Common form:

```python
out = jt.code(shape, dtype, inputs, cpu_src="...", cpu_header="...")
```

Useful overloads include:

- Single output: `jt.code(shape, dtype, inputs, ...) -> Var`.
- Multiple outputs: `jt.code([shape0, shape1], [dtype0, dtype1], inputs, ...) -> tuple[Var, ...]`.
- Write into existing outputs: `jt.code(inputs, outputs, ...)`.

Inside `cpu_src` or `cuda_src`, Jittor expands built-ins such as:

- `in0_shape0`, `in0_shape1`, `in0_p`, `in0_type`, `@in0(i, j)` for inputs.
- `out_shape0`, `out0_shape0`, `out_p`, `out0_p`, `@out(i)`, `@out0(i)` for outputs.
- `@alias(name, in0)` to make shorter aliases in a header/source string.
- For CUDA snippets, `@ARGS_DEF`, `@PRECALC`, and `@ARGS` help pass Jittor-managed buffers and metadata into the kernel.

A tiny CPU elementwise pattern:

```python
import numpy as np
import jittor as jt

x = jt.array(np.arange(4, dtype="float32"))
y = jt.code(
    x.shape,
    x.dtype,
    [x],
    cpu_src=r"""
        for (int i=0; i<in0_shape0; ++i) {
            @out(i) = @in0(i) * @in0(i) + (float)1;
        }
    """,
)
assert np.allclose(y.data, np.arange(4, dtype="float32") ** 2 + 1)
```

A conceptual CUDA pattern, guarded separately from CPU verification:

```python
if getattr(jt.compiler, "has_cuda", False):
    with jt.flag_scope(use_cuda=1):
        y = jt.code(
            x.shape,
            x.dtype,
            [x],
            cuda_src=r"""
                __global__ static void kernel(@ARGS_DEF) {
                    @PRECALC
                    int i = threadIdx.x + blockIdx.x * blockDim.x;
                    if (i < in0_shape0) @out(i) = @in0(i) * (float)2;
                }
                kernel<<<(in0_shape0 + 255) / 256, 256>>>(@ARGS);
            """,
        )
        y.sync()
```

Do not run CUDA-only snippets when CUDA is not present. Provide a CPU `cpu_src` path first whenever the user needs portable guidance.

## Gradients and multi-output code ops

- `cpu_grad_src` and `cuda_grad_src` are lists aligned with differentiable inputs.
- For complex backward logic, wrap `jt.code` in a `jittor.Function` subclass: save inputs in `execute`, then return code-op gradients from `grad`.
- Multiple outputs require a list of output shapes and dtypes. Refer to them with `@out0`, `@out1`, and shape variables such as `out0_shape0`.
- Dynamic output lengths can be declared with a negative maximum shape and set inside source via `out->set_shape({...})` or `out0->set_shape({...})`; verify bounds with small inputs before scaling.

## Custom op API contract

### `compile_custom_op`

Use `jt.compile_custom_op(header, source, op_name, warp=True)` when one op class is enough.

- `header` and `source` are code strings, not file paths.
- `op_name` is the Python-exported operation name and should match the op class convention. For example, op name `my` pairs with a class like `MyOp` whose `name()` returns `"my"`.
- With `warp=True`, Jittor wraps the snippets with common includes and the `jittor` namespace. With `warp=False`, provide the full header/source envelope yourself.
- The C++ op constructor creates outputs, `jit_prepare` adds dtype/shape defines, and `jit_run` implements CPU and/or CUDA branches.

Minimal structure checklist for a wrapped single op:

```cpp
// header snippet
struct MyOp : Op {
    Var* output;
    MyOp(NanoVector shape, NanoString dtype=ns_float32);
    const char* name() const override { return "my"; }
    DECLARE_jit_run;
};
```

```cpp
// source snippet
#ifndef JIT
MyOp::MyOp(NanoVector shape, NanoString dtype) {
    output = create_output(shape, dtype);
}
void MyOp::jit_prepare(JK& jk) {
    add_jit_define(jk, "T", output->dtype());
}
#else
void MyOp::jit_run() {
    index_t n = output->num;
    auto* out = output->ptr<T>();
    for (index_t i=0; i<n; ++i) out[i] = (T)i;
}
#endif
```

After compilation, call the returned Python function with the op constructor arguments and verify shape, dtype, and values:

```python
my = jt.compile_custom_op(header, source, "my")
out = my([3, 4], "float")
assert out.shape == [3, 4]
assert out.dtype == "float"
```

### `compile_custom_ops`

Use `jt.compile_custom_ops(filenames, extra_flags="", return_module=False, dlopen_flags=None, gen_name_="")` for paired source files.

Rules to enforce before compiling:

- File basenames should be paired as `xxx_xxx_op.h` and `xxx_xxx_op.cc`/`.cpp`/`.cu`.
- Type names should follow the basename convention, such as `XxxXxxOp` for `xxx_xxx_op.*`.
- Header/source counts must match; missing headers or source files are rejected.
- Add include directories and compile defines through `extra_flags` or op `compile_options`, not by depending on a source checkout.
- If `return_module=False`, the return object exposes compiled op callables; if `return_module=True`, consume the module object directly.

## Meta-operator design pattern

Meta-operators express tensor programs in terms of reindexing, broadcasting, reductions, and elementwise operations. They are often safer than custom C++ because Jittor can fuse and optimize them without hand-written kernels.

A convolution-like sketch:

```python
def conv_meta(x, w):
    # x: [N, H, W, C], w: [Kh, Kw, C, Kc]
    N, H, W, C = x.shape
    Kh, Kw, C2, Kc = w.shape
    assert C == C2
    patches = x.reindex(
        [N, H-Kh+1, W-Kw+1, Kh, Kw, C, Kc],
        ["i0", "i1+i3", "i2+i4", "i5"],
    )
    return (patches * w.broadcast_var(patches)).sum([3, 4, 5])
```

Use this pattern when the task is indexing algebra. Verify boundary conditions (`H >= Kh`, `W >= Kw`), output layout, dtype, and numeric parity with a tiny NumPy or Jittor reference. Enable tuning only after correctness is proven.

## CPU-first then CUDA extension workflow

1. Implement and verify a tiny CPU `jt.code` or CPU branch in a custom op.
2. Assert shape, dtype, and numeric values with a small deterministic input.
3. Add gradient source or a `Function.grad` wrapper only after forward correctness passes.
4. Add `cuda_src` or a `JIT_cuda` branch behind `jt.compiler.has_cuda` and `jt.flag_scope(use_cuda=1)`.
5. Report CPU verification and CUDA verification separately. If CUDA is unavailable, leave the CUDA claim as unverified rather than implying CPU coverage proves it.

For a quick local sanity check, run `scripts/custom_op_smoke.py --help` and then choose `--skip-compile`, the default CPU smoke, or optional `--try-cuda`.
