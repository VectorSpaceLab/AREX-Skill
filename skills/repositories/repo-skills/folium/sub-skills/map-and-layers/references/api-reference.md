# Verified API reference

These signatures were checked against the installed Folium package used to build this skill. Use them as a quick accuracy check when writing map and layer workflows.

## Map and render shell

| Object | Verified signature | Notes |
| --- | --- | --- |
| `folium.Map` | `(location: Optional[collections.abc.Sequence[float]] = None, width: Union[str, float] = '100%', height: Union[str, float] = '100%', left: Union[str, float] = '0%', top: Union[str, float] = '0%', position: str = 'relative', tiles: Union[str, folium.raster_layers.TileLayer, NoneType] = 'OpenStreetMap', attr: Optional[str] = None, min_zoom: Optional[int] = None, max_zoom: Optional[int] = None, zoom_start: int = 10, min_lat: float = -90, max_lat: float = 90, min_lon: float = -180, max_lon: float = 180, max_bounds: bool = False, crs: str = 'EPSG3857', control_scale: bool = False, prefer_canvas: bool = False, no_touch: bool = False, disable_3d: bool = False, png_enabled: bool = False, zoom_control: Union[bool, str] = True, font_size: str = '1rem', **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Root object for interactive map HTML. |
| `folium.Figure` | `(width: str = '100%', height: Optional[str] = None, ratio: str = '60%', title: Optional[str] = None, figsize: Optional[Tuple[int, int]] = None)` | Container for one or more rendered elements. |

## Common render methods

- `_repr_html_()` returns notebook HTML.
- `_repr_png_()` returns `None` unless `png_enabled=True`.
- `_to_png(delay=3, driver=None, size=None)` uses Selenium and a browser driver for screenshot capture.
- `show_in_browser()` writes a temporary HTML file and opens it in the default browser.

## UI and layer classes

| Object | Verified signature | Notes |
| --- | --- | --- |
| `folium.Marker` | `(location: Optional[collections.abc.Sequence[float]] = None, popup: Union[ForwardRef('Popup'), str, NoneType] = None, tooltip: Union[ForwardRef('Tooltip'), str, NoneType] = None, icon: Union[folium.map.Icon, ForwardRef('CustomIcon'), ForwardRef('DivIcon'), NoneType] = None, draggable: bool = False, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Simple stock Leaflet marker. |
| `folium.Popup` | `(html: Union[str, branca.element.Element, NoneType] = None, parse_html: bool = False, max_width: Union[str, int] = '100%', show: bool = False, sticky: bool = False, lazy: bool = False, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Popup wrapper for map layers. |
| `folium.Tooltip` | `(text: str, style: Optional[str] = None, sticky: bool = True, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Hover label wrapper. |
| `folium.Icon` | `(color: str = 'blue', icon_color: str = 'white', icon: str = 'info-sign', angle: int = 0, prefix: str = 'glyphicon', **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Standard marker icon. |
| `folium.DivIcon` | `(html: Optional[str] = None, icon_size: Optional[tuple[int, int]] = None, icon_anchor: Optional[tuple[int, int]] = None, popup_anchor: Optional[tuple[int, int]] = None, class_name: str = 'empty')` | Lightweight HTML-based marker icon. |
| `folium.CustomIcon` | `(icon_image: Any, icon_size: Optional[tuple[int, int]] = None, icon_anchor: Optional[tuple[int, int]] = None, shadow_image: Any = None, shadow_size: Optional[tuple[int, int]] = None, shadow_anchor: Optional[tuple[int, int]] = None, popup_anchor: Optional[tuple[int, int]] = None)` | Image-based marker icon. |
| `folium.FeatureGroup` | `(name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Toggleable group of map children. |
| `folium.LayerGroup` | `(name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Leaflet layer group with custom options. |
| `folium.LayerControl` | `(position: str = 'topright', collapsed: bool = True, autoZIndex: bool = True, draggable: bool = False, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Toggle base/overlay layers. Add it last. |
| `folium.map.CustomPane` | `(name: str, z_index: Union[int, str] = 625, pointer_events: bool = False)` | Custom z-order pane for map elements. |
| `folium.FitBounds` | `(bounds: collections.abc.Sequence[collections.abc.Sequence[float]], padding_top_left: Optional[collections.abc.Sequence[float]] = None, padding_bottom_right: Optional[collections.abc.Sequence[float]] = None, padding: Optional[collections.abc.Sequence[float]] = None, max_zoom: Optional[int] = None)` | Fit the map to a bounding box. |
| `folium.FitOverlays` | `(padding: int = 0, max_zoom: Optional[int] = None, fly: bool = False, fit_on_map_load: bool = True)` | Fit to all enabled overlays. |
| `folium.LatLngPopup` | `()` | Click helper that shows coordinates. |
| `folium.ClickForLatLng` | `(format_str: Optional[str] = None, alert: bool = True)` | Click helper that formats or alerts the clicked coordinates. |
| `folium.ClickForMarker` | `(popup: Union[branca.element.IFrame, branca.element.Html, str, NoneType] = None)` | Click helper that drops a marker. |
| `folium.Control` | `(control: Optional[str] = None, *args, position: Optional[Literal['bottomright', 'bottomleft', 'topright', 'topleft']] = None, **kwargs)` | Base control class used by many UI controls. |
| `folium.utilities.JsCode` | `(js_code: Union[str, ForwardRef('JsCode')])` | JavaScript literal wrapper for callbacks and overrides. |

## Tile and overlay classes

| Object | Verified signature | Notes |
| --- | --- | --- |
| `folium.TileLayer` | `(tiles: Union[str, xyzservices.lib.TileProvider] = 'OpenStreetMap', min_zoom: Optional[int] = None, max_zoom: Optional[int] = None, max_native_zoom: Optional[int] = None, attr: Optional[str] = None, detect_retina: bool = False, name: Optional[str] = None, overlay: bool = False, control: bool = True, show: bool = True, no_wrap: bool = False, subdomains: str = 'abc', tms: bool = False, opacity: float = 1, **kwargs)` | Custom or built-in tile layer. Custom URLs need `attr`. |
| `folium.WmsTileLayer` | `(url: str, layers: str, styles: str = '', fmt: str = 'image/jpeg', transparent: bool = False, version: str = '1.1.1', attr: str = '', name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs)` | Browser-side WMS layer. |
| `folium.raster_layers.ImageOverlay` | `(image: Any, bounds: collections.abc.Sequence[collections.abc.Sequence[float]], origin: str = 'upper', colormap: Optional[Callable] = None, mercator_project: bool = False, pixelated: bool = True, name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs)` | Image over a geographic bounding box. |
| `folium.raster_layers.VideoOverlay` | `(video_url: str, bounds: collections.abc.Sequence[collections.abc.Sequence[float]], autoplay: bool = True, loop: bool = True, name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs: Union[str, float, bool, collections.abc.Sequence, dict, NoneType])` | Browser video overlay. |
| `folium.PolyLine` | `(locations, popup=None, tooltip=None, **kwargs)` | Polyline path overlay. |
| `folium.Polygon` | `(locations: Union[collections.abc.Iterable[collections.abc.Sequence[float]], collections.abc.Iterable[collections.abc.Iterable[collections.abc.Sequence[float]]]], popup: Union[folium.map.Popup, str, NoneType] = None, tooltip: Union[folium.map.Tooltip, str, NoneType] = None, **kwargs: Union[bool, str, float, NoneType])` | Polygon or multipolygon path overlay. |
| `folium.Rectangle` | `(bounds: collections.abc.Iterable[collections.abc.Sequence[float]], popup: Union[folium.map.Popup, str, NoneType] = None, tooltip: Union[folium.map.Tooltip, str, NoneType] = None, **kwargs: Union[bool, str, float, NoneType])` | Rectangle path overlay. |
| `folium.Circle` | `(location: Optional[collections.abc.Sequence[float]] = None, radius: float = 50, popup: Union[folium.map.Popup, str, NoneType] = None, tooltip: Union[folium.map.Tooltip, str, NoneType] = None, **kwargs: Union[bool, str, float, NoneType])` | Circle overlay in meters. |
| `folium.CircleMarker` | `(location: Optional[collections.abc.Sequence[float]] = None, radius: float = 10, popup: Union[folium.map.Popup, str, NoneType] = None, tooltip: Union[folium.map.Tooltip, str, NoneType] = None, **kwargs: Union[bool, str, float, NoneType])` | Circle overlay in pixels. |
| `folium.ColorLine` | `(positions: collections.abc.Iterable[collections.abc.Sequence[float]], colors: collections.abc.Iterable[float], colormap: Union[branca.colormap.ColorMap, collections.abc.Sequence[Any], NoneType] = None, nb_steps: int = 12, weight: Optional[int] = None, opacity: Optional[float] = None, **kwargs: Any)` | Line with color gradient. |

## Practical notes

- `LayerControl` should be attached after the layers it manages.
- `FeatureGroup` and `LayerGroup` help future agents toggle related overlays together.
- `CustomPane` is the tool to reach for when layer z-order matters more than data shape.
- Use `JsCode` when the API expects browser JavaScript instead of Python callables.
- The exact browser behavior of `ImageOverlay`, `VideoOverlay`, and `show_in_browser()` depends on the client environment, not just Python serialization.
