# BlenderGIS Georeferencing and CRS Workflows

Use these workflows when a BlenderGIS task needs a valid CRS, scene origin, or point transform before importing data or rendering georeferenced output.

## 1. Check scene georeferencing before a GIS workflow

In a Blender Python context where the add-on is enabled:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
print({
    "has_crs": gs.hasCRS,
    "has_valid_crs": gs.hasValidCRS,
    "has_origin_projected": gs.hasOriginPrj,
    "has_origin_geographic": gs.hasOriginGeo,
    "is_georef": gs.isGeoref,
    "is_fully_georef": gs.isFullyGeoref,
    "is_broken": gs.isBroken,
    "crs": gs.crs,
    "origin_projected": gs.getOriginPrj() if gs.hasOriginPrj else None,
    "origin_geographic": gs.getOriginGeo() if gs.hasOriginGeo else None,
    "scale": gs.scale,
    "zoom": gs.zoom,
})
```

Proceed with vector/raster/basemap workflows only when:

- `is_broken` is false, and
- `is_georef` is true for workflows that place projected data, or
- you have a deliberate plan to initialize the scene first.

If the task is only to inspect a CRS string or transform a point, use [../scripts/transform_point.py](../scripts/transform_point.py) instead of opening Blender.

## 2. Initialize a scene from known projected coordinates

Use this when the target CRS and projected origin are known, for example a local engineering or UTM coordinate.

1. Set the CRS first. In UI, use the Geoscene panel CRS control (`geoscene.set_crs`) and choose a predefined CRS, or add one in preferences with `bgis.add_predef_crs`.
2. Initialize the projected origin:
   - UI: Geoscene panel origin add button -> `geoscene.init_org`, leave `lonlat` false, enter `x` and `y` in the selected CRS.
   - Python:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
gs.crs = "EPSG:32631"      # example UTM zone 31N
gs.setOriginPrj(448251.8, 5411932.7, synch=True)
assert gs.isGeoref and not gs.isBroken
```

3. If `synch=True` succeeds, `longitude` and `latitude` are also written. If synchronization fails, the scene can still be valid with projected origin only (`isGeoref` true, `isFullyGeoref` false).
4. Use `geoscene.coords_viewer` in a View3D object-mode area to display CRS coordinates under the cursor.

## 3. Initialize a scene from known longitude/latitude

Use this when the real-world origin is known as WGS84 `(longitude, latitude)`.

1. Set a suitable scene CRS. Do not use `EPSG:4326` as a precision modelling CRS unless the task explicitly requires degree units. Prefer an appropriate projected CRS such as UTM for local work or Web Mercator for web tiles.
2. Initialize the origin as lon/lat:
   - UI: `geoscene.init_org`, enable `lonlat`, enter `x=longitude`, `y=latitude`.
   - Python:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
gs.crs = "EPSG:3857"
gs.setOriginGeo(2.0, 48.0)  # lon, lat
assert gs.hasOriginGeo
assert gs.hasOriginPrj
```

3. Validate that the projected origin looks plausible. For the example above, WGS84 `(2, 48)` in Web Mercator should be near `(222638.98, 6106854.83)`.

## 4. Recover a scene whose origin exists but CRS is unset

This is a difficult but common partial state: `crs x`/`crs y` or `longitude`/`latitude` exists, but `SRID` is missing, so `GeoScene.isBroken` is true.

Decision tree:

1. Inspect exact keys and decide which origin is trustworthy:

```python
from BlenderGIS.geoscene import SK
scn = bpy.context.scene
state = {key: scn.get(key) for key in [SK.CRS, SK.CRSX, SK.CRSY, SK.LON, SK.LAT, SK.SCALE, SK.ZOOM]}
print(state)
```

2. If `longitude` and `latitude` exist and are within valid ranges, choose the intended projected scene CRS, set it, then link projected origin:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
gs.crs = "EPSG:3857"       # choose from task evidence, data metadata, or user intent
gs.setOriginGeo(gs.lon, gs.lat)
# equivalent UI recovery after setting CRS: geoscene.link_org_prj
assert gs.isGeoref and not gs.isBroken
```

