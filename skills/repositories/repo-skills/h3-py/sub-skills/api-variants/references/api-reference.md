# API variant reference

## Representation and dependency matrix

The public function names and signatures are shared across the four variants.
The differences below are the important runtime contract. Collection-returning
functions include operations such as `grid_ring`, `cell_to_children`, and
`compact_cells`; a few specialized functions intentionally return ordinary
Python values regardless of variant.

| Import | H3 scalar input/output | Collection output | Collection input accepted by the conversion layer | Dependency and use |
|---|---|---|---|---|
| `h3` or `h3.api.basic_str` | hexadecimal Python `str`, e.g. `'8928308280fffff'` | Python `list[str]` in the current package; use a set or sorted list yourself when order is not meaningful | General Python iterables of strings, including lists, tuples, and sets | Base install; best boundary and readability choice |
| `h3.api.basic_int` | Python `int` representing an unsigned 64-bit H3 value | Python `list[int]` | General Python iterables of integers, including lists, tuples, sets, and iterators | Base install; ordinary Python integer pipeline |
| `h3.api.memview_int` | Python `int` | Typed H3 `uint64` buffer exposed as a Cython memoryview slice; `list(view)` is a copy into a Python list | A buffer with matching unsigned 64-bit item type, such as `array('Q')`, `memoryview(array('Q'))`, or a NumPy `uint64` array | Base install; typed buffers without a NumPy dependency |
| `h3.api.numpy_int` | Python `int` for scalar-returning functions; NumPy scalar values can be accepted as integer inputs | NumPy `ndarray`, normally `dtype('uint64')` | Arrays, lists, and tuples convertible by `numpy.asarray(..., dtype='uint64')`; sets and arbitrary iterators are not a reliable input contract | Requires optional NumPy; best when the next consumer already uses arrays |

The string documentation describes the default as using standard Python
collections; in the current implementation, collection-returning functions
normally materialize a list. Do not infer set semantics from an output type:
choose list/set/sorted normalization according to whether order or duplicates
matter to your task.

All H3 index representations are views of the same unsigned 64-bit index value.
The representation does not change the cell, resolution, or geographic meaning.
It does change accepted collection buffers, output types, conversion cost, and
how easily a downstream library can consume the result.

## Default import equivalence

```python
import h3
import h3.api.basic_str as h3_strings

assert h3.latlng_to_cell(0.0, 0.0, 0) == h3_strings.latlng_to_cell(0.0, 0.0, 0)
```

`import h3` re-exports the basic string API. Import a named variant when the
representation is part of the function's contract; do not rely on changing a
process-wide alias later.

## Conversion signatures

The explicit conversion functions are available from every public variant:

```python
h_int = h3.api.basic_int.str_to_int(h: str) -> int
h_hex = h3.api.basic_int.int_to_str(x: int) -> str
```

The same signatures are used through `h3`, `basic_str`, `memview_int`, and
`numpy_int`:

- `str_to_int(h)` parses a hexadecimal string and returns a Python `int`.
- `int_to_str(x)` formats an unsigned H3 integer as lowercase hexadecimal with
  no `0x` prefix.
- These functions convert representation; they do not by themselves establish
  that the value is a valid cell, edge, vertex, or other H3 index. Use the
  relevant `is_valid_*` function before an operation when validation matters.

Prefer the API module's own conversion function at a boundary, or use a single
canonical conversion module consistently:

```python
from h3.api import basic_int, basic_str

h = basic_int.str_to_int('8928308280fffff')
assert basic_str.int_to_str(h) == '8928308280fffff'
```

`int_to_str` requires an integer in the unsigned 64-bit range. Negative values,
values above `2**64 - 1`, and non-integers fail rather than producing a valid
H3 string. A syntactically valid hexadecimal string can still encode an invalid
H3 index; validation is a separate step.

## Output and ownership details

- Basic string and basic integer collection results are ordinary Python lists;
  their elements are Python `str` or `int`, respectively.
- A NumPy collection result has `uint64` dtype. `np.asarray` may preserve this
  dtype without copying when the input already has a compatible buffer; an
  explicit `dtype='uint64'` makes the intended representation clear.
- A memoryview result owns or retains the allocated buffer through its view. It
  is readable and can be writable; mutations change the view's storage. Keep a
  live reference to the view while consumers use it and copy it when an
  independent snapshot is required.
- `np.asarray(mv)` is a view for the compatible H3 buffer in the documented
  memoryview-to-NumPy path. `np.array(mv)` creates an independent array copy.
  `np.asarray(mv).copy()` is an explicit independent copy.
- Converting a view with `list(mv)` copies values into Python integers. Converting
  integers to a Python list or set similarly gives up buffer sharing.

## API parity boundaries

Shared functions should agree after scalar/collection normalization. A useful
parity comparison is to convert every returned H3 value to its lowercase hex
string, then compare lists or sets according to the task. `get_icosahedron_faces`
is a special public function whose result is an ordinary list of face integers
across APIs. Shape objects and polygon workflows are outside this route; use the
polygon route instead.
