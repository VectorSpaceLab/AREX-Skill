# Formats and CLI Reference

## Choosing Formats

| Need | Preferred format/API | Notes |
| --- | --- | --- |
| Preserve units and metadata in a text file | `ascii.ecsv` with `QTable` | Best default for Astropy-native table round-trips |
| Standard astronomy image/table files | FITS | Use explicit HDU selection and verification policy |
| Virtual Observatory exchange | VOTable | Validate schema/metadata when sharing externally |
| Human-readable simple tables | `ascii.csv`, `ascii.fixed_width`, `ascii.basic` | May not preserve all metadata/units |
| Large binary table ecosystem | HDF5 or Parquet | Requires optional dependencies and format-specific paths |
| Interop with Pandas-like tools | pandas/dataframe bridges | Validate units, times, and mixins after conversion |

## Public CLI Safety

Run `--help` first for every command. Use temporary copies for experiments.

```bash
fitsinfo file.fits
fitsheader file.fits
fitsdiff old.fits new.fits
showtable-astropy table.ecsv --format ascii.ecsv --max-lines 20
volint table.xml
```

`fitscheck` can update files depending on flags. Treat it as diagnostic unless
the user explicitly asks to add/update checksums or fix verification state.

```bash
fitscheck --help
```

## Tiny Fixture Pattern

```python
from astropy import units as u
from astropy.io import fits
from astropy.table import QTable
import numpy as np

fits.PrimaryHDU(np.zeros((2, 2))).writeto("tiny.fits", overwrite=True)
QTable({"x": [1, 2] * u.m}).write("tiny.ecsv", format="ascii.ecsv", overwrite=True)
```

Use fixtures like this for CLI smoke checks, not user data.
