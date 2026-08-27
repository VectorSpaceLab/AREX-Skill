# Lexicon reference

## What a lexicon guarantees

Earth2Studio's common vocabulary is a dictionary of standardized IDs to
physical meanings. Examples include `t2m` (2-m temperature in K), `u10m` and
`v10m` (10-m wind components), `msl` (mean sea-level pressure), `z500`
(geopotential at 500 hPa), and `tcwv` (total column water vapor). The common
vocabulary is descriptive; a source-specific lexicon decides whether an ID is
available and how to retrieve it.

A source lexicon is normally a class with `metaclass=LexiconType`, a `VOCAB`
dictionary, and a `get_item` implementation. The metaclass provides:

```python
if "t2m" in SourceLexicon:
    backend_key, modifier = SourceLexicon["t2m"]
```

The result is commonly `(backend_key, modifier)`. The backend key can be a
native field name, a compound selector, or a route containing separators such
as `::`. The callable modifier receives the source data and returns values in
the Earth2Studio representation. Some source lexicons return a longer tuple
when the source requires product or dataset routing; inspect that lexicon's
contract instead of unpacking every result as a pair.

A missing key is intentional: the vocabulary lists supported standardized
fields, not every field present in a remote data store. A request for an ID
outside `VOCAB` should fail early and explicitly.

## Level naming

- No suffix after a pressure number means a pressure-level variable, e.g.
  `t850`, `u500`, or `z250`.
- `m` denotes height above the surface, e.g. `t2m` or `u10m`.
- A source-specific/custom level may use a `k` suffix, e.g. `u100k`; the
  meaning is defined by that source/use-case and is not interoperable by name
  alone.

The same short ID can have a different native key in different lexicons. For
example, one GRIB-backed source can route `t2m` through a parameter and level
selector, while an ERA5-style Zarr source can route it through a dataset field.
The caller must keep the standardized ID and let the source perform the
translation.

## Mapping and modifier workflow

Use this sequence when adding or debugging a source variable:

1. Identify the source class and its lexicon class. Do not use a lexicon from a
   similar product merely because the variable names look familiar.
2. Check membership for every requested Earth2Studio ID.
3. Resolve each entry through the documented indexing operation. Record the
   native key/route, expected level, unit convention, and modifier.
4. Apply the modifier only through the source's intended path. Do not apply it
   a second time to already standardized values.
5. Confirm the output array/frame still labels the variable with the
   Earth2Studio ID and has the expected physical units.
6. If a required ID is absent, either select another source that advertises it
   or extend the source/lexicon with tests. Do not guess a native name.

Representative mappings in the package include GFS-style `PARAM::LEVEL`
selectors and ERA5/ARCO-style `dataset_field::level` selectors. Compound
routes can contain additional separators or identifiers, and observation or
satellite lexicons can return product-specific metadata. The mapping shape is
not universal; the source implementation owns parsing.

## Synthetic missing-variable check

This is a safe, offline contract check. It intentionally uses a missing ID and
should fail before any data access:

```python
requested = ["t2m", "made_up_field"]
missing = [name for name in requested if name not in SourceLexicon]
if missing:
    raise KeyError(
        f"Unsupported standardized variables for {SourceLexicon.__name__}: {missing}"
    )
```

For a concrete package lexicon, replace `SourceLexicon` with the selected
lexicon class. If membership passes but indexing fails, inspect the class's
`VOCAB` and `get_item` contract; if indexing passes but fetching fails, debug
the native route, date/level availability, optional parser, or remote product.

## Units and representation traps

Lexicon modifiers can make sources more comparable, but they do not make all
products physically identical. Examples of source-specific transformations
include converting geopotential height to geopotential, accumulated
precipitation units, Celsius to Kelvin, percentages to fractions, wind-vector
decomposition, or sensor-specific brightness-temperature/reflectance values.

Always inspect the standardized vocabulary description and the source lexicon's
modifier before combining sources. Do not assume:

- `tp` has the same accumulation period across products;
- a percentage is already a 0–1 fraction;
- `z500` and a native model-level geopotential field are the same variable;
- satellite channel IDs from different sensors are interchangeable;
- a tabular `observation` column has the same units for every source.

## Custom source pattern

A custom DataSource should accept standardized IDs at its public boundary and
translate them internally:

```python
class LocalSource:
    def __init__(self, array):
        self.array = array

    def __call__(self, time, variable):
        names = [variable] if isinstance(variable, str) else list(variable)
        unknown = [name for name in names if name not in self.array.variable]
        if unknown:
            raise KeyError(f"local data lacks variables: {unknown}")
        return self.array.sel(time=time, variable=names)
```

For a remote/custom source, the same check should be followed by lexicon
lookup and modifier application. Return an Xarray DataArray with `time` and
`variable` coordinates, and preserve the requested standardized variable
labels even if the backing array uses native names.

## Lexicon-focused hard case

Combine this missing-variable check with an observation source configured with
an asymmetric tolerance such as:

```python
from datetime import timedelta

window = (timedelta(hours=-1), timedelta(hours=6))
# A source that supports TimeTolerance receives `window` at construction.
```

The expected behavior is two independent gates: reject an unsupported
standardized variable before fetch, and, for a supported variable, accept only
rows in the inclusive interval `[request - 1h, request + 6h]`. Do not let the
presence of a nearby row compensate for a missing lexicon entry, and do not
silently change the asymmetric interval to `±6h`.
