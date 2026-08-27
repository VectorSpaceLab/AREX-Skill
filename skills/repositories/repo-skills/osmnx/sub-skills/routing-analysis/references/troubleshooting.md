# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `scikit-learn must be installed as an optional dependency to search an unprojected graph.` | `nearest_nodes` was called on an unprojected graph without the neighbors extra. | Install the routing nearest-neighbor extras, or project the graph first and retry. |
| `scipy must be installed as an optional dependency to search a projected graph.` | `nearest_nodes` was called on a projected graph without SciPy. | Install the neighbors extra, or temporarily work in unprojected space if that is acceptable. |
| `Graph must be unprojected to add edge bearings.` | `add_edge_bearings` was called after projection. | Keep the graph in lat/lon while adding bearings, then project only if a downstream task needs it. |
| `scipy must be installed as an optional dependency to calculate entropy.` | `orientation_entropy` was called without SciPy. | Install the entropy extra before running the bearing analysis. |
| `This graph's edges have no preexisting 'maxspeed' attribute values so you must pass hwy_speeds or fallback arguments.` | `add_edge_speeds` had no usable speed data to impute from. | Pass `hwy_speeds`, `fallback`, or add `maxspeed` attributes first. |
| `All edges must have 'length' and 'speed_kph' attributes.` | `add_edge_travel_times` ran before length or speed preparation. | Run `add_edge_lengths` and `add_edge_speeds` first, then retry. |
| `Edge 'length' and 'speed_kph' values must be non-null.` | Some edges still have missing weights. | Fill the missing values or rebuild the graph with complete attributes. |
| `Weight contains non-numeric values.` | The routing weight names an attribute that is text or mixed type. | Use a numeric edge attribute such as `length`, `travel_time`, or `speed_kph`. |
| `orig` and `dest` iterable mismatch | One side of a batch shortest-path call was scalar and the other was a list, or the lengths differ. | Make both sides lists/arrays of equal length before calling `shortest_path`. |
| `Cannot solve path from ...` or a `None` route in a batch result | The graph is disconnected for that OD pair, or the chosen weight makes the path impossible. | Recheck connectivity, confirm the weight exists, or choose another routing weight. |
| Route GeoFrame looks out of order or missing expected edges | A node path was not passed to `route_to_gdf`, or the weight used to select parallel edges did not match routing. | Pass the node sequence from `shortest_path` and reuse the same weight. |
| `street_count`-based stats look wrong | The graph was edited after `street_count` was computed, or the attribute was never set. | Recompute street counts with `count_streets_per_node` and update node attributes before stats. |
| Distances or nearest results look wrong | `X`/`Y` order is reversed, or the graph and query coordinates are in different CRSs. | Remember `X=longitude/easting`, `Y=latitude/northing`, and keep both inputs in the same CRS. |

## Recovery pattern

1. Check whether the graph is projected or unprojected.
2. Confirm that the required edge attributes already exist and are numeric.
3. Re-run `add_edge_lengths`, `add_edge_speeds`, or `add_edge_bearings` as needed.
4. Retry the route, nearest-match, or orientation call with matching CRS and weight names.
5. Use the smoke script to confirm the repair on a tiny local graph.
