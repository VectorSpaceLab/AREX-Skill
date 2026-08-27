---
name: vector-data-and-osm
description: "Routes BlenderGIS vector data and OpenStreetMap shapefile
  import/export, Overpass query preflight, elevation/extrusion fields, and OSM
  tag workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Vector Data and OSM

Use this sub-skill when a task involves BlenderGIS vector geodata or OpenStreetMap data:

- importing ESRI Shapefile `.shp` data into a Blender scene;
- exporting selected mesh objects or collections back to Shapefile;
- importing local `.osm` XML files;
- querying Overpass for the current BlenderGIS extent;
- choosing DBF fields for elevation, extrusion, or object names;
- configuring OSM tags, Overpass servers, building extrusion, and object separation.

Do **not** use this sub-skill for raster/DEM/image basemaps, terrain mesh post-processing, or camera/render outputs. Route those to the sibling sub-skills for raster/basemaps, terrain analysis, or geocameras. If the scene CRS/origin is missing or broken, route first to `../georeferencing-and-crs/`.

## Read First

1. For end-to-end vector and OSM procedures, read `references/workflows.md`.
2. For exact operator IDs, properties, defaults, and inputs/outputs, read `references/operator-reference.md`.
3. For failures such as broken georeferencing, invalid fields, empty exports, and Overpass timeouts, read `references/troubleshooting.md`.
4. For a no-network Overpass preflight query, run or inspect `scripts/build_overpass_query.py`.

## High-Level Routes

- **Shapefile import:** use `importgis.shapefile_file_dialog` from `View3D > GIS > Import > Shapefile (.shp)` for interactive import, or `importgis.shapefile` for scripted execution after choosing CRS/elevation/extrusion fields.
- **Shapefile export:** use `exportgis.shapefile` from `View3D > GIS > Export > Shapefile (.shp)`; export only mesh objects from the current selection or a collection.
- **Local OSM XML:** use `importgis.osm_file` from `View3D > GIS > Import > Open Street Map xml (.osm)`; it parses local OSM XML and builds nodes, ways, areas, relations, and optionally extruded buildings.
- **Overpass query:** use `importgis.osm_query` from `View3D > GIS > Web geodata > Get OSM`; it requires a valid georeferenced scene and an extent from top orthographic view or one selected reference mesh.
- **OSM preflight without network:** use `scripts/build_overpass_query.py` to construct the exact Overpass QL shape before opening BlenderGIS or contacting a public Overpass server.

## Boundary Reminders

- Scene CRS, origin custom properties, reprojection engine selection, and broken-georef recovery are owned by `../georeferencing-and-crs/`.
- DEMs, georeferenced rasters, ASCII grids, web DEMs, and basemap tiles are owned by `../raster-dem-and-basemaps/`.
- Dropping imported vectors to a terrain mesh, Delaunay/Voronoi terrain creation, and terrain analysis materials are owned by `../terrain-mesh-and-analysis/`.
