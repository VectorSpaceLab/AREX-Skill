# GeoJSON and choropleth workflows

These recipes stay inside Folium's rendering contract and avoid upstream GIS preprocessing.

## 1) Plain GeoJson with style and bounds

```python
import folium

m = folium.Map(location=[0, 0], zoom_start=2, tiles="cartodbpositron")

geojson = folium.GeoJson(
    data,
    name="regions",
    style_function=lambda feature: {
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.4,
        "fillColor": "#8dd3c7",
    },
    highlight_function=lambda feature: {
        "weight": 3,
        "fillOpacity": 0.7,
    },
    zoom_on_click=True,
)

geojson.add_to(m)
m.fit_bounds(geojson.get_bounds())
```

Use this pattern when the data already carry useful properties and you just need a rendered layer.

## 2) Loop-safe style functions

```python
for style in styles:
    style_function = lambda feature, style=style: style
    folium.GeoJson(item, style_function=style_function).add_to(m)
```

Capture the loop value in a default argument. That avoids late-binding closure bugs.

## 3) Tooltip, popup, and `JsCode`

```python
from folium.utilities import JsCode

tooltip = folium.GeoJsonTooltip(
    fields=["name", "value"],
    aliases=["Name", "Value"],
    labels=True,
    localize=True,
    class_name="foliumtooltip",
)

popup = folium.GeoJsonPopup(
    fields=["name", "value"],
    aliases=["Name", "Value"],
    labels=True,
    localize=True,
    class_name="foliumpopup",
)

on_each = JsCode("""
function(feature, layer) {
    layer.on({
        click: function() {
            console.log(feature.properties.name);
        }
    });
}
""")

folium.GeoJson(
    data,
    tooltip=tooltip,
    popup=popup,
    on_each_feature=on_each,
    popup_keep_highlighted=True,
).add_to(m)
```

Use `JsCode` when the Python-side style callback is not enough.

## 4) Choropleth from table data

```python
choropleth = folium.Choropleth(
    geo_data=geojson_data,
    data=df,
    columns=["id", "value"],
    key_on="feature.id",
    bins=[0, 10, 20, 30, 40],
    fill_color="YlGn",
    legend_name="Value",
    nan_fill_color="lightgray",
    nan_fill_opacity=0.3,
    highlight=True,
)
choropleth.add_to(m)
```

Use this when the map geometry and the numeric measure live in different tables.

Validation steps:

- confirm the key column is unique in the table
- confirm the join key resolves in the GeoJSON
- verify the bins cover the value range
- inspect the legend caption and missing-value style

## 5) TopoJSON

```python
folium.TopoJson(
    topojson_data,
    object_path="objects.counties",
    style_function=lambda feature: {"color": "#444", "weight": 1},
).add_to(m)

folium.Choropleth(
    geo_data=topojson_data,
    topojson="objects.counties",
    data=df,
    columns=["id", "value"],
    key_on="feature.id",
).add_to(m)
```

Keep the object path explicit and stable.

## 6) Point features and click helpers

```python
folium.GeoJson(
    point_features,
    marker=folium.CircleMarker(radius=5, color="black", fill=True),
    style_function=lambda feature: {"fillColor": "orange"},
).add_to(m)

folium.ClickForMarker().add_to(m)
folium.ClickForLatLng().add_to(m)
```

`ClickForMarker` drops a draggable marker at the clicked map point. `ClickForLatLng` copies the clicked coordinates and is handy for diagnosing swapped coordinate order.

## 7) Safe render checks

For each layer, verify at least one of these after rendering:

- `get_bounds()` returns finite bounds
- the HTML contains the expected field names or layer names
- the color scale appears when a choropleth uses bound data
- point features render at the expected location
