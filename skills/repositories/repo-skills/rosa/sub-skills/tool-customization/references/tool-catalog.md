# Deterministic ROSA tool catalog

The catalog below is based on the source implementations and the installed
schemas. Inputs are JSON-schema arrays/strings/integers even where Python
annotations use tuples or `List`; validate the exact tool schema before
sending calls. These tools calculate, inspect bounded text, or change process
logging state. They do not discover ROS entities; use the ROS 1/ROS 2 sibling
routes for middleware tools.

## Calculation, geometry, and statistics

### Aggregation and arithmetic

| Tool(s) | Input | Result and caveats |
|---|---|---|
| `add_all` | `numbers: list[number]` | Numeric sum; empty list returns `0`. |
| `multiply_all` | `numbers: list[number]` | Numeric product; empty list returns `1` (the initialized product). |
| `mean` | `numbers: list[number]` | Dict `{"mean": ..., "stdev": ...}` using Python's sample standard deviation. Empty input raises `statistics.StatisticsError`; one value also cannot produce sample stdev. |
| `median` | `numbers: list[number]` | Python median; empty input raises `StatisticsError`. |
| `mode` | `numbers: list[number]` | Python `statistics.mode`; empty input raises `StatisticsError`. For a tie, preserve Python's version-specific first-mode behavior rather than claiming a list of all modes. |
| `variance` | `numbers: list[number]` | Python sample variance; fewer than two values raises `StatisticsError`. |
| `add`, `subtract`, `multiply` | `xy_pairs: list[array]` of `(x, y)` | List of one-key dicts such as `{"1+2": 3}`. Each pair must unpack into two values. |
| `divide` | `xy_pairs` | Same shape; division by zero returns the string `"undefined"`, not an exception/result number. |
| `exponentiate` | `xy_pairs` | Same shape with `x ** y`; extreme/invalid numeric values can still raise Python errors. |
| `modulo` | `xy_pairs` | Same shape; modulo by zero returns `"undefined"`. |

The schemas intentionally do not express pair length or numeric units. Preserve
units in the caller's values and state them in the surrounding plan; these
functions do not convert metres, degrees, seconds, or other physical units.

### Trigonometry and angle units

`sin`/`cos`/`tan` are exposed as `sine`, `cosine`, and `tangent`; they accept
`x_values: list[number]` and return a list of one-key dicts. Input angles are
in **radians**; the sine/cosine/tangent results are dimensionless numeric
values. `asin`, `acos`, and `atan` use the same list shape and return angles in
radians. `asin` and `acos` catch an out-of-domain `ValueError` and return
`"undefined"` for that element. `tangent` may become very large near a pole;
no robotics safety bound is supplied.

`atan2(pairs: list[array])` consumes pairs in `(y, x)` order and returns
radians. Do not silently send `(x, y)` order. For a point A to point B, pass
`(y2-y1, x2-x1)` as the pair.

`degrees_to_radians(degrees: list[number])` returns a dictionary keyed by each
input degree with values in radians. `radians_to_degrees(radians: list[number])`
returns the inverse mapping in degrees. Inputs are numeric angles; these tools
do not normalize wraparound or validate a robot's frame convention.

Hyperbolic tools `sinh`, `cosh`, and `tanh` accept radians-like numeric values
and return one-key dict lists. They are mathematical functions, not motion
commands. Large inputs can overflow or otherwise raise a Python math error.

### Geometry

- `sqrt(x_values)` returns one-key dicts. Negative values produce the exact
  string `"undefined (negative number)"`.
- `distance_between_points(point_pairs)` consumes
  `[((x1, y1), (x2, y2)), ...]` and returns Euclidean distances. The output
  distance has the same implied unit as the coordinates; it does not know
  whether coordinates are metres, pixels, or simulation units.
- `calculate_line_angle_and_distance(point_pairs)` uses the same point-pair
  shape and returns, per line, a nested object with `angle_radians`,
  `angle_degrees`, and `distance`. The angle is relative to positive x, and
  distance retains the input coordinate unit. It is a planning result, not an
  authorization to execute movement.

Malformed arrays, nonnumeric values, and wrong nesting are schema/validation or
Python errors; they are not converted to a safe robot command. Use these tools
for precision-sensitive geometry instead of doing the arithmetic manually.

### Counting

- `count_list(items: list)` returns the number of list items.
- `count_words(text: str)` returns `len(text.split())`; whitespace-separated
  words only, with an empty string returning `0`.
- `count_lines(text: str)` returns `len(text.split("\\n"))`; an empty string
  therefore counts as **one** line under this implementation.

## Log reader

`read_log` has the installed schema:

```text
read_log(
  log_file_directory: str,
  log_filename: str,
  level_filter: "ERROR" | "INFO" | "DEBUG" | "WARNING" | "CRITICAL" |
                "FATAL" | "TRACE" | None = None,
  num_lines: int | None = None,
) -> dict
```

Behavior is deterministic but filesystem-dependent:

1. `num_lines < 1` returns
   `{"error": "Invalid `num_lines` argument. It must be a positive integer."}`.
2. A missing directory returns an error telling the caller to discover the
   correct directory first.
3. A missing file returns an error; an existing non-file path returns an
   error.
4. The file is read, every line is stripped and prefixed with its one-based
   original line number (`line N: ...`). If `num_lines` is set, only the most
   recent N lines are retained before the size guard and level filter.
5. If the retained list is still over 200 lines, the tool returns an error
   asking for a smaller `num_lines` subset. A request with no limit on a large
   file therefore fails rather than returning an unbounded payload.
6. `level_filter` is a case-insensitive substring filter applied after the
   recent-line selection. It can return an empty `lines` list.

A successful result includes `log_filename`, `log_file_directory`,
`level_filter`, `requested_num_lines`, `total_lines`, `lines_returned`, and
`lines`. The implementation reads the complete file before slicing, so a
custom adaptation should add an independent byte/encoding/allowlisted-path
policy if logs may be large or untrusted. Never invent a log path: discover it
through the applicable ROS route, and do not expose secrets found in log
contents.

## Verbosity, debugging, and wait

| Tool | Input | Effect |
|---|---|---|
| `set_verbosity` | `enable_verbose_messages: bool` | Sets module `VERBOSE` and calls LangChain `set_verbose`; returns `Verbose messages are now enabled/disabled.` |
| `set_debugging` | `enable_debug_messages: bool` | Sets module `DEBUG` and calls LangChain `set_debug`; returns `Debug messages are now enabled/disabled.` |
| `wait` | `seconds: int` | Calls `time.sleep(seconds)` and returns `Waited exactly {elapsed} seconds.` The schema says integer; negative values fail in `sleep`, and there is no upper bound. |

Debug and verbose are process/global LangChain state, not isolated per ROSA
instance. They can change output for other agents in the same process. Enable
them only for bounded diagnosis and restore the prior state when a host
application requires isolation. Treat `wait` as a blocking tool: cap or reject
long waits in a custom wrapper and never use it to hide an action timeout.
