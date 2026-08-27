# Alternate Backends Troubleshooting

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ImportError` for `keplergl`, `bokeh`, `pydeck`, or `lonboard` | Optional backend package is not installed | Either install the backend or switch to a verified backend such as MapLibre, ipyleaflet, or folium. |
| HERE backend import fails | HERE widget stack or a required API key is missing | Confirm the HERE prerequisites before trying again. |
| `heremap` compatibility error | The current Python/package combination does not satisfy that backend's dependencies | Record the backend as unverified or use another backend. |
| Backend choice feels arbitrary | The workflow has not been routed to the right visual style | Re-read `references/backends.md` and choose based on the requested map style rather than the source module name. |

## Recovery checklist

1. Run `python scripts/check_leafmap_smoke.py --mode optional`.
2. If the backend is optional, decide whether to install it or route the task to a verified backend.
3. If the task only needs a quick map, choose the simplest verified backend instead of chasing an uninstalled optional one.

## When to stop

Stop and hand the task back when:
- the backend requires a key the user does not have,
- the backend import fails because the environment is incompatible,
- or the user really wanted a default map workflow rather than a backend comparison.
