# Interactive Maps Troubleshooting

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Error displaying widget: model not found` | ipyleaflet widget support is missing or the kernel needs a restart | Restart the notebook kernel and rerun `scripts/check_leafmap_smoke.py --mode core`. |
| Map works in Colab but not locally, or vice versa | Backend fallback is different across notebook environments | Use `leafmap.Map` to let the package choose, or explicitly import `leafmap.foliumap` / `leafmap.leafmap`. |
| Vector layer import fails | `geopandas`, `shapely`, or file-driver dependencies are missing | Install the missing dependency and rerun the interactive smoke. |
| HTML export does not show the expected layer | A backend-specific method behaves differently than the other backend | Check `references/api-reference.md` and switch to the backend that supports the method. |
| Toolbar or widget controls are absent | The map was created without the ipyleaflet backend | Use `leafmap.leafmap` instead of `leafmap.foliumap`. |

## Recovery checklist

1. Confirm the backend choice.
2. Run `python scripts/check_leafmap_smoke.py --mode core`.
3. If the smoke passes but the notebook still fails, restart the kernel and try again.
4. If the requested method is not implemented in the selected backend, route the task to the backend that supports it.

## When to stop

Stop and change backend or scope when the user actually needs:
- STAC / Planetary Computer / OSM / fire / Terrascope data retrieval,
- a MapLibre viewer or CLI,
- or an optional backend that is missing from the environment.
