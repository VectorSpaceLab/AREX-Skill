# Troubleshooting for maps and layers

For install/import issues, missing optional dependencies, browser/CDN failures, or skill staleness, also read `../../references/troubleshooting.md`.

## Custom tiles and attribution

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Custom tiles must have an attribution.` | A tile URL was passed without `attr` | Add a clear attribution string or use a built-in tileset/provider name that carries one. |
| Built-in tiles render in Python but not in the browser | The browser cannot fetch the remote tile URL | Check network access, CSP, ad blockers, and mixed-content restrictions. |
| Tiles look wrong or overwrapped | `no_wrap`, `tms`, or the tile provider choice does not match the data source | Recheck the tile layer options before changing the map center. |

## Layer ordering and controls

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A control does not show a layer | The layer was added after the control or has `control=False` | Add the layer first, then add `LayerControl` last. |
| A group toggles unexpectedly | The layer was added to the wrong `FeatureGroup` or `LayerGroup` | Move the layer into the intended group and check its `name`/`show` flags. |
| Panes do not appear to work | The element was not assigned to the expected pane | Create the `CustomPane` first and pass the pane name to the layer that should live there. |

## Invalid locations and bounds

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A marker or shape is in the wrong place | `[lat, lon]` was mixed up with `[lon, lat]` | Fix the coordinate order and compare with the map center before blaming Folium. |
| `validate_location` / `validate_locations` rejects the input | The point or path data are the wrong shape or contain invalid values | Use plain numeric coordinate pairs, not sets, dicts, ranges, or strings. |
| `fit_bounds()` does nothing useful | The layer has no finite bounds yet | Add real geometry first, or fit to a layer that already contains points. |

## Image and video overlays

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImageOverlay` is shifted or stretched | The source image is not aligned to the requested geographic bounds | Verify the bounds and use `mercator_project=True` when appropriate. |
| The array overlay seems upside down | The default row origin is not the one you intended | Pass `origin="lower"` when the first array row should map to the southern edge. |
| A video overlay does not visually play | The browser blocked the media URL or format | Check the browser console and confirm the video URL is reachable and allowed. |

## Browser output and PNG export

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `_repr_html_()` works but the browser page is blank | Browser-side assets were blocked or failed to load | Inspect the browser network tab and console; fix CDN/CSP issues rather than Folium serialization. |
| `_repr_png_()` returns `None` | PNG export is disabled | Set `png_enabled=True` on the map before calling the PNG representation. |
| PNG export errors mention Selenium or a browser driver | The environment is missing the screenshot stack | Install the browser driver and Selenium support package before retrying. |
| `show_in_browser()` blocks the terminal | The helper is intentionally waiting for manual interruption | Use it only when you want an interactive browser session; otherwise save HTML and open it yourself. |

## Notebook display and embedding

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Notebook output shows a trust warning | The notebook is not trusted | Save the map to HTML or trust the notebook before retrying. |
| The Flask example fails to import Flask | The optional dependency is missing | Install Flask only when you need the embedding example. |
| A custom JS/CSS resource does not behave as expected | The asset URL or browser policy is wrong | Verify the asset URL first, then the browser console and page policy. |

## Quick triage sequence

1. Render the smallest possible map.
2. Remove custom panes, external tiles, and browser extras.
3. Confirm the coordinates and the layer order.
4. Add the browser-side features back one at a time.
5. If PNG export is the only failing part, debug Selenium/browser setup separately from Folium.
