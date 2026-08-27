# CLI reference

## Entry point and help

`setup.py` installs exactly one console script for this surface:

```text
nuplan_cli = nuplan.cli.nuplan_cli:main
```

Use these commands without opening a database:

```bash
nuplan_cli --help
nuplan_cli db --help
nuplan_cli db info --help
nuplan_cli db duration --help
nuplan_cli db log-duration --help
nuplan_cli db log-vehicle --help
nuplan_cli db scenarios --help
```

The inspected installation exposes Typer's completion options at the top level
and a single `db` sub-group. Help rendering is independent of dataset
availability. Do not run a query with the default path just to answer a syntax
question: query execution enters `_ensure_file_downloaded`, which delegates to
the package data helper and may attempt to obtain an absent path.

## Common argument shape

All five DB commands have the same signature shape:

```text
nuplan_cli db <command> [OPTIONS] [DB_VERSION]
```

- `DB_VERSION`: optional positional database path. In code this is the
  `db_version: str` argument and defaults to a mini-split path below the data
  root. Prefer an explicit existing local `.db` path for deterministic use.
- `--data-root TEXT`: root used by the package's
  `download_file_if_necessary` helper. The code default is the value of
  `NUPLAN_DATA_ROOT`, or the package's documented fallback dataset root when
  that variable is absent. Pass an explicit root for deterministic use.
- `--help`: show command help and exit without querying the DB.

The default DB expression is built at import time from
`NUPLAN_DATA_ROOT` and points at the mini split's sample log. A changed
`NUPLAN_DATA_ROOT` after the CLI process starts does not retroactively rewrite
that default; pass `DB_VERSION` explicitly when this matters.

## `db info`

```bash
nuplan_cli db info path/to/log.db
nuplan_cli db info path/to/log.db --data-root /path/to/data
```

This calls `get_db_description(log_file)` and prints every SQLite table,
row count, and column. Column output includes data type, `NULL`/`NOT NULL`,
and `PRIMARY KEY`. Tables come from `sqlite_schema` and are ordered by table
name in the query layer. This is schema inspection, not a general SQL shell.

## `db duration`

```bash
nuplan_cli db duration path/to/log.db
```

This calls `get_db_duration_in_us(log_file)`, computes seconds from
microseconds, and prints:

```text
DB duration is HH:MM:SS [HH:MM:SS]
```

The query is `MAX(timestamp) - MIN(timestamp)` over `lidar_pc`. It therefore
requires a usable `lidar_pc` table and reports whole clock-style hours,
minutes, and seconds. It is not a wall-clock query and does not print the raw
microsecond value.

## `db log-duration`

```bash
nuplan_cli db log-duration path/to/log.db
```

The query groups lidar timestamps by `log.logfile` through `scene`, sorts by
log name, and prints one line per log followed by a count:

```text
The duration of log <logfile> is HH:MM:SS [HH:MM:SS]
There are <N> total logs.
```

An empty result is a valid query result and ends with `There are 0 total logs.`
A schema or join failure is not the same as an empty result.

## `db log-vehicle`

```bash
nuplan_cli db log-vehicle path/to/log.db
```

The query reads `logfile` and `vehicle_name` from `log`, ordered by logfile.
Output is:

```text
For the log <logfile>, vehicle <vehicle_name> was used.
```

## `db scenarios`

```bash
nuplan_cli db scenarios path/to/log.db
```

The query groups `scenario_tag.type`, orders by descending count, and prints:

```text
<tag>: <count> scenarios.
TOTAL: <sum> scenarios.
```

This reports tags, not necessarily unique scenario records: a scenario can
carry more than one tag depending on the database contents.

## Query API signatures

The installed package exposes these query functions:

```python
get_db_description(log_file: str) -> DbDescription
get_db_duration_in_us(log_file: str) -> int
get_db_log_duration(log_file: str) -> Generator[Tuple[str, int], None, None]
get_db_log_vehicles(log_file: str) -> Generator[Tuple[str, str], None, None]
get_db_scenario_info(log_file: str) -> Generator[Tuple[str, int], None, None]
```

They take a database file argument, not a data-root argument. The CLI resolves
(or attempts to resolve) the file first, then passes the resulting path to the
query function.

## Deterministic command pattern

For a local-only inspection, make the file existence decision outside the CLI
and pass the same root explicitly. Use paths supplied by the caller; the
example deliberately contains no machine-specific default:

```bash
DB=<existing-local-database-file>
if [ ! -f "$DB" ]; then
  printf 'missing local DB: %s\n' "$DB" >&2
  exit 2
fi
nuplan_cli db info "$DB" --data-root "<data-root>"
```

This shell guard is an example only; it prevents the CLI's missing-file helper
from becoming an implicit download path. Use a real data root appropriate to
the machine, and do not put credentials or remote URLs in a manifest.

## Scope boundary

Use the `data-and-maps` route for DB schema details, sensor blobs, map roots,
scenario builders, and dataset layout. Use the `simulation-and-evaluation`
route for planner/simulation commands. This route only records the CLI's
command surface and the safe decision about when to execute it.
