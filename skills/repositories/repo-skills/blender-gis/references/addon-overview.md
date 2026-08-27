# BlenderGIS Add-on Overview

## Purpose

Read this for shared BlenderGIS facts: version, feature flags, menu routes, operator IDs, preferences, optional dependencies, and what each sub-skill owns.

## Public Identity

- Add-on name: `BlenderGIS`
- Add-on version: `2.2.14`
- Blender minimum: `2.83`
- Category: `3D View`
- Main UI route: `View3D > GIS`
- Public purpose: handle geodata in Blender, including GIS file import, OSM/web geodata, rasters/DEMs, terrain generation, scene georeferencing, and georeferenced cameras.

The add-on guards startup: it raises when Blender is older than the declared minimum or when Blender major version is greater than 5.

## Menu and Operator Map

| GIS menu area | Main operator IDs | Owning sub-skill |
| --- | --- | --- |
| `GIS > Web geodata` | `view3d.map_start`, `importgis.osm_query`, `importgis.dem_query` | `raster-dem-and-basemaps`, `vector-data-and-osm` |
| `GIS > Import` | `importgis.shapefile_file_dialog`, `importgis.georaster`, `importgis.osm_file`, `importgis.asc_file` | `vector-data-and-osm`, `raster-dem-and-basemaps` |
| `GIS > Export` | `exportgis.shapefile` | `vector-data-and-osm` |
| `GIS > Camera` | `camera.georender`, `camera.geophotos`, `camera.geophotos_setactive` | `geocameras-and-rendering` |
| `GIS > Mesh` | `tesselation.delaunay`, `tesselation.voronoi`, `earth.sphere`, `earth.curvature` | `terrain-mesh-and-analysis` |
| `GIS > Object` | `object.drop` | `terrain-mesh-and-analysis` |
| `GIS > Nodes` | `analysis.nodes` plus `reclass.*` node-editor operators | `terrain-mesh-and-analysis` |
| `GIS > Logs` | `bgis.logs` | root troubleshooting |

## Feature Flags

The source registers these features when their booleans are true: camera from EXIF, georeferenced render camera, shapefile export, web DEM, georaster import, OSM import/query, shapefile import, ASCII grid import, Delaunay/Voronoi, terrain nodes, terrain reclassify, basemaps, drop-to-ground, and earth sphere/curvature.

## Preferences and Configuration

BlenderGIS stores editable values in add-on preferences and mirrors some choices into `core.settings` at registration.

Important preferences:

- predefined CRS list, defaulting to `EPSG:3857` Web Mercator and `EPSG:4326` WGS84 latitude/longitude;
- projection engine: `AUTO`, `GDAL`, `PYPROJ`, `EPSGIO`, or `BUILTIN` depending on installed dependencies;
- image engine: `AUTO`, `GDAL`, `IMGIO`, or `PIL` depending on installed dependencies;
- basemap cache folder, defaulting to a user data directory created by the add-on;
- OSM tag filters, defaulting to `building`, `highway`, `landuse`, `leisure`, `natural`, `railway`, and `waterway`;
- Overpass server list;
- DEM server list, including OpenTopography SRTM templates that require an API key.

## Optional Dependencies

| Dependency/service | Used for | Behavior when missing |
| --- | --- | --- |
| Blender Python modules (`bpy`, `bmesh`, `mathutils`, `gpu`) | Add-on registration and operator execution | The add-on cannot run outside a Blender-compatible Python runtime. |
| `pyproj` | local CRS transformations | `AUTO` can fall back to GDAL, built-in WGS84/WebMercator/UTM math, or EPSG.io/MapTiler remote transforms depending on CRS pair. |
| GDAL Python bindings (`osgeo`) | raster/projection engine and WKT export | GDAL-specific raster/projection paths are unavailable; use pyproj/PIL/ImageIO or document the missing optional dependency. |
| Pillow/PIL | image loading for raster workflows | Image engine list omits `PIL`; raster helpers and imports may need GDAL/ImageIO instead. |
| ImageIO FreeImage | image IO fallback for more formats | The add-on attempts to obtain FreeImage; failures mark `HAS_IMGIO` false. |
| Network and services | basemap tiles, Nominatim search, Overpass, EPSG.io/MapTiler, OpenTopography DEM | Do not assume availability; handle timeouts, rate limits, API keys, and privacy. |

## Skill Routing Notes

- Use `georeferencing-and-crs` before any workflow that depends on scene CRS/origin.
- Use `vector-data-and-osm` for shapefile and OSM vector objects.
- Use `raster-dem-and-basemaps` for image/DEM/tile data.
- Use `terrain-mesh-and-analysis` after data is imported and needs geometric terrain processing or analysis materials.
- Use `geocameras-and-rendering` when cameras, photo EXIF, render extents, or world files are the main output.
