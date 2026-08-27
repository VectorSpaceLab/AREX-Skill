# Newton development and maintenance guidance

Read this when the user is editing Newton source, adding public APIs, examples, tests, or docs. For ordinary package usage, start with the root router and workflow sub-skills instead.

## Public API boundary

- Public API is exposed through `newton`, `newton.geometry`, `newton.solvers`, `newton.utils`, `newton.sensors`, `newton.viewer`, and other non-private public modules.
- Do not import from `newton._src` in examples, docs, or user-facing snippets.
- Breaking public API changes require deprecation first.
- Prefer prefix-first names for discoverability, such as `ActuatorPD`-style classes or `add_shape_sphere()`-style methods.

## Type and doc conventions

- Use PEP 604 unions, such as `x | None`.
- Annotate Warp arrays with bracket syntax such as `wp.array[wp.vec3]` and `wp.array2d[float]`; do not use parenthesized `wp.array(dtype=...)` in type annotations.
- Use Google-style docstrings with types in annotations, not duplicated in `Args:`.
- Public physical quantities should include SI units and shapes where applicable.
- Use public Sphinx cross-references and never reference `newton._src` in public docs.
- Keep code comments brief and explain why, not what.

## Builder/API patterns

Shape-builder methods follow a stable vocabulary:

```python
def add_shape_something(
    self,
    body: int,
    *,
    xform: Transform | None = None,
    # shape-specific parameters,
    cfg: ShapeConfig | None = None,
    as_site: bool = False,
    color: Vec3 | None = None,
    label: str | None = None,
    custom_attributes: dict[str, Any] | None = None,
) -> int:
    ...
```

Use `xform`, `cfg`, `body`, `label`, and `custom_attributes` consistently. Defaults should be `None`, not constructed Warp objects.

Nested enums should be integer enums where stable sentinel values matter; `NONE = 0` should come first when a `NONE` member exists.

## Tests and examples

- Use `unittest`, not pytest, for Newton tests.
- Every test function/method should have a triple-double-quoted docstring starting with a concise imperative summary.
- Do not call `wp.synchronize()` or `wp.synchronize_device()` immediately before `.numpy()`; `.numpy()` synchronizes the device-to-host copy.
- Examples should follow the `Example` class format and implement `test_final()` when they are registered as examples.
- Register examples in the README with a `python -m newton.examples <name>` command and a screenshot when adding user-facing examples.

Focused commands:

```bash
uv run --extra dev -m newton.tests
uv run --extra dev -m newton.tests -k test_viewer_log_shapes
uv run --extra dev -m newton.tests -k test_basic.example_basic_shapes
uv run --extra examples -m newton.examples basic_pendulum --viewer null --test
```

## Docs, changelog, and release notes

- Run API generation when adding public API symbols.
- Add a Towncrier fragment for user-facing changes instead of editing the changelog directly.
- Use a `.skip` fragment only when there is no user-facing impact and the project permits it.
- Preview release notes with the documented Towncrier draft command for the target version/date.

## Scripts and hooks

Useful repository commands include:

```bash
uvx pre-commit run -a
python scripts/check_warp_array_syntax.py
python docs/generate_api.py
```

The generated skill does not copy the repository docs generator because it is checkout-specific. Use the command above only when working inside a Newton checkout.

## Commit and PR rules

- Create a feature branch before committing; do not commit directly to `main`.
- Use imperative commit subjects around 50 characters and wrap bodies at 72 characters.
- If opening a PR, use the repository PR template and include required tests/changelog notes.
- Pin GitHub Actions by SHA when changing workflows.
- In SPDX copyright lines, use the year a file was first created; do not create date ranges merely because a file changed.
