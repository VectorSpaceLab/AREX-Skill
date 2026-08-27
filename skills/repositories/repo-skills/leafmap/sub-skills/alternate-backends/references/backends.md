# Alternate Backend Selection

## Purpose

Use this table when you need to choose among the optional visual backends in leafmap.

| Backend | Best for | Dependency signal | Notes |
| --- | --- | --- | --- |
| `kepler` | Kepler.gl notebook maps | `keplergl` | Optional import; not installed in the minimum smoke environment. |
| `plotlymap` | Plotly-based notebook maps | `plotly` | Imported successfully during inspection. |
| `bokehmap` | Bokeh notebook maps | `bokeh` | Optional import; missing in the minimum smoke environment. |
| `deck` | Pydeck-style layers | `pydeck` | Optional import; missing in the minimum smoke environment. |
| `deckgl` | Lonboard/deck.gl-style maps | `lonboard` | Optional import; missing in the minimum smoke environment. |
| `heremap` | HERE widget maps | HERE widget stack and API key | Optional import; inspection showed a shapely-related import failure in the current environment. |
| `mapbox` | Mapbox-style maps | Mapbox-related widget stack | Imported successfully during inspection. |

## Selection guidance

- Use `plotlymap` or `mapbox` only when the user explicitly wants that rendering style.
- Use `kepler`, `bokeh`, `deck`, or `deckgl` when the notebook example or backend name is already part of the request.
- Use `heremap` only when the user has the HERE widget stack and an API key.
- If the optional backend is missing, prefer a verified backend instead of promising that the optional one can be made to work.

## Smoke helper

Run the shared root helper with:

```bash
python scripts/check_leafmap_smoke.py --mode optional
```

That mode reports which optional backend imports succeed and which fail with a missing-dependency or compatibility error.
