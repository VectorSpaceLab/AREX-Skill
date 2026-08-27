# CRS troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `CRSError` or an empty CRS | Invalid authority/string, malformed mapping, or missing CRS metadata | Validate with `CRS.from_user_input`/`CRS.from_string`, inspect `to_wkt()` and `to_epsg()`, and stop rather than guessing a CRS. |
| Transform raises a PROJ/GDAL error | PROJ data is unavailable, source/destination definitions are incompatible, or coordinates are malformed | Use `environment-cloud` runtime checks, verify `PROJ_DATA`/GDAL data, confirm equal `xs`/`ys` lengths, and test one known point. |
| Result is numerically plausible but spatially wrong | CRS label or axis/order assumption is wrong | Record units and axis convention, compare against a known coordinate, and inspect source collection CRS before transforming. |
| Geometry type changes unexpectedly | Antimeridian cutting split the geometry | Disable cutting unless required, or handle the documented Polygon-to-MultiPolygon possibility. |
| Precision warning appears | Deprecated `precision` parameter was used | Remove it for new code and round the returned coordinates explicitly. |
| Output coordinates changed but map still appears misplaced | Destination dataset metadata was left at the source CRS | Set the output CRS to the same destination CRS used by `transform_geom`; re-open and inspect `dst.crs`. |
