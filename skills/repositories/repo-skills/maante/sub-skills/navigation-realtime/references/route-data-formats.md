# Route Data Formats

## Purpose

Use this reference when creating, validating, or adapting MaaNTE local route JSON or teleport/check-point JSON data.

## Multi-Route Segment Format

This is the main online-map export shape:

```json
{
  "version": 1,
  "routes": [
    {
      "id": "route-1",
      "name": "main",
      "segments": [
        {
          "id": "segment-1",
          "name": "1",
          "points": [
            {"lat": 51.9, "lng": -36.0},
            {"lat": 51.8, "lng": -29.0}
          ]
        }
      ]
    }
  ]
}
```

`route_name` matches route `name` or `id`. `segment_index` is 1-based for task-facing parameters.

## Simple Point Formats

The route parser also supports a simple list or object:

```json
[
  {"pixelX": 1000, "pixelY": 2000},
  {"pixelX": 1200, "pixelY": 2300}
]
```

```json
{
  "points": [
    {"x": -152876.62, "y": 129507.04},
    {"target_x": 4310, "target_y": 5980}
  ]
}
```

Supported point fields:

| Fields | Meaning |
| --- | --- |
| `pixelX`, `pixelY` | Pixel coordinates. Optional `sourceWidth`/`sourceHeight` or `sourceSize` can rescale them. |
| `target_x`, `target_y` | Pixel-coordinate aliases. |
| `lat`, `lng` | Online-map world coordinates; converted through online map constants to current map pixels. |
| `x`, `y`, optional `z` | Raw game world coordinates; converted through the coordinate calibration transform. |

## Online Coordinate Conversion

MaaNTE's route model uses online-map constants:

- Online map size: 22528×22528.
- Online world origin pixel: 11264, 11264.
- Online pixels per world unit: 44.
- Runtime map size commonly 11264×11264.

The parser scales online-map points into the target map size.

## Teleport Points

Teleport records normally live under a resource `map_teleport` JSON file:

```json
{
  "version": 1,
  "teleport_points": [
    {
      "id": "fountain",
      "name": "喷泉传送点",
      "areaName": "绘空",
      "iconIndex": 2,
      "selectionName": "推荐地点",
      "iconPath": "image/map_teleport/teleport_icon/phone_booth.png",
      "description": "地图索引中使用的传送点"
    }
  ]
}
```

## Check Points

The teleport-required check can load named points from a `points` collection. Records may expose `worldX/worldY`, `rawX/rawY`, `pixelX/pixelY`, `x/y`, or nested `coordinate: {x, y}`. A `threshold` value controls when the point counts as near.

## Validation

Use the bundled route validator for route files:

```bash
python sub-skills/navigation-realtime/scripts/validate_route_json.py routes/my-route.json
```

It checks JSON shape and accepted point fields without needing the original repo or a game window.
