# Data Workflows Troubleshooting

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `No module named planetary_computer` | The Planetary Computer helper dependency is missing | Install `planetary-computer` plus the small raster stack used by `leafmap.download` and rerun the data smoke. |
| `No module named rioxarray` or `xarray` | Raster download or viewer dependencies are missing | Install the missing package and retry the import or smoke check. |
| Empty STAC/OSM/fire/Terrascope result | Wrong bbox, tag filter, or endpoint | Check the query parameters and try a metadata-only query first. |
| CRS or coordinate-order mismatch | Lat/lon fields or bbox order are wrong | Verify whether the helper wants longitude/latitude or north/south/east/west ordering. |
| `ImportError` for `osmnx`, `geopandas`, `fiona`, or `rasterio` | Optional file-driver or geospatial stack is incomplete | Install the missing dependency and rerun the local conversion smoke. |

## Recovery checklist

1. Run `python scripts/check_leafmap_smoke.py --mode data`.
2. Confirm the file schema or service arguments.
3. Retry with a tiny local fixture before using a remote source.
4. If the task needs network or credentials, state that explicitly instead of pretending the failure is a code bug.

## When to stop

Stop and hand the task back to the user or a different backend when:
- a live service is unavailable,
- credentials are missing,
- a large download would be slow or expensive,
- or the user really needs a rendered map rather than a data helper.
