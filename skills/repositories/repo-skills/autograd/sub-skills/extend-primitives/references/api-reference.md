# API reference

## Modern imports

```python
from autograd.extend import primitive, defvjp, defjvp, defvjp_argnums, defjvp_argnums, vspace
from autograd.test_util import check_grads, combo_check
```

## Primitive authoring

- `primitive(fun)` or `@primitive` marks `fun` as a black-box primitive.
- `defvjp(fun, *vjpmakers, argnums=...)` registers staged reverse-mode rules.
- `defjvp(fun, *jvpfuns, argnums=...)` registers staged forward-mode rules.
- `defvjp_argnums(fun, maker)` and `defjvp_argnums(fun, maker)` let one maker share cached work across several argnums.

## Staged contracts

### `defvjp`

- maker signature: `vjpmaker(ans, *args, **kwargs) -> vjp`
- closure signature: `vjp(g) -> covector`
- `None` means the VJP is zero for that argnum.
- Use `vspace(x).zeros()` or `vspace(ans).zeros()` when you need a zero value with matching container semantics.

### `defjvp`

- maker signature: `jvpfun(g, ans, *args, **kwargs) -> tangent`
- `None` means the JVP is zero for that argnum.
- `"same"` means the tangent should flow through the primitive body unchanged.
- Use `vspace(...)` to build zero tangents with the right type and shape.

### `defvjp_argnums`

- maker signature: `maker(argnums, ans, args, kwargs) -> vjp`
- the returned `vjp(g)` should yield one covector per requested argnum, in the same order as `argnums`.
- prefer this when a single normalization, factorization, or shape analysis can be reused by several reverse-mode rules.

### `defjvp_argnums`

- maker signature: `maker(argnums, gs, ans, args, kwargs) -> tangent`
- `gs` contains the incoming tangents for the requested argnums.
- prefer this when one forward-pass cache can be shared across several tangents.

## Shared-work patterns

- Capture only the values needed by the returned closure; that is the main memory-management benefit of staged rules.
- If the derivative depends on both input and output shape, compute those shape facts in the maker and close over them.
- Keep the closure body differentiable if you expect higher-order derivatives.

## Compatibility wrappers

Legacy code may still call:
- `f.defvjp(...)`
- `f.defgrad(...)`
- `f.defvjp_is_zero(...)`
- `quick_grad_check(...)`

These remain for compatibility and emit warnings. Prefer `autograd.extend` and `check_grads` for new code.

## Gradient checking

- `check_grads(fun, modes=["rev"], order=2)(*args)` is the default smoke for a small fixture.
- Use `modes=["fwd", "rev"]` only when the primitive has both JVP and VJP rules.
- `combo_check(fun, modes=["rev"], order=2)` returns a checker that accepts candidate positional-argument lists and keyword lists, then evaluates the Cartesian product of every combination.
- If you intentionally leave an argnum undefined, the expected failure is `NotImplementedError` when differentiation reaches that path.
