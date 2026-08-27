# Troubleshooting remote geospatial workflows

Use these recoveries in order. Do not expose secret values, silently retry
an expensive remote operation, or turn an unverified result into a success.

## Authentication and token failures

**Symptoms:** initialization rejects the token name, authentication is
required, a project is missing, or an Earth Engine call returns permission or
quota errors.

**Recovery:** confirm that the caller supplied the intended token-variable name
and that a secret exists without printing its value. Confirm the selected
`auth_mode`, `auth_args`, and optional `project` with the caller, then invoke
`ee_initialize` once at the explicit service boundary. If interactive or
project approval is required, stop and request it. The local validator can
check only token-variable presence; it cannot prove authentication. Do not
repeat an unchanged request after quota or authorization failure.

## Invalid asset ID or public-asset drift

**Symptoms:** `ee.ImageCollection.load` fails, a constructor rejects an ID, a
known state/country has no building-footprint data, or a previously documented
public dataset is no longer returned.

**Recovery:** classify the intended asset as image, image collection, or feature
collection. Search the catalog again with `search_ee_data`, inspect the returned
ID/type/title, and only then construct the matching Earth Engine object. Treat
IDs from the application evidence as examples subject to catalog drift. If a
catalog record or remote constructor does not confirm the asset, report the
asset as unavailable or changed; do not substitute a similarly named asset
without user approval.

## Malformed palette or visualization parameters

**Symptoms:** JSON parsing fails, a palette is not a list of strings, a
visualization value has an unexpected type, or map/timelapse rendering rejects
parameters.

**Recovery:** stop before the remote call. Use the validator on a JSON object;
for a palette require a JSON list of non-empty strings, and for visualization
parameters require a JSON object. Ask the caller to correct the field. Keep
Earth Engine-specific semantics (band names, min/max ranges, palette color
names) separate from syntax validation; only the remote rendering call can
confirm semantic compatibility.

## ROI upload and CRS failures

**Symptoms:** upload cannot be parsed, a KML driver is unavailable, the GeoDataFrame
has no CRS, geometries are empty/invalid, coordinates are out of bounds, or
`gdf_to_ee` rejects the object.

**Recovery:** reject malformed input before authentication. Confirm GeoJSON
geometry is present and non-empty, repair or redraw invalid geometry rather
than guessing, and reproject a known CRS to WGS84 before
`gdf_to_ee(gdf, geodesic=False)`. A missing CRS must be resolved by the caller;
do not assume it is longitude/latitude. For KML, ensure the runtime has the
needed Fiona driver. For zipped upload, validate that it contains a readable
supported vector dataset. Try a small WGS84 rectangle as a control to separate
ROI parsing from Earth Engine availability.

## Empty collection or no imagery

**Symptoms:** an image collection is empty for the ROI/date range, `.first()`
returns no usable image, band probing fails, or a timelapse returns no frames.

**Recovery:** distinguish an empty result from an invalid asset. Confirm the
asset type and band names, then narrow or shift the dates, use a valid ROI,
or choose a collection with coverage. For cloud-masked Landsat/Sentinel-2,
relaxing cloud filtering should be an explicit approved change. For NLCD,
check the selected supported year. For building footprints, an empty feature
collection means coverage is not established. Do not render a blank result as
successful imagery.

## Oversized ROI or time span

**Symptoms:** request times out, memory/pixel limits are exceeded, generation
runs too long, or the app reports that too much data was requested.

**Recovery:** do not retry unchanged. Reduce ROI area first, then shorten the
date interval, lower dimensions and frame rate, choose a coarser frequency,
use a larger `step`, or split the job into independent bounded outputs. GOES
needs especially tight datetime intervals; global MODIS requests need an
explicit output-size limit even when spatial coverage is intended. Preserve
the original request as a failed attempt and report the bound that changed.

## GIF, MP4, ffmpeg, and gifsicle failures

**Symptoms:** Earth Engine generation appears complete but the GIF is absent,
GIF optimization fails, or MP4 playback is unavailable.

**Recovery:** check the caller-selected GIF path and file existence first. If
GIF exists but MP4 does not, classify it as a local conversion failure and
verify `ffmpeg` before rerunning with `mp4=True`. If reduction fails, verify
`gifsicle` or omit optimization and keep the original GIF. Do not claim that
Earth Engine failed solely because media conversion failed. A nonexistent GIF
means the generator result is unverified; inspect the captured exception
without placing secret values in logs.

## Public catalog and API drift

**Symptoms:** a helper signature differs, legend names are unavailable, a
parameter is rejected, or an example asset has moved.

**Recovery:** inspect the installed helper signature and current returned
metadata in the caller's environment. This skill records the inspected
geemap `0.37.2` signatures, but the runtime may differ. Adapt only parameter
names confirmed by inspection, update the local evidence record, and re-run
static/config checks. Keep the remote result unverified unless an approved
live call succeeds.

## Difficult synthetic cases

1. Give a caller a valid WGS84 polygon, a reversed date interval, and a palette
   JSON object instead of a palette list. The safe preflight must identify the
   date and palette errors without importing Earth Engine or authenticating.
2. Give a valid small ROI and a catalog-selected collection, then request a
   global multi-decade timelapse with MP4. The route must choose one family,
   reject the unbounded request, and recommend bounded reductions plus an
   `ffmpeg` prerequisite check rather than launching a remote call.
