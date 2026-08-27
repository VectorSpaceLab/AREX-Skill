# Maps, routes, traffic, and missions

## Map/engine compatibility matrix

| Map source | Default map class | Traffic engine guidance | Availability note |
|---|---|---|---|
| `.net.xml` SUMO network | SUMO road network | `SUMO` | Requires SUMO Python/runtime integration for actual SUMO use. |
| `.xodr` OpenDRIVE | OpenDRIVE road network | `SMARTS` | Requires the optional OpenDRIVE parser/geometry stack. |
| Waymo Scenario TFRecord | Waymo map | `SMARTS` or dataset replay path | Requires Waymo package and local Scenario-proto data. |
| Argoverse map archive | Argoverse map | `SMARTS` or dataset replay path | Requires optional Argoverse/data stack; unverified here. |
| custom source | user `RoadMap` | normally `SMARTS` | `builder_fn` must be importable and return a road map/hash. |

The default map builder identifies a file by extension or conventional filename.
An unknown extension is not a custom map automatically: provide `builder_fn`.
OpenDRIVE does not support `shift_to_origin` in this release. Do not pair
`Traffic(engine="SUMO")` with OpenDRIVE, Waymo, Argoverse, or arbitrary custom
maps and expect the route generator to repair it. A map may load while traffic
artifacts still fail later because the engine-specific route generator is not
available.

## Route tuple contract

```text
(road_id: str, lane_index: int, offset: number | "random" | "max")
```

`lane_index` is indexed from the rightmost lane in the SMARTS types. The route
is `Route(begin=..., end=..., via=(road_id, ...))`; `via` contains road IDs the
resolved route must include. `RandomRoute` is a distinct descriptor and is not a
placeholder string. `map_spec` can be attached to a route to override the
scenario's default map specification.

Use offsets carefully:

- numeric offsets are meters along the lane;
- `"random"` asks the generator for a valid random offset;
- `"max"` means the far end after resolving lane length;
- `"base"` is accepted in some zone contexts, but do not use it as a Route
  offset unless the installed generator explicitly supports it.

Verify edge IDs and lane indexes against the chosen map. A route beginning and
ending on disconnected roads may fail in route resolution; `via` can constrain
routing but cannot create missing connections.

## Flows and trips

A `Flow` has a route, a vehicle/hour `rate`, a start/end time in seconds, an
actor-to-weight mapping, and `randomly_spaced`/`repeat_route` flags. `Traffic`
contains a sequence of flows, optional one-shot `Trip`s, and `engine`. A `Trip`
has a unique `vehicle_name`, route, departure second, vehicle type, and optional
actor model. Keep traffic group keys stable because they become generated
artifact names; `missions` is reserved by lower-level generation and should not
be used as a traffic group key.

The generated route file is not a complete semantic test. Common authoring
errors include zero/negative route lengths, actors on unsupported vehicle types,
flow end shorter than an intended episode, rates interpreted as seconds instead
of hours, and multiple actors/trips placed at one start coordinate.

## Mission and entry contract

`Mission` describes a route to complete. `EndlessMission` describes a start and
never-ending route. `TrapEntryTactic` and `IdEntryTactic` can delay or control
entry. A map-relative trap zone's edge must match the mission's start edge;
generation validates this particular relation. `Via` points contain a road id,
lane index, lane offset, required speed, and optional hit distance.

Scenario Studio intentionally does not prove that an ego mission start is clear
of background traffic or social routes. If the same edge/lane/offset/time is
used, the vehicle can collide immediately and terminate the episode. Stagger
lanes/offsets/departure times or remove the overlapping route and rerun a
bounded validation.

## Social actors and bubbles

A social actor's locator is a Python import reference, usually
`package.module:registered-name`. It is not a filesystem path. A social mission
is grouped as `group: ([actors], [missions])`; names must be unique across groups.
Bubbles capture eligible traffic for the social actor in a fixed or map-relative
zone. A traveling bubble follows one actor/vehicle with an explicit offset.
Conditions are validated for geometry and broadphase requirements, but route
occupancy and policy behavior remain runtime concerns.

## History and metadata boundaries

`TrafficHistoryDataset` imports trajectories from NGSIM, INTERACTION, Waymo, or
Argoverse according to the `source_type` and input format. It may be mixed with
ordinary `Traffic`; map coordinates, scaling, heading inference, `flip_y`,
`swap_xy`, and off-map filtering must be checked against the dataset. A dataset
placeholder without `input_path` is skipped by generation.

Friction patches are timed zones with a friction coefficient. Metadata contains
actor-interest filtering/color, difficulty, duration, and arbitrary descriptive
fields. Metadata is not a substitute for simulation configuration.
