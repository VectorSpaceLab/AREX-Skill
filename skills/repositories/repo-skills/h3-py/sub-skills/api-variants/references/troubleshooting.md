# API variant troubleshooting

## NumPy is missing

The base install deliberately has no runtime dependency on NumPy. Importing
`h3.api.numpy_int` may not fail immediately, because NumPy is imported when a
collection conversion is needed. Probe the dependency explicitly:

```python
try:
    import numpy as np
except ImportError:
    np = None

if np is None:
    # Select basic_int or memview_int, or install the optional extra.
    raise RuntimeError('numpy_int requires NumPy; install "h3[numpy]"')
```

Install the optional capability with `python -m pip install "h3[numpy]"` (or
install NumPy separately), then retry the array operation in the same
environment. The diagnostic `scripts/check_api_variants.py` reports a skipped
NumPy route with an actionable message instead of treating optional absence as
a failure of the base APIs.

## Wrong scalar or index representation

A string API expects hexadecimal string scalars; integer APIs expect an integer
H3 value. Convert at the boundary:

```python
from h3.api import basic_int, basic_str

h_int = basic_int.str_to_int('8928308280fffff')
h_hex = basic_str.int_to_str(h_int)
```

A NumPy `uint64` scalar can usually be passed to an integer API, but `int(x)` is
a portable normalization step when calling conversion functions. Do not pass a
string directly to an integer-only operation or a Python integer directly to a
string-only operation and then diagnose the resulting Cython type error as an
invalid cell. First normalize the representation, then use `is_valid_cell` (or
the relevant `is_valid_*` function) to test the H3 kind.

A numerically valid hexadecimal string is not necessarily a valid H3 index.
`str_to_int` only performs numeric conversion; H3 validity is checked by later
index operations or an explicit validator.

## Collection input constraints

Use the matrix in [the API reference](api-reference.md) when an input fails:

- `basic_str` and `basic_int` materialize ordinary iterables, so lists, tuples,
  sets, and iterators are suitable when their element types are correct.
- `numpy_int` uses `np.asarray(x, dtype='uint64')`. Lists, tuples, and compatible
  arrays work; sets and arbitrary iterators can fail. Convert a set to a sorted
  list (or another deliberate order) before `np.asarray`.
- `memview_int` requires a bytes-like buffer with the exact unsigned 64-bit item
  type. A Python list, tuple, set, or iterator is not a memoryview input. Use
  `array('Q')`, `memoryview(array('Q'))`, or a NumPy array with `dtype='uint64'`.

For `memview_int`, a signed NumPy array such as `dtype='int64'` has the wrong
buffer format even if all values are positive. Rebuild it explicitly:

```python
uints = np.asarray(signed_values, dtype=np.uint64)
result = memview_int.compact_cells(uints)
```

Do not use this conversion to hide negative or out-of-range values; validate
those values before casting.

## Memoryview lifetime, mutation, and copies

A `memview_int` collection result is a typed, allocated view. It can be indexed,
iterated, converted with `list`, or passed to compatible buffer consumers. It
may be writable, so an assignment such as `view[0] = 0` changes the view's
storage; that does not make the resulting value a valid H3 cell.

When NumPy is available:

```python
arr_shared = np.asarray(view)  # compatible uint64 view; can share storage
arr_copy = np.array(view)      # independent copy
arr_owned = np.asarray(view).copy()
```

Use `np.asarray` for zero-copy interop only when shared lifetime and mutation are
wanted. Use `np.array` or `.copy()` for an independent snapshot. Keep the view
alive while an API consumer is using it, release it only after consumers finish,
and never assume that a Python list or set shares storage.

## Conversion errors: invalid hex and overflow

`str_to_int(h)` accepts a hexadecimal numeric string and returns a Python
integer. Empty strings and non-hex text raise a `ValueError`. A `0x` prefix may
be accepted by the underlying hexadecimal parser, but use the canonical
lowercase, prefix-free form returned by `int_to_str` for portable interchange.
Whitespace or unusual formatting should be normalized by the caller rather than
used as an implicit protocol.

`int_to_str(x)` formats an unsigned 64-bit value. Negative values, values at or
above `2**64`, and non-integer objects raise a type/range error (commonly
`OverflowError` or `TypeError`). Check before converting when values originate
from user input:

```python
def as_h3_uint64(x):
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError('H3 index must be an integer')
    if not 0 <= x < 2**64:
        raise OverflowError('H3 index is outside uint64 range')
    return x
```

The range check does not replace `is_valid_cell`, because many in-range values
are not valid H3 indices.

## Parity and debugging

When variants appear to disagree:

1. Confirm the same package version with `versions()` in each import.
2. Confirm the same scalar index after `str_to_int`/`int_to_str` round-trip.
3. Run the same tiny operation with the same logical input.
4. Normalize every collection element to lowercase hex and compare sets when
   ordering is not part of the contract; compare lists when order is required.
5. Check collection input dtype and ownership separately from H3 values.
6. Use `inspect.signature(api.function)` to confirm that the public call shape is
   the expected one; do not import or depend on internal Cython functions.
7. Run `python scripts/check_api_variants.py` and save its output with the task's
   normal diagnostics, not inside the runtime skill tree.

If only ordering differs, do not call it a semantic mismatch until the task's
ordering contract is known. If normalized values differ, reduce to a fixed
scalar operation and route geospatial or index-algorithm questions to
[core-indexing](../../core-indexing/SKILL.md). For polygon or shape-specific
mismatches, use [polygon-geospatial](../../polygon-geospatial/SKILL.md).
