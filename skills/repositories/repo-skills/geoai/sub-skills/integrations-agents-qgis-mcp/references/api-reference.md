# Integration API Reference

This reference records the integration-layer API surface that this sub-skill owns.
It is intentionally routing-focused: model construction, agent classes, map/catalog/STAC tools, and MCP tool names.

## Extra and import notes

- The `geoai.agents` package is optional and depends on Strands extras.
- If imports fail with `No module named 'strands'`, install the GeoAI package with its agents extra or the equivalent environment bundle that provides `strands-agents`, `strands-agents-tools`, and the relevant model provider extras.
- The package may also need `leafmap`, `boto3`, `ipywidgets`, and `ipyevents` depending on which agent class you use.

## Model and provider constructors

| Constructor | Purpose | Key defaults | Secrets / env |
| --- | --- | --- | --- |
| `create_ollama_model(host='http://localhost:11434', model_id='llama3.1', client_args=None)` | Local Ollama-backed model wrapper. | Host points to the local Ollama server. | No API key by default. |
| `create_openai_model(model_id='gpt-4o-mini', api_key=None, client_args=None)` | OpenAI-compatible chat model wrapper. | Uses the OpenAI API shape. | `OPENAI_API_KEY` when `api_key` is not passed. |
| `create_anthropic_model(model_id='claude-sonnet-4-20250514', api_key=None, client_args=None)` | Anthropic chat model wrapper. | Uses the Anthropic API shape. | `ANTHROPIC_API_KEY` when `api_key` is not passed. |
| `create_bedrock_model(model_id='anthropic.claude-sonnet-4-20250514-v1:0', region_name=None, boto_session=None, boto_client_config=None)` | AWS Bedrock wrapper. | Pass AWS region/session as needed. | Uses normal AWS credentials and region resolution. |
| `create_gemini_model(model_id='gemini-2.5-flash', api_key=None, client_args=None)` | Google Gemini wrapper. | Uses the Gemini API shape. | `GOOGLE_API_KEY` when `api_key` is not passed. |
| `create_minimax_model(model_id='MiniMax-M3', api_key=None, client_args=None)` | MiniMax OpenAI-compatible wrapper. | Sets `base_url='https://api.minimax.io/v1'`. | `MINIMAX_API_KEY` when `api_key` is not passed. |
| `create_vllm_model(base_url='http://localhost:8000/v1', model_id='meta-llama/Llama-3.1-8B-Instruct', api_key='EMPTY', client_args=None)` | vLLM OpenAI-compatible wrapper. | Intended for a locally or remotely hosted vLLM server. | Uses the server key only if the server requires one. |

### Routing rule for string model values

`GeoAgent`, `STACAgent`, and `CatalogAgent` use string-based routing so users can pass a model name instead of a prebuilt provider object.

- Strings containing `:` or starting with `llama` route to Ollama.
- Strings starting with `minimax` route to MiniMax.
- Existing provider objects are copied into fresh instances when possible.
- Other plain strings route to Bedrock.

## Agent classes

| Class | Purpose | Notable methods |
| --- | --- | --- |
| `GeoAgent(model='llama3.1', map_instance=None, system_prompt='default', model_args=None)` | Interactive map assistant built on Leafmap. | `ask`, `show_ui` |
| `STACAgent(model='llama3.1', system_prompt='default', endpoint='https://planetarycomputer.microsoft.com/api/stac/v1', model_args=None, map_instance=None)` | STAC search assistant backed by `STACTools`. | `ask`, `search_and_get_first_item`, `show_ui` |
| `CatalogAgent(model='llama3.1', system_prompt='default', catalog_url=None, catalog_df=None, model_args=None)` | Catalog search assistant backed by `CatalogTools`. | `ask`, `search_datasets` |

### Direct helper methods

These helpers are preferred when the user does not need LLM routing:

- `CatalogAgent.search_datasets(...)` returns structured dataset dictionaries.
- `STACAgent.search_and_get_first_item(...)` returns the first matched STAC item as a dictionary.
- `GeoAgent.ask(...)`, `STACAgent.ask(...)`, and `CatalogAgent.ask(...)` still exist for routed agent conversations, but they depend on Strands availability.

