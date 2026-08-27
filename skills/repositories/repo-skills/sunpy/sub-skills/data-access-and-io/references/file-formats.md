# Local file formats and integration

Start with a non-destructive byte/header check. A suffix is a hint, not proof:
SunPy's detection reads magic bytes first and only then falls back to known
extensions. Preserve the original file and write round trips to a temporary or
new path.

## Format decision table

| Format | Public entry point | Returned/consumed object | Use it for | Important limits |
|---|---|---|---|---|
| FITS (`.fits`, `.fit`, `.fts`, gzip variants) | `astropy.io.fits`; `sunpy.map.Map` | HDU/header objects; Map for usable 2-D HDU | Interoperable solar images/tables and Map input | Header validity, HDU selection, WCS metadata, and multidimensional shape matter. |
| GENX | `sunpy.io.special.genx.read_genx(path)` | nested `OrderedDict` including a `HEADER` record | SolarSoft calibration/configuration structures | Reader is read-only; XDR/IDL conventions and UTF-8 strings are assumed. |
| ANA (`.fz`, `.f0`) | `sunpy.io.ana.read`, `.get_header`, `.write`; common `sunpy.io` dispatch | `(data, FileHeader)` pair or header | Legacy compressed solar image data | Deprecated in SunPy 6.0, needs the native C extension, and is not supported on Windows. |
| SRS | `sunpy.io.special.srs.read_srs(path)` | Astropy `QTable` with parsed columns, units, and `.meta` | NOAA/SWPC Solar Region Summary text | Input layout must be a recognized SRS report; it is a table, not a Map. |
| ASDF | `Map.save(path)`, `Map(path)` with `sunpy[asdf]` | serialized Map/coordinate objects; Map loads as `GenericMap` | Portable SunPy/Astropy object archives | Optional dependency; custom subclass recovery depends on registration. |
| JPEG2000 (`.jp2`, `.j2k`, `.jpc`, `.jpt`) | common `sunpy.io`/`Map` reader with `sunpy[jpeg2000]` | image data/header pair or Map | Instrument products distributed as JP2 | `glymur` and a usable codec are platform-dependent; write support is optional. |
| CDF/NetCDF/HDF5 | format-specific TimeSeries readers | TimeSeries-compatible data | Time-series files from CDAWeb/mission products | Route construction/analysis to the TimeSeries skill and install its optional readers. |

The public `sunpy.io` surface intentionally has a narrower role than the full
SunPy file ecosystem. GENX and SRS are public special readers, while ASDF is
detected by Map's ASDF integration rather than treated as a normal `(data,
header)` reader. The lower-level unified dispatch used internally by Map is not
a stable `sunpy.io.read_file` facade.

## FITS: read, inspect, write

```python
from pathlib import Path
import numpy as np
from astropy.io import fits

path = Path("input.fits")
with fits.open(path, memmap=False) as hdul:
    for hdu in hdul:
        print(np.shape(hdu.data) if hdu.data is not None else None)
        print(list(hdu.header)[:8])
    data = np.asarray(hdul[0].data)
    header = hdul[0].header.copy()
fits.PrimaryHDU(data=data, header=header).writeto("copy.fits", overwrite=False)
```

Use `hdul[index]` when a multi-HDU file needs a specific HDU, and use
`memmap=True` only when the file lifetime and storage semantics are understood.
For a Map, prefer `sunpy.map.Map(path)` so Map validation and source-specific
dispatch are applied. A FITS file with only 1-D or empty HDUs can be a valid
FITS file but is not a valid Map input.

A local Map round trip is:

```python
from sunpy.map import Map
m = Map("image.fits")
m.save("image-copy.fits")
reloaded = Map("image-copy.fits")
assert reloaded.data.shape == m.data.shape
```

The metadata required for a coordinate-aware Map is more than just `NAXIS`;
WCS/frame routing belongs to the maps and coordinates skills. If the purpose is
only extracting array/header content, stay with `sunpy.io` and avoid adding
WCS assumptions.

## GENX, ANA, and SRS

GENX is a SolarSoft XDR calibration/configuration container. It returns nested
Python structures rather than a Map. Check `result["HEADER"]` and the expected
keys before consuming calibration values; a short file, unsupported version,
or IDL save-file signature should be treated as a format mismatch.

ANA uses the legacy C extension:

```python
from sunpy.io import ana
pairs = ana.read("input.fz")
ana.write("copy.fz", pairs[0][0], comments=pairs[0][1])
```

This path is intentionally not used by the safe bundled helper because it is
deprecated, native-extension dependent, and platform-limited. If import raises
the ANA reader error, install the supported build or convert the source in a
controlled external tool; do not silently reinterpret an ANA file as FITS.

SRS parsing is table-oriented:

```python
from sunpy.io.special.srs import read_srs
srs = read_srs("19960106SRS.txt")
print(srs.colnames, srs.meta["issued"])
print(srs["Carrington Longitude"].unit)
```

The parser normalizes section names, extracts latitude/longitude columns,
assigns solar-region units, and stores report metadata. Validate that expected
columns exist; SRS content is not appropriate for `Map`.

## ASDF and optional round trips

ASDF is useful when preservation of SunPy/Astropy object metadata and masks is
more important than maximum interoperability with older FITS-only tools:

```python
import sunpy.map
m = sunpy.map.Map("input.fits")
m.save("map.asdf")
loaded = sunpy.map.Map("map.asdf")
assert loaded.data.shape == m.data.shape
```

Guard the import in applications:

```python
try:
    import asdf  # noqa: F401
except ImportError as exc:
    raise RuntimeError("Install sunpy[asdf] for ASDF support") from exc
```

SunPy currently serializes Maps as `GenericMap`; this is expected and does not
mean data were lost. If a custom map subclass is loaded as GenericMap, inspect
registration and metadata rather than force-casting it.

## File-layout validation

After every remote or converted file, validate in this order:

1. `Path.is_file()` and expected size/nonzero bytes.
2. The magic bytes and suffix agree with the intended format; if they do not,
   inspect the bytes and use an explicit special reader only when the content
   is known. Renaming is not conversion.
3. `astropy.io.fits.open` or the relevant special reader succeeds and returns
   the expected count.
4. Data shape/dtype and key metadata match the experiment contract.
5. Map or TimeSeries construction succeeds when that object is required.
6. For a round trip, compare shape, metadata keys, units, and representative
   values; do not compare only the filename or suffix.

[validate_local_data.py](../scripts/validate_local_data.py) automates a small,
local subset of these checks and can create its own FITS fixture. It does not
repair a malformed file or contact a URL.
