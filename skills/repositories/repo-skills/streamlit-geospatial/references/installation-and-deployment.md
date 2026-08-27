# Installation and deployment

Read this reference before preparing a clean runtime, deploying to Streamlit
Cloud, or adapting the repository's host setup.

## Python and geospatial dependencies

The repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, package source
root, or console entry point. Its runtime dependency list is `requirements.txt`:
GDAL, Folium, `geemap[extra]`, GeoPandas, Kepler.gl, Leafmap,
LocalTileServer, Plotly, PyArrow, Streamlit, `streamlit-folium`, and
`streamlit-keplergl`. The inspected Python 3.11 environment also needed Fiona
for the explicit KML/vector page imports and a `setuptools<81` compatibility pin
for the installed Kepler.gl release's `pkg_resources` import.

The host dependency list in `packages.txt` names `ffmpeg`, `gifsicle`,
build tools, Python/GDAL development headers, GDAL/PROJ/GEOS libraries, and
PROJ binaries. Install these through the host or deployment platform's normal
package manager; do not make the runtime skill silently run `sudo` or mutate a
shared machine.

Use a private virtual environment or Conda prefix. Do not install the app's
requirements into DisCo's Python or a user-owned environment without approval.
After installation, run:

```bash
python -m pip check
USE_FOLIUM=1 python -c "import streamlit, leafmap, geemap, geopandas, fiona, folium, pydeck, ee, rasterio, localtileserver, keplergl"
python -m streamlit --help
```

`GDAL` appears in the requirements file because some geospatial wheels and
raster workflows depend on GDAL functionality. The inspected wheel set
provided Fiona, Pyogrio, Rasterio, PROJ, GEOS, and Shapely imports; it did not
provide a separate `osgeo` module, so do not use an `osgeo` import as the
minimum smoke check unless you deliberately install that binding.

## Streamlit entry point

Run the app from its root with:

```bash
USE_FOLIUM=1 streamlit run Home.py
```

`Procfile` expresses the deployment shape as `sh setup.sh && streamlit run
Home.py`. The setup script is not a safe generic installer: its apt commands
are commented examples, and its active command writes
`~/.streamlit/config.toml` using the deployment `PORT`. In a managed service,
set headless mode, port, CORS policy, and secrets through the platform or an
explicit project-local config instead of mutating a shared home directory.

The `pages/` directory is a Streamlit multipage convention. Add a page with a
stable numeric prefix and an emoji only when the target deployment supports
that filename; keep imports and page configuration at the top of the file.

## External prerequisites

- Earth Engine pages require an authenticated Earth Engine account/project and
  a secret such as the `EARTHENGINE_TOKEN` variable. Authentication is a
  deliberate runtime boundary, not part of installation verification.
- WMS, XYZ, COG, housing, historical tile, and sample point workflows require
  network access and may be rate-limited, changed, or unavailable.
- Timelapse output may require `ffmpeg`/`gifsicle` for MP4 conversion or GIF
  reduction. Keep ROI, time span, dimensions, and frame rate small first.
- Upload pages need supported GeoPandas/Fiona/Pyogrio drivers and should
  validate CRS and geometry before rendering.

## Safe deployment checklist

1. Create an isolated Python 3.11 environment.
2. Install `requirements.txt` and only the host libraries needed by selected
   workflows.
3. Set `USE_FOLIUM=1` before the Streamlit process imports geemap.
4. Run the root environment checker and `py_compile` on `Home.py` and pages.
5. Configure secrets and remote service access in the deployment platform.
6. Start `streamlit run Home.py` and exercise one small local/vector page.
7. Add remote Earth Engine or HTTP workflows only after their service-specific
   preflight succeeds.