## Map tools

`MapTools` is the Leafmap-facing tool collection used by `GeoAgent`.
Key methods include:

- `create_map(center_lat, center_lon, zoom, style, projection, use_message_queue)`
- `fly_to(longitude, latitude, zoom=12)`
- `add_basemap(name)`
- `add_vector(data, name=None)`
- `add_raster(source, indexes=None, colormap=None, vmin=None, vmax=None, nodata=None, name='Raster', fit_bounds=True, visible=True, opacity=1.0, overwrite=True)`
- `add_cog_layer(url, name=None, attribution='TiTiler', opacity=1.0, visible=True, bands=None, nodata=0, titiler_endpoint=None)`
- `remove_layer(name)`
- `save_map(output='map.html', title='My Awesome Map', width='100%', height='100%', replace_key=False, remove_port=True, preview=False, overwrite=False)`
- `add_marker(lng_lat, popup=None, options=None)`
- `add_overture_3d_buildings(release=None, style=None, values=None, colors=None, visible=True, opacity=1.0, tooltip=True, template='simple', fit_bounds=False)`
- `zoom_to(zoom, options={})`, `jump_to(options={})`, `pan_to(lnglat, options={})`, `rotate_to(bearing, options={})`, `set_pitch(pitch)`

Additional styling and layer helpers exist for legends, colour bars, labels, WMS/PMTiles/vector tiles, terrain, and draw controls.

## Catalog tools

`CatalogTools` covers catalog search and spatial search.
Key methods include:

- `search_datasets(keywords=None, dataset_type=None, provider=None, start_date=None, end_date=None, max_results=10)`
- `search_by_region(bbox=None, location=None, keywords=None, dataset_type=None, provider=None, start_date=None, end_date=None, max_results=10)`
- `get_dataset_info(dataset_id)`
- `list_dataset_types()`
- `list_providers()`
- `get_catalog_stats()`
- `geocode_location(location_name)`

## STAC tools

`STACTools` covers Planetary Computer STAC discovery and item lookup.
Key methods include:

- `list_collections(filter_keyword=None, detailed=False)`
- `search_items(collection, bbox=None, time_range=None, query=None, limit=10, max_items=1)`
- `get_item_info(item_id, collection)`
- `geocode_location(location_name)`
- `get_common_collections()`

## Adjacent agent utilities

`DataTools` is present in `geoai.agents` as an adjacent utility surface.
It is useful for routing and inspection, but its heavy geospatial work should still be delegated to the geospatial-data sub-skill when the user is doing actual raster/vector processing.

Key methods:

- `inspect_raster(raster_path)`
- `inspect_vector(vector_path)`
- `clip_raster(input_raster, output_raster, min_lon, min_lat, max_lon, max_lat)`
- `raster_to_vector(raster_path, output_path)`
- `list_files(directory, extension=None)`

## MCP server tool names

The GeoAI MCP server exposes these integration-facing tools:

- `segment_objects_with_prompts`
- `auto_segment_image`
- `detect_and_classify_features`
- `classify_land_cover`
- `detect_temporal_changes`
- `download_satellite_imagery`
- `prepare_training_data`
- `extract_features_with_foundation_model`
- `estimate_canopy_height`
- `analyze_with_vision_language_model`
- `clean_segmentation_results`
- `list_available_files`

These tools are wrappers over GeoAI modules and should be treated as routing entry points.
Heavy operations may still require optional backend packages, model files, or network access in the target environment.

## QGIS plugin integration entry points

The QGIS plugin exposes the following user-facing actions:

- Tree Segmentation
- Water Segmentation
- Moondream VLM
- Segment Anything
- Semantic Segmentation
- Instance Segmentation
- Clear GPU Memory
- Check for Updates
- Generate Diagnostics Report

Those actions are UI routes into the underlying dependency installer, workers, and model wrappers.