3. If only `crs x` and `crs y` exist, recover by setting the original CRS that those coordinates were in, then link geographic origin:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
x, y = gs.getOriginPrj()
gs.crs = "EPSG:32631"      # must match the existing projected coordinates
gs.setOriginPrj(x, y, synch=True)
# equivalent UI recovery after setting CRS: geoscene.link_org_geo
assert gs.isGeoref and not gs.isBroken
```

4. If the CRS cannot be inferred, do not guess silently. Preserve any known origin values outside the scene, run `geoscene.clear_georef`, and ask for the CRS or recover it from data metadata in the appropriate data sub-skill.

5. If `SRID` is invalid and origin coordinates are valuable, save the origin values, clear the broken CRS, set a valid CRS, then reapply/link the origin. See [troubleshooting.md](troubleshooting.md#invalid-crs) for invalid CRS handling.

## 5. Recover a scene whose CRS exists but projected origin is missing

This is broken when `SRID` and `longitude`/`latitude` exist but `crs x`/`crs y` do not.

1. Validate the CRS:

```python
from BlenderGIS.core.proj.srs import SRS
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
assert SRS.validate(gs.crs)
```

2. If geographic origin exists, link projected origin with UI operator `geoscene.link_org_prj` or Python:

```python
gs.crsx, gs.crsy = reprojPt(4326, gs.crs, gs.lon, gs.lat)
```

3. If only CRS exists and no origin exists, initialize origin with `geoscene.init_org` or `GeoScene.setOriginPrj`.

## 6. Switch an existing scene to a different CRS

1. Confirm the scene is not broken. CRS switch tries to update existing origin coordinates and can fail if the current CRS is invalid or a reprojection engine is unavailable.
2. Prefer a scene backup before switching CRS when objects are already placed.
3. In UI, use `geoscene.set_crs` after selecting/adding a predefined CRS in preferences.
4. In Python:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
if gs.isBroken:
    raise RuntimeError("Repair georef before switching CRS")
gs.crs = "EPSG:32631"
assert gs.isGeoref and not gs.isBroken
```

5. If switching fails, keep the old state, choose a different engine, install/enable the missing engine, or clear and rebuild georef from trusted coordinates.

## 7. Choose projection engine when pyproj exists but GDAL does not

The verified minimum environment has pyproj and no GDAL. That means `AUTO` selects `PYPROJ` for general local CRS transforms.

Recommended behavior:

1. Leave add-on preference `Projection engine` set to `Auto detect` unless debugging.
2. If transforms work in `AUTO`, record that `Reproj(...).iproj == "PYPROJ"` is expected when GDAL is absent.
3. If a user forces `GDAL`, switch back to `AUTO` or `PYPROJ` because `GDAL` raises `Missing reproj engine` when `osgeo` is unavailable.
4. If pyproj exists but a particular transform fails because of CRS syntax or library data, test a simpler CRS spelling (`EPSG:xxxx` instead of deprecated `+init=epsg:xxxx`) and validate with the bundled helper.
5. Use `BUILTIN` only for WGS84 <-> Web Mercator or WGS84 <-> UTM transforms. Do not force it for arbitrary CRS pairs.
6. Use `EPSGIO` / MapTiler Coordinates only when local engines cannot perform an EPSG-to-EPSG transform and network/API-key use is acceptable.

Programmatic check:

```python
from BlenderGIS.core import settings
from BlenderGIS.core.proj.reproj import Reproj

settings.proj_engine = "AUTO"
r = Reproj("EPSG:4326", "EPSG:3857")
print(r.iproj)  # expected: PYPROJ when pyproj is installed and GDAL is absent
```

## 8. Transform one point outside Blender

Use the bundled helper for deterministic preflight checks:

```bash
python sub-skills/georeferencing-and-crs/scripts/transform_point.py \
  --src-crs EPSG:4326 \
  --dst-crs EPSG:3857 \
  --x 2 \
  --y 48 \
  --json
```

Expected shape:

```json
{
  "ok": true,
  "src_crs": "EPSG:4326",
  "dst_crs": "EPSG:3857",
  "input": {"x": 2.0, "y": 48.0},
  "output": {"x": 222638.98158654713, "y": 6106854.834885074},
  "engine": "pyproj"
}
```

The exact `engine` may be `pyproj`, `builtin`, or `identity` depending on installed dependencies and CRS pair. The helper does not use network fallback by default.

## 9. Add or edit predefined CRS entries

Use add-on preferences when the CRS should appear in the Geoscene panel selector.

- Open preferences: `bgis.pref_show` or Blender Add-ons preferences for BlenderGIS.
- Add a CRS: `bgis.add_predef_crs` with fields:
  - `crs`: EPSG code, `AUTH:CODE`, or Proj4 string.
  - `name`: display label.
  - `desc`: tooltip/comment.
  - optional `search`: MapTiler search; requires `maptiler_api_key` in preferences.
- Edit/remove/reset entries: `bgis.edit_predef_crs`, `bgis.rmv_predef_crs`, `bgis.reset_predef_crs`.

Use `SRS.validate(crs)` before storing custom entries. A CRS preset can be syntactically valid but still unsuitable for precision modelling if units are degrees or the projection is heavily distorted.

## 10. Validate georef before routing to data sub-skills

Before importing data:

- Shapefile/OSM workflows: ensure CRS/origin are valid here, then route geometry import details to `vector-data-and-osm`.
- Raster/world-file workflows: ensure CRS/origin are valid here only for scene placement, then route file metadata and raster import mode details to `raster-dem-and-basemaps`.
- Camera georender workflows: ensure CRS/origin are valid here, then route camera/world-file output details to `geocameras-and-rendering`.

Minimal gate:

```python
from BlenderGIS.geoscene import GeoScene

gs = GeoScene(bpy.context.scene)
if gs.isBroken:
    raise RuntimeError("Scene georef is broken; repair it before importing geodata")
if not gs.isGeoref:
    raise RuntimeError("Set scene CRS and projected origin before this workflow")
```
