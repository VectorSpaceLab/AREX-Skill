---
name: mapping-location-services
description: "Operate map widgets, web maps and web scenes, geocoding, network
  analysis, and geoenrichment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mapping and location services router

Use this sub-skill for map widgets, web maps, web scenes, symbol and renderer choices, popups, geocoding and reverse geocoding, batch and custom geocoders, routing and service-area solvers, OD matrices, vehicle routing, and geoenrichment variables or reports.

Do **not** use this sub-skill for portal item lifecycle and admin operations, feature schema or editing work, or raster and imagery analysis. Route those to the sibling sub-skills instead.

## Operating rules

- Map widgets and 3D scenes depend on the `arcgis-mapping` package and a notebook-style front end. Import success does not guarantee that a widget will render in the browser.
- Treat geocoding, routing, and geoenrichment as remote service operations. Do not attempt live calls unless the user has provided the target GIS/service context, credentials or profile details, and explicit approval for the service cost.
- Before batch geocoding, check the geocoder object, batch-size limits, and whether `for_storage` is required for the intended use.
- Before routing, service-area, OD matrix, or VRP work, validate stop or order feature sets, travel mode, time windows, time zone handling, and network service availability.
- Before geoenrichment or report generation, validate the study-area shape, country/source availability, data collections, analysis variables, and export format.
- Keep content ownership, sharing, cloning, delete, and other portal administration tasks out of this sub-skill.

## Reference map

- [Workflow guide](references/mapping-and-location-workflows.md): notebook-derived patterns for map widgets, renderers, popups, geocoding, routing, and geoenrichment.
- [Service API reference](references/service-api-reference.md): verified import surface plus the key class and function signatures to use here.
- [Troubleshooting](references/troubleshooting.md): Jupyter widget issues, geocoder and credit caveats, malformed route inputs, and geoenrichment/report failures.
- [Import smoke script](scripts/check_location_service_imports.py): safe import and signature checker with no locator, network, or enrichment calls.

## First response pattern

1. Decide whether the user needs map display, geocoding, routing, or geoenrichment.
2. If the request is service-backed, ask only for the missing GIS, service, credential, or credit details needed to choose a safe path.
3. Use the workflow guide for the notebook-style recipe and the service API reference for exact arguments.
4. Use the troubleshooting guide when imports work but the widget, locator, route, or report path fails.
5. Use the smoke script only for import and signature triage; never as a substitute for live service execution.
