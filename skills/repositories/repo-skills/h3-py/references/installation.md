# Installation and runtime facts

Read this reference when installing `h3`, selecting the optional NumPy API, or
checking whether a package/version mismatch explains an import failure.

## Public package contract

- Distribution: `h3`.
- Python requirement: `>=3.10`.
- Version inspected for this skill: `4.5.0`.
- Default runtime dependencies: none.
- Optional dependency: `numpy`, exposed by the `h3[numpy]` extra and required by
  `h3.api.numpy_int`.
- `h3.api.memview_int` uses typed memoryview-backed collections and does not
  require NumPy.
- The package wraps the H3 C library. `h3.versions()` returns a mapping such
  as `{'python': '4.5.0', 'c': '4.5.0'}`; major/minor versions should match.

## Recommended installs

```console
python -m pip install h3
python -m pip install 'h3[numpy]'
```

The second command is additive; use it when the consumer actually needs NumPy
arrays. A normal `import h3` uses the dependency-free string API.

For a Conda-based runtime, use the public conda-forge package name:

```console
conda install -c conda-forge h3-py
```

Do not install the similarly named `h3` package from an unrelated source unless
its distribution metadata and API are confirmed to be Uber's H3 binding.

## Minimal verification

```python
import h3

assert h3.is_valid_cell(h3.latlng_to_cell(37.769377, -122.388903, 9))
print(h3.versions())
```

Then run `python scripts/check_h3_environment.py --help` and
`python scripts/check_h3_environment.py check`. If NumPy is selected, add
`--include-numpy`.

## Source/build note

The published wheels hide the C/Cython build. A source installation may need a
C compiler, CMake, Cython, and the H3 core source made available by the build
configuration. Prefer a published wheel for ordinary Researcher work; do not
turn a missing compiler into an H3 API diagnosis. When inspecting a checkout,
verify that its H3 core submodule or equivalent source is present before
attempting an editable build.
