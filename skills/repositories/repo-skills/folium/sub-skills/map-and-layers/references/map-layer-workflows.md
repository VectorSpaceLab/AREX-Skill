# Map and layer workflows

These recipes stay inside Folium's own render contract and avoid original repo paths.

## 1) A simple interactive map

```python
import folium

m = folium.Map(location=[45.5236, -122.6750], zoom_start=12)
folium.Marker([45.5236, -122.6750], tooltip="Portland").add_to(m)
m.save("map.html")
```

Use this when you only need a single map with one or two points.

## 2) Base tiles and custom tile URLs

```python
m = folium.Map(location=[45, -122], tiles="CartoDB Positron", zoom_start=10)
folium.TileLayer(
    tiles="https://{s}.tiles.example.com/{z}/{x}/{y}.png",
    attr="My tile attribution",
    name="Custom tiles",
).add_to(m)
```

Rules of thumb:

- built-in xyzservices names are the easiest path
- custom tile URLs need an explicit `attr`
- use `tiles=None` when you want a map without a base layer
- `no_wrap` changes world wrapping behavior on the tile layer

## 3) Group layers and control visibility

```python
m = folium.Map(location=[0, 0], zoom_start=2)
fg = folium.FeatureGroup(name="Points")
folium.Marker([0, 0], popup="Center").add_to(fg)
fg.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)
```

Use `FeatureGroup` or `LayerGroup` when the user wants to toggle a whole set of items together.

Add `LayerControl` last so it sees the finished layer list.

## 4) Draw vectors and shapes

```python
route = [[45.52, -122.68], [45.55, -122.67], [45.58, -122.64]]
folium.PolyLine(route, color="purple", weight=4).add_to(m)
folium.Rectangle([[45.50, -122.72], [45.60, -122.60]], color="green", fill=False).add_to(m)
folium.Circle([45.53, -122.66], radius=200, color="red", fill=True).add_to(m)
```

Use these for local geometry that does not need GeoJSON binding.

## 5) Raster overlays

```python
image = [[0, 1], [1, 0]]
folium.raster_layers.ImageOverlay(
    image=image,
    bounds=[[45.50, -122.72], [45.60, -122.60]],
    colormap=lambda x: (1, 0, 0, x),
).add_to(m)
```

For `ImageOverlay`, remember:

- the bounds must match the image projection you intend
- `mercator_project=True` helps when the source image is in geographic space
- `origin="lower"` changes how array rows map to latitude

Use `VideoOverlay` for browser-side video URLs; the HTML output only serializes the player.

## 6) Custom panes and z-order

```python
folium.map.CustomPane("labels", z_index=650).add_to(m)
folium.TileLayer("CartoDB Positron", pane="labels").add_to(m)
```

Use a custom pane when a layer must sit above or below others consistently.

## 7) Flask embedding and iframe/component output

A Folium map can be embedded in a Flask app or extracted into HTML components. Use the bundled Flask example script when you want a runnable reference.

Typical patterns:

- return the rendered map HTML directly for the simplest app integration
- render the map in an iframe when you want to preserve existing page layout
- extract header/body/script parts when you need to place them into a larger template

## 8) Notebook display and PNG export

- `_repr_html_()` is the standard notebook display path.
- `_repr_png_()` only works when the map has `png_enabled=True` and the environment can do browser-driven screenshot capture.
- `show_in_browser()` writes a temporary HTML file and opens it in the default browser.

For PNG snapshots, treat Selenium/browser-driver setup as a prerequisite, not as an optional runtime fix.

## 9) JS/CSS resource overrides

Folium can add custom JS or CSS resources to the map through the `JSCSSMixin` APIs. Use that when a map or plugin needs a specific browser asset version or a private asset mirror.

Keep browser-side assets minimal and well documented so future agents can debug CDN or CSP failures quickly.
