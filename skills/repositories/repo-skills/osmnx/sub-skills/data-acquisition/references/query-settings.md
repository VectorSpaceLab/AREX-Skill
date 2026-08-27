# Query and settings reference

This page condenses the configuration knobs that affect OSMnx data acquisition. Use it when you need to decide which settings to change before geocoding, querying Overpass, or replaying cached responses.

## Public API baseline

For ordinary public Nominatim and Overpass use, keep the defaults unless the task clearly needs a different instance, historical snapshot, or cache behavior.

- `use_cache=True`
- `cache_only_mode=False`
- `overpass_rate_limit=True`
- `requests_timeout=180`
- `http_user_agent` and `http_referer` set to identify the client
- `default_crs="epsg:4326"`

## Settings by concern

| Setting | What it controls | When to change it | Notes |
| --- | --- | --- | --- |
| `use_cache` | Whether HTTP responses are cached locally. | You want repeatable queries or fewer public API calls. | Applies to both Nominatim and Overpass requests. |
| `cache_folder` | Where cached responses are stored. | You need a different cache location for the run. | Keep it local and writable. |
| `cache_only_mode` | Save Overpass responses and stop before graph/feature assembly. | You are warming cache entries first, or building a no-network plan. | This intentionally raises `CacheOnlyInterruptError` after the response is saved. |
| `requests_timeout` | HTTP request and Overpass execution timeout. | Queries are slow, large, or served by a custom instance. | Also used in the default Overpass settings string. |
| `requests_kwargs` | Extra `requests` options. | You need proxies, auth, certificates, or custom verification. | Useful keys include `verify`, `cert`, `auth`, and `proxies`. |
| `http_user_agent` | HTTP `User-Agent` header. | You need a custom client identity. | Keep it explicit for public APIs. |
| `http_referer` | HTTP `Referer` header. | Your deployment policy requires a custom referer. | Keep it stable for repeatable requests. |
| `http_accept_language` | HTTP `Accept-Language` header. | You want a different language bias for Nominatim. | Default is English. |
| `nominatim_url` | Nominatim base URL. | You use a custom or self-hosted Nominatim instance. | Point it at the base endpoint, not a specific search URL. |
| `nominatim_key` | Nominatim API key. | Your Nominatim instance requires a key. | Public OSMNominatim usually does not require one. |
| `overpass_url` | Overpass base URL. | You use a self-hosted or alternative Overpass instance. | Point it at the base endpoint, not `/interpreter`. |
| `overpass_rate_limit` | Whether to respect Overpass status/slot waiting. | You own the Overpass instance or have explicit permission to ignore slot polling. | Keep it `True` for public instances. |
| `overpass_memory` | Overpass `[maxsize:...]` value in bytes. | Your instance needs a specific memory limit. | `None` lets the server choose. |
| `overpass_settings` | The Overpass prefix string. | You need a historical snapshot or custom Overpass options. | Default is `[out:json][timeout:{timeout}]{maxsize}`. |
| `default_access` | Access filter baked into built-in street network filters. | You need to alter the built-in private/public access behavior. | Used by default network presets, not by arbitrary custom filters. |
| `useful_tags_node` | OSM node tags copied into graph node attributes. | You want extra node metadata retained. | Keep only tags you actually need. |
| `useful_tags_way` | OSM way tags copied into graph edge attributes. | You want extra edge metadata retained. | Keep only tags you actually need. |
| `bidirectional_network_types` | Network types built as fully bidirectional graphs. | You need a different bidirectional preset. | Default includes `walk`. |
| `max_query_area_size` | Maximum polygon area before OSMnx subdivides the query. | You are querying very large polygons. | Smaller values mean more requests; larger values mean fewer but bigger requests. |
| `default_crs` | CRS assigned to newly created graphs and features. | You have a special downstream convention. | For acquisition workflows, stay in `epsg:4326`. |

## Historical snapshot settings

To request historical Overpass data, encode the date directly in `overpass_settings`:

```python
import osmnx as ox

ox.settings.overpass_settings = '[out:json][timeout:90][date:"2019-10-28T00:00:00Z"]'
```

Guidance:

- Keep the date inside the Overpass settings string.
- Preserve the timeout and maxsize placeholders or provide explicit values.
- Use a stable UTC timestamp format when you need a reproducible snapshot.
- Expect the historical query to be slower and potentially larger than a current-data query.

## Query behavior reminders

- `graph_from_point` and `graph_from_address` can use either geographic bbox truncation or network-distance truncation.
- `features_from_*` tags are unioned, not intersected.
- `custom_filter` strings intersect; lists union.
- `cache_only_mode=True` is a deliberate short-circuit, not an error.
- Public Nominatim and Overpass usage should remain rate-limited and cache-aware.

## When not to change settings here

Do not use this file to plan graph validation, projection, persistence, routing, or plotting behavior. Those workflows belong to sibling routes.
