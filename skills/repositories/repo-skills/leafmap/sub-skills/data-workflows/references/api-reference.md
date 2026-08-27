# Data Workflows API Reference

## Purpose

This reference captures the verified high-frequency data helpers that leafmap users most often need for conversion, download, and source discovery.

## Verified entry points

| API | Verified signature | Use |
| --- | --- | --- |
| `leafmap.common.csv_to_gdf` | `in_csv, latitude='latitude', longitude='longitude', geometry=None, crs='EPSG:4326', encoding='utf-8', **kwargs` | Convert tabular point data to a GeoDataFrame.
| `leafmap.common.csv_to_geojson` | `in_csv, out_geojson=None, latitude='latitude', longitude='longitude', encoding='utf-8'` | Convert a CSV file to GeoJSON.
| `leafmap.common.gdf_to_geojson` | `gdf, out_geojson=None, epsg=None, tuple_to_list=False, encoding='utf-8'` | Convert a GeoDataFrame to GeoJSON.
| `leafmap.common.get_local_tile_url` | verified callable | Build a local tile URL for a raster source.
| `leafmap.common.set_proxy` | `port=1080, ip='http://127.0.0.1'` | Configure proxy variables for restricted-network environments.
| `leafmap.common.find_files` | verified callable | Search for files in a directory tree.
| `leafmap.stac.cog_tile` | `url, bands=None, titiler_endpoint=None, **kwargs` | Build a tile URL for a COG.
| `leafmap.stac.stac_search` | `url, method='POST', max_items=None, limit=100, ...` | Query a STAC endpoint.
| `leafmap.download.download_naip` | `bbox, output_dir, year=None, max_items=10, overwrite=False, preview=False, **kwargs` | Download NAIP imagery from Planetary Computer.
| `leafmap.download.download_overture_buildings` | `bbox, output=None, overture_type='building', **kwargs` | Download Overture building data.
| `leafmap.download.view_pc_items` | verified callable | Build a Planetary Computer item viewer.
| `leafmap.osm.osm_gdf_from_place` | `query, tags, which_result=None, buffer_dist=None` | Query OSM features for a named place.
| `leafmap.pc.get_pc_collection_list` | verified callable | List Planetary Computer collections.
| `leafmap.pc.get_bands` | `collection, item=None` | Inspect collection bands.
| `leafmap.fire.search_fires` | `bbox=None, place=None, collection='snapshot_perimeter_nrt', ...` | Search fire datasets.
| `leafmap.terrascope.search` | `collection, bbox=None, start=None, end=None, max_cloud_cover=None, limit=None, unique_dates=True, **kwargs` | Search Terrascope collections.
| `leafmap.terrascope.create_time_layers` | `items, asset_key='NDVI', colormap='RdYlGn', vmin=0, vmax=250` | Build time-layer dictionaries for maps.

## Notes from inspection

- `leafmap.download` imports successfully after installing `planetary-computer`, `rioxarray`, and `xarray`.
- Many helper names are layered on top of network services or optional file drivers, so import success is not the same as live-data success.
- For simple smoke tests, prefer local CSV or in-memory GeoDataFrame conversions first.

## Other useful helpers

- `leafmap.common.read_raster`
- `leafmap.common.read_netcdf`
- `leafmap.common.read_parquet`
- `leafmap.common.read_lidar`
- `leafmap.common.vector_to_geojson`
- `leafmap.common.read_file`
- `leafmap.common.read_file_from_url`
- `leafmap.common.download_file`
- `leafmap.common.download_from_url`

## Data layout reminders

- `csv_to_gdf` and friends expect valid coordinate columns and a sensible CRS.
- STAC and Planetary Computer helpers usually expect endpoints or collection names, not raw file paths.
- OSM helpers need a query place/name plus tag filters.
- Fire and Terrascope helpers usually work on bbox or time-range filters.
