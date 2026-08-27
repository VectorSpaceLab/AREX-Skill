# Client integration

## Purpose

Read this when the task is about using OpenFreeMap in a website or app rather than operating the repo itself.

## Style URLs

OpenFreeMap styles are served from the public tile instance under URLs like:

- `https://tiles.openfreemap.org/styles/bright`
- `https://tiles.openfreemap.org/styles/liberty`
- `https://tiles.openfreemap.org/styles/positron`
- `https://tiles.openfreemap.org/styles/dark`
- `https://tiles.openfreemap.org/styles/fiord`

The `3D` demo on the public site is a `liberty` style plus camera settings, not a separate style family.

## MapLibre GL JS

This is the preferred integration path.

```html
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet" />
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const map = new maplibregl.Map({
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [13.388, 52.517],
    zoom: 9.5,
    container: 'map',
  })
</script>
```

## Mapbox migration

If a project still uses Mapbox GL JS 2.x+, the recommended migration is to switch to MapLibre GL JS and keep the style URL pointed at OpenFreeMap.

Use this when the request mentions:

- Mapbox GL JS 2.x or later
- a need for an open-source Mapbox-compatible client
- swapping only the client library while leaving the style URL unchanged

## Leaflet

Use the MapLibre GL Leaflet bridge when a Leaflet map needs vector tiles.

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/@maplibre/maplibre-gl-leaflet/leaflet-maplibre-gl.js"></script>
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const map = L.map('map').setView([52.517, 13.388], 9.5)
  L.maplibreGL({
    style: 'https://tiles.openfreemap.org/styles/liberty',
  }).addTo(map)
</script>
```

## OpenLayers

Use `ol-mapbox-style` to attach an OpenFreeMap style to an OpenLayers map.

```html
<script src="https://unpkg.com/ol/dist/ol.js"></script>
<link rel="stylesheet" href="https://unpkg.com/ol/ol.css" />
<script src="https://unpkg.com/ol-mapbox-style/dist/olms.js"></script>
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const openfreemap = new ol.layer.Group()
  const map = new ol.Map({
    layers: [openfreemap],
    view: new ol.View({ center: ol.proj.fromLonLat([13.388, 52.517]), zoom: 9.5 }),
    target: 'map',
  })
  olms.apply(openfreemap, 'https://tiles.openfreemap.org/styles/liberty')
</script>
```

## Mobile apps

Mobile clients can use the same style URLs through MapLibre Native.

## Custom styles

When a user wants to edit colors, labels, POI visibility, or other style details, point them at Maputnik and remind them to host the edited JSON themselves.

Useful starting points:

- `https://maputnik.github.io/editor?style=https://tiles.openfreemap.org/styles/bright`
- `https://maputnik.github.io/editor?style=https://tiles.openfreemap.org/styles/liberty`
- `https://maputnik.github.io/editor?style=https://tiles.openfreemap.org/styles/positron`

## Attribution reminder

The public site uses the attribution string:

```html
<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>
```

If a client does not show MapLibre's default attribution controls, the app must still display the required attribution.

## When to trouble-shoot here

Symptoms that belong here rather than in server-ops troubleshooting:

- style URL returns 404 or a blank map
- CORS or attribution issues in the client
- a project still uses Mapbox GL JS 2.x+
- custom styles work in Maputnik but not in the app
- the user needs a quick-start snippet for a specific map library

For self-hosting or server-side problems, switch to the deployment or HTTP-host sub-skill.
