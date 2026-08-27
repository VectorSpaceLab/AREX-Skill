# Routes And Scenarios

## Scope and source contract

TransFuser's training metadata covers eight public CARLA maps:
`Town01`, `Town02`, `Town03`, `Town04`, `Town05`, `Town06`, `Town07`, and
`Town10HD`. Training-data generation covers `Scenario1`, `Scenario3`,
`Scenario4`, `Scenario7`, `Scenario8`, `Scenario9`, and `Scenario10`.
Structural validation also accepts `Scenario2`, `Scenario5`, and `Scenario6`
because they occur in the checked-in Longest6 evaluation annotations. The
checked-in metadata under `leaderboard/data/training/` is the safest starting
point for a collection run. The generator source is CARLA-bound and is
distilled here rather than copied.

The checked-in collection is uneven by design: some town/scenario files contain
no routes, and Scenario10's checked-in files include towns not represented by
its route XML. Validate the specific pair you intend to use rather than
assuming a complete Cartesian product.

## Scenario JSON

A generated scenario file has this shape:

```json
{
  "available_scenarios": [
    {"Town03": [
      {"scenario_type": "Scenario8",
       "available_event_configurations": [
         {"transform": {"x": 1.0, "y": 2.0, "z": 0.0,
                        "yaw": 90.0, "pitch": 0.0},
          "other_actors": null}
       ]}
    ]}
  ]
}
```

`available_scenarios` is a list of town-keyed objects. Each town maps to a
list of scenario entries. Each entry has `scenario_type` and an
`available_event_configurations` list. Each event normally has a `transform`
with numeric `x`, `y`, `z`, `yaw`, and `pitch`. `other_actors` is not uniform
across the repository: it is absent for Scenario1/3, `{}` for Scenario4, and
usually `null` for Scenario7/8/9/10. Preserve the value; do not normalize it
into a guessed actor configuration.

Scenario generation obtains a CARLA map and writes one JSON file per town and
scenario. Scenario1 and 3 scan non-junction road topology and select curved
sections; Scenario4 samples driving traversals through junctions. Scenarios
7/8/9 classify signalized-junction traversal angles; Scenario10 selects
unsignalized junctions. These classifications depend on the CARLA map and
world actors and cannot be reproduced by a CPU-only JSON validator.

## Route XML

A route file is an XML document with a `<routes>` root and one or more
`<route id="..." town="Town..">` elements:

```xml
<routes>
  <route id="0" town="Town03">
    <waypoint x="-88.7" y="-124.9" z="0.0"
              pitch="0.0" roll="0.0" yaw="89.84"/>
    <waypoint x="-85.0" y="-74.9" z="-0.8"
              pitch="0.0" roll="0.0" yaw="89.84"/>
  </route>
</routes>
```

Every route requires a nonempty string `id` and supported `town`; every
waypoint requires numeric `x`, `y`, `z`, `pitch`, `roll`, and `yaw`. The
training route generators commonly write two endpoints for scenario routes
and three keypoints for lane-change routes. Longest6 files contain many
intermediate waypoints and one nested `<weather .../>` element per route.
A parser should allow extra route attributes and a weather child, but must
reject a route with no waypoints or nonnumeric coordinates.

Route ids need not be globally unique across files, and generated Scenario7/8/9
files in this snapshot can have non-contiguous ids. Uniqueness is required
within one XML file; contiguity is not. Town in the XML must agree with the
intended CARLA world and with the town named by the paired scenario file.

## Route length and lane changes

The generator source uses one-metre interpolation in its route planner after
coarse keypoints are chosen. The distance constraints in source code are
expressed in interpolated waypoint counts, not a direct XML length field:

- Curved Scenario1/3 routes use roughly 380 m candidate sections, discard very
  short routes, and keep paths that have a meaningful bend. The repository
  documentation reports about 400 m average and places the scenario near the
  middle.
- Junction routes (Scenario4/7/8/9/10) use about 30 m before and after a
  junction, with roughly 100 m average reported in the dataset documentation.
  Scenario matching and turn subtype checks decide whether a traversal is
  usable.
- Lane-change generation walks a non-junction segment with approximately 10 m
  waypoint spacing, creates changes near the midpoint and endpoint, and limits
  the final sampling to at most 50 routes per direction class in the source
  implementation. The direction classes are `lr`, `ll`, `rr`, and `rl`:
  first letter is the initial lateral direction and second is the later one.
  A three-waypoint route is the start, midpoint lane, and endpoint lane.

Do not infer exact physical length from a two-point XML file without loading the
CARLA map and interpolating it. `MAX_LEN`/pruning in the source is a safety
filter on the map-derived trajectory, not a field persisted into XML.

## Scenario-to-route compatibility

The intended generation order is:

1. Generate JSON annotations for each selected town/scenario.
2. Generate XML routes from those annotations and the same town map.
3. Scan/interpolate the route to ensure its trigger can instantiate the
   scenario, including the route-dependent turn subtype for Scenario4 and
   Scenario7/8/9.
4. Validate the pair using the bundled CPU checker.

The source matcher uses a position threshold of about 2 m and yaw threshold of
about 10 degrees. A route may be structurally valid but contain no matching
scenario trigger. A scenario/town mismatch, wrong `ScenarioN` directory, or a
route generated from a different map version is a hard compatibility warning.

## Visualization

The source `vis_points.py` reads an XML or JSON file and uses CARLA-derived map
assets plus pygame to draw route/trigger points. The reusable safe validator
only checks the input schema. For an actual image, prepare the CARLA map image
cache and run the source-equivalent visualization command externally; do not
claim visualization passed from schema parsing. Useful visual checks are:

- XML: different colors per route, arrows from each waypoint, and town map
  matching the route's `town` attribute.
- JSON: trigger points and yaw arrows grouped by scenario type.
- Lane changes: confirm the midpoint and endpoint lateral direction agree with
  the filename class (`lr`, `ll`, `rr`, `rl`).

## Longest6 distinction

Longest6 is evaluation metadata, not training collection metadata. Its
`longest6.xml` contains 36 routes, six each in Town01–Town06, with one weather
child per route. The complete weather/daylight product is six weather labels
(`Cloudy`, `Wet`, `MidRain`, `WetCloudy`, `HardRain`, `SoftRain`) crossed with
six daytimes (`Night`, `Twilight`, `Dawn`, `Morning`, `Noon`, `Sunset`). Use
`carla-evaluation` for benchmark execution; this sub-skill only validates the
route XML and scenario JSON structure.
