# Longest6 And Result Analysis

## Benchmark Contract

Longest6 contains 36 routes with an average route length of about 1.5 km,
compared with roughly 1.7 km for the official leaderboard routes. The combined
route file covers Town01 through Town06, with six routes in each town.

Every route has one unique weather/daylight pair. The complete 6 by 6 product
appears exactly once:

- Weather: `Cloudy`, `Wet`, `MidRain`, `WetCloudy`, `HardRain`, `SoftRain`.
- Daylight: `Night`, `Twilight`, `Dawn`, `Morning`, `Noon`, `Sunset`.

The local evaluator attempts dense traffic by requesting 500 background
vehicles when `DATAGEN=0`. Use the local evaluator to preserve this and the
no-stop-penalty scoring change.

## Combined And Split Routes

Use the combined route set for a complete benchmark. Its expected checkpoint
total is:

```text
36 routes × REPETITIONS
```

The benchmark also has 36 one-route XML files named conceptually
`longest_weathers_0.xml` through `longest_weathers_35.xml`. Use a split file to
isolate one route, shorten a diagnostic run, or distribute routes across
workers. Its expected checkpoint total is:

```text
1 route × REPETITIONS
```

Keep the same scenario annotation JSON for combined and split runs. Do not
concatenate partial result JSON files unless each record maps back to a route id
in the XML supplied to the parser.

The command builder chooses the bundled repository layout from
`--route-set longest6` or `--route-set split --route-index N`; it checks that the
selected XML and scenario JSON exist but never starts evaluation.

## Inspect Before Aggregating

Run:

```bash
python scripts/inspect_result_json.py /path/to/result.json
```

Add `--records` for a compact per-route table or `--format json` for a
machine-readable report. Add `--strict` only when every route must be completed
successfully; Longest6 result sets containing valid blocked routes will then be
rejected.

A repository fixture demonstrates an important distinction: it has progress
`36/36`, 23 `Completed` records, 13 `Failed - Agent got blocked` records,
`eligible: true`, and `entry_status: Finished with agent errors`. Its published
global values start with driving score `74.487`, route completion `82.710`, and
penalty `0.894`. A complete checkpoint can therefore contain unsuccessful
routes and still be structurally eligible.

## Parse Results

The parser is a safe, standard-library adaptation of the repository analysis
utility. It reads JSON/XML, writes a CSV, and can write SVG map overlays; it does
not import CARLA.

```bash
python scripts/parse_results.py \
  --xml /path/to/longest6.xml \
  --results /path/to/result-directory \
  --save-dir /path/to/parsed
```

`--results` accepts one or more JSON files or directories. Directory discovery
is recursive and deterministic. The parser refuses to overwrite existing
outputs unless `--overwrite` is explicit.

### CSV contents

`results.csv` contains:

1. Weighted global label/value rows. Scores come from each JSON's `labels` and
   `values`; infraction labels are replaced by rates recomputed from records.
2. Mean and population-standard-deviation tables grouped by route, town,
   weather, daylight, and route status.
3. Per-event infraction coordinates extracted from descriptions that contain
   `(x=..., y=..., z=...)`.

Driven distance is computed per route as:

```text
(score_route / 100) × (route_length_m / 1000)
```

Collision, red-light, stop, route-deviation, timeout, and blocked metrics are
event counts divided by aggregate driven kilometres. `outside_route_lanes` is
converted from described metres off route to kilometres, divided by driven
kilometres, then multiplied by 100 to express a percentage. A malformed
off-route description aborts rather than silently producing a wrong metric.

Grouped infraction columns are raw event-count means and standard deviations,
matching the intent of the repository parser; the global summary rows are the
per-kilometre rates.

### Optional map output

Provide the six town-map PNGs to generate self-contained SVG overlays without
NumPy, Matplotlib, or CARLA:

```bash
python scripts/parse_results.py \
  --xml /path/to/longest6.xml \
  --results /path/to/results \
  --save-dir /path/to/parsed \
  --town-maps /path/to/town_maps_xodr
```

For each town represented in the records, the parser writes `TownNN.svg` with
the PNG embedded and coloured cross marks for located infractions. It also
writes `legend.svg`. Missing map images, malformed PNG headers, unknown town
geometry, or out-of-bounds coordinates are reported. Map rendering is optional;
CSV analysis remains CPU-only and dependency-free.

## Coverage And Repetition Checks

The safe parser is stricter than the original in one important way. It verifies
not only that record count is a multiple of XML route count, but also that every
XML route id appears the same number of times. This detects a duplicated route
that masks a missing route.

For a combined XML, 36 one-record split JSON files are acceptable if the route
ids cover all 36 routes exactly once. For a split XML, result records must map
to that one XML id. Mixing route files from another benchmark is rejected.

## Failure Policy

Choose `--failure-policy` deliberately:

- `source` (default): aborts on the exact statuses rejected by the repository
  parser: `Failed`, `Failed - Agent couldn't be set up`, and
  `Failed - Simulation crashed`. A blocked route remains analyzable.
- `strict`: requires every route status to be `Completed`.
- `allow`: does not reject route status text, but still enforces JSON schema,
  nonzero driven distance, XML coverage, and metric validity.

Unlike the original utility's bare `exit()`, every parser abort returns a
nonzero exit code. A route with effectively zero completion produces a warning;
if aggregate driven distance is zero, parsing aborts because per-kilometre
metrics are undefined.

Read [result-schema.md](result-schema.md) for field meanings and
[troubleshooting.md](troubleshooting.md) for rejected inputs.
