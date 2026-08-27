# API variant workflows

## Select a variant deliberately

Use this decision tree before importing a module:

```text
Are H3 values crossing a human/config/JSON boundary?
  yes -> h3 (basic_str); convert only at compute boundaries
  no  -> Are collection consumers NumPy code or typed arrays?
           yes -> numpy_int, after installing the NumPy extra
           no  -> Must the pipeline remain dependency-free but exchange buffers?
                    yes -> memview_int, with uint64 buffers
                    no  -> basic_int for ordinary Python integer collections
```

Choose based on the representation contract, not an assumed universal speed
ranking. If computation is large enough for performance to matter, measure the
same operation, input size, output handling, and conversion cost on the target
workload. The published comparison numbers are illustrative evidence from one
example, not a promise for every machine or operation.

## Normalize scalars at boundaries

Keep one canonical internal representation per pipeline stage. This example
starts at the default string boundary, computes with integers, and serializes
back to strings:

```python
import h3
from h3.api import basic_int

seed_hex = h3.latlng_to_cell(37.7752702151959, -122.418307270836, 9)
seed_int = basic_int.str_to_int(seed_hex)
# Use the core-indexing route for the meaning of the grid operation itself.
ring_ints = basic_int.grid_ring(seed_int, 1)
ring_hex = [basic_int.int_to_str(int(h)) for h in ring_ints]
```

`int()` is intentional in normalization code: NumPy `uint64` values and typed
buffer elements then use the same scalar conversion path as Python integers.
Keep order only when it is part of the task. For unordered semantics, compare
`set(ring_hex)`; for stable output, use a deliberately chosen ordering rather
than relying on incidental API order.

## Compare API parity

All four APIs should produce the same H3 values after conversion. Use a fixed
seed and normalize outputs before comparing:

```python
import h3
from h3.api import basic_int, memview_int

seed_hex = h3.latlng_to_cell(0.0, 0.0, 0)
seed_int = basic_int.str_to_int(seed_hex)

def as_hex(api, values):
    return [value if isinstance(value, str) else api.int_to_str(int(value))
            for value in values]

str_values = h3.grid_ring(seed_hex, 1)
int_values = basic_int.grid_ring(seed_int, 1)
mv_values = memview_int.grid_ring(seed_int, 1)

assert set(str_values) == set(as_hex(basic_int, int_values))
assert set(str_values) == set(as_hex(memview_int, mv_values))
```

For NumPy, use the same `as_hex` helper over the returned array. Compare
meaning after normalization, and compare dtype separately when dtype is part of
the downstream contract.

## Cross-API collection conversion

Convert explicitly instead of passing a collection from one variant to another:

```python
import numpy as np
from h3.api import basic_int, basic_str, numpy_int

hexes = ['8928308280fffff', '89283082807ffff']
ints = [basic_int.str_to_int(h) for h in hexes]
uints = np.asarray(ints, dtype=np.uint64)

# Each call receives the representation it documents.
ordinary = basic_int.compact_cells(ints)
array_result = numpy_int.compact_cells(uints)
back_to_hex = [basic_str.int_to_str(int(h)) for h in array_result]
```

`basic_int` accepts general iterables because its wrapper materializes them into
a list. `numpy_int` uses `numpy.asarray`, so lists and tuples are convenient,
but a set or one-shot iterator is not a reliable input. If a set is the source,
choose an order first:

```python
uints = np.asarray(sorted(source_set), dtype=np.uint64)
```

This preserves a deliberate order while making the unsigned dtype explicit.

## Safe NumPy and memoryview exchange

NumPy is optional for the package. The dependency-free buffer route uses a
standard library unsigned-long-long array (the platform's `array('Q')` buffer
must expose the expected unsigned 64-bit format):

```python
from array import array
from h3.api import memview_int

seed = memview_int.str_to_int('8928308280fffff')
input_buffer = array('Q', [seed])
input_view = memoryview(input_buffer)
result_view = memview_int.cell_to_children(input_view)
try:
    values = list(result_view)       # independent Python-int snapshot
finally:
    result_view.release()             # release when the view is no longer used
```

For a result created by `memview_int`, use NumPy only when it is installed:

```python
import numpy as np
from h3.api import memview_int

result_view = memview_int.grid_ring(seed, 1)
array_view = np.asarray(result_view)       # compatible uint64 view; may share data
array_copy = np.array(result_view)         # independent copy
owned_view = np.asarray(result_view).copy()  # explicit independent copy
```

Do not mutate `result_view` while another consumer expects the original values.
If shared mutation is intended, retain both objects and document ownership. If
an independent snapshot is needed, use `np.array(...)` or `.copy()` and then
allow the original view to be released. A NumPy array made with `asarray` keeps
a buffer reference, but keeping the source view variable makes lifetime and
mutation intent obvious.

## Optional NumPy setup

The base package has no NumPy runtime dependency. Install the optional extra in
the environment that will execute the array route:

```console
python -m pip install "h3[numpy]"
```

Alternatively install a compatible NumPy release separately. Probe with
`import numpy as np` before selecting `numpy_int`; do not silently fall back to
an array contract if the caller requires `ndarray` output. Use `basic_int` or
`memview_int` when adding NumPy is not acceptable.
