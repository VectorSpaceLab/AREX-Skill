# Troubleshooting

## 1) Map widget or scene does not render

**Likely cause**: Python imports are fine, but the notebook front end, browser, or widget package is missing or incompatible.

**Check**

- Confirm the `arcgis-mapping` package is installed alongside `arcgis`.
- Confirm you are running in a notebook-style environment that can render widgets.
- Make sure the map or scene object is the visible result of the cell.
- If you are outside a widget-capable notebook, use `Map.export_to_html(...)` or save the map or scene only if persistence is intended.

**Do not assume** a successful import means the interactive widget will render.

## 2) Custom symbols, renderers, or popups look wrong

**Likely cause**: the layer is not loaded, the map is not rendered, or the wrong object is being styled.

**Check**

- Confirm the layer has been added to the map content.
- Confirm you are styling a rendered layer through `content.renderer(index).smart_mapping()`.
- Confirm the symbol type matches the geometry type.
- For popups, confirm the `PopupInfo` or popup element is attached when the layer is added or drawn.

## 3) Geocoding problems

### No results or weak matches

**Check**

- Verify the address text, category, country code, and search extent.
- If the result should come from a service-specific geocoder, confirm the correct geocoder object was chosen from the GIS.
- If a secure locator is required, make sure the geocoder has access through the supplied GIS.

### Batch geocoding hits a limit

**Check**

- Read the geocoder’s `MaxBatchSize` and `SuggestedBatchSize` before sending a large list.
- Split large inputs into smaller batches.
- Treat batch geocoding as a service-backed operation that can consume credits.

### Storage or reuse of results is requested

**Check**

- Use `for_storage=True` only when the results will be stored or reused beyond a transient display.
- If the user wants persisted output, explain the implications before running.

### Reverse geocoding returns the wrong place

**Check**

- Confirm the input is `x, y` order.
- Confirm the coordinate reference system is what the service expects.
- Pass an explicit point object or spatial reference when the coordinates are not already unambiguous.

## 4) Routing, service area, OD matrix, or VRP failures

### Malformed stops, incidents, or orders

**Check**

- Confirm the inputs are `FeatureSet` objects or supported feature collections.
- Confirm the required geometry and routing fields exist.
- Check for duplicate, missing, or invalid network location fields.
- Decide whether to ignore invalid locations or fail fast.

### No network-analysis service is available

**Check**

- Do not try to fake a local solve.
- Validate the inputs and explain that route, service-area, OD, or VRP solves need an appropriate network service and permissions.

### Time windows or travel mode errors

**Check**

- Confirm `travel_mode` is valid for the service.
- Confirm `time_of_day` and the time-zone parameters are aligned.
- For VRP and route sequencing, confirm the time-window settings are intentional.

### Service cost or performance concern

**Check**

- Warn before long-running or batch solves.
- Explain that route, service-area, OD, and VRP operations can consume credits and may return asynchronous jobs.

## 5) Geoenrichment or report failures

### Study area or variable errors

**Check**

- Confirm the study area type is supported for the chosen call path.
- Confirm `data_collections` and `analysis_variables` are valid IDs.
- Confirm the country/source is available from the active GIS or Business Analyst source.

### Report export errors

**Check**

- Confirm the output folder exists or can be created.
- Confirm the export format is supported by the chosen report.
- Confirm the report id exists for the active country/source.

### Source or credits unavailable

**Check**

- Verify whether the task expects Web GIS geoenrichment or a local Business Analyst source.
- Remind the user that enrichment and report generation are service-backed and can consume credits.

## 6) Minimal information to ask for when the request is underspecified

Ask for only the missing items needed to avoid guesswork:

- Map or scene output target: notebook widget, saved item, or HTML export
- Geocoder source: GIS, URL, or service item
- Routing source: network service or layer URL, plus stop or order schema
- Geoenrichment source: Web GIS or Business Analyst, plus country and report requirements
