# WCS and NDData API Reference

## WCS Constructors and Methods

- `WCS(header=None, fobj=None, key=' ', minerr=0.0, relax=True, naxis=None, keysel=None, colsel=None, fix=True, translate_units='', _do_set=True, preserve_units=False)` constructs FITS WCS objects or empty WCS objects with `naxis=`.
- High-level methods: `pixel_to_world`, `world_to_pixel`, `array_index_to_world`, `world_to_array_index`.
- Low-level/legacy methods: `all_pix2world`, `all_world2pix`, `wcs_pix2world`, `wcs_world2pix`.
- Inspectors: `pixel_n_dim`, `world_n_dim`, `pixel_shape`, `array_shape`, `world_axis_physical_types`, `world_axis_units`, `axis_type_names`, `celestial`, `to_header()`.

## Pixel Conventions

- High-level `pixel_to_world`/`world_to_pixel` use zero-based pixel coordinates and Astropy world objects.
- `array_index_*` methods use NumPy array order `(row, column, ...)`.
- `all_pix2world`/`all_world2pix` require explicit `origin=0` for NumPy/Python pixel coordinates or `origin=1` for FITS/DS9 style.
- `all_*` methods include distortion corrections; core `wcs_*` methods do not include all distortion stages.

## NDData and CCDData

- `NDData(data, uncertainty=None, mask=None, wcs=None, meta=None, unit=None, copy=False, psf=None)` stores array-like data with metadata.
- Use `StdDevUncertainty`, `VarianceUncertainty`, or `InverseVariance` for uncertainty propagation semantics.
- `CCDData` is the FITS-oriented image data class; it requires a unit and maps FITS `BUNIT` to units.
- Boolean masks follow NumPy masked-array convention: `True` means invalid/ignored.

## CLI/API Mapping

- `wcslint file.fits` validates WCS-related FITS header issues.
- Use `fits.open` from the tables/I/O route to obtain headers or HDUs.
- Use WCS numeric round-trips as validation even when `wcslint` passes.
