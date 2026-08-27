# pyproj CLI reference

## Entry points and top-level parser

The packaged console script is `pyproj`, mapped to `pyproj.__main__:main`.
The equivalent module invocation is `python -m pyproj`. The parser exposes:

```text
pyproj [-h] [-v] {sync} ...
```

`-h`/`--help` prints usage and exits. With no command, the output includes the
installed pyproj and PROJ versions, `-v/--verbose`, and the `sync` command.
`-v`/`--verbose` calls `pyproj.show_versions()` and prints pyproj, runtime and
compiled PROJ versions, selected data directory, user data directory, PROJ
and EPSG/ESRI/IGNF database metadata, Python/system information, and relevant
Python dependency versions. It does not print the normal help.

The package also exposes `pyproj.show_versions()` for the same diagnostic from
Python. Use the bundled read-only diagnostic when output must be machine
checked without the extra system executable field.

## `sync` parser and selection rules

`pyproj sync` is a grid-manifest query plus optional download operation. Its
help text is available with `pyproj sync --help`. A command with no selection
among `--bbox`, `--list-files`, `--all`, `--source-id`, `--area-of-use`, and
`--file` prints sync help instead of acting.

| Option | Input and behavior |
|---|---|
| `--bbox W,S,E,N` | Four comma-separated decimal degrees. West/east are normally in `[-180,180]`; an east value below west represents an antimeridian crossing. Bad arity or non-numeric text raises a parser-to-runtime error, so validate before invoking. |
| `--spatial-test intersects\|contains` | How a resource extent is compared with the bbox; default is `intersects`. |
| `--source-id TEXT` | Substring filter against the GeoJSON feature `source_id`. |
| `--area-of-use TEXT` | Substring filter against the feature `area_of_use`. |
| `--file TEXT` | Substring filter against the grid filename (`name`). |
| `--exclude-world-coverage` | Remove global-extent resources from bbox results. |
| `--include-already-downloaded` | Include resources already present in the selected PROJ/user data paths. Without it, existing names are filtered out. |
| `--list-files` | Print `filename | source_id | area_of_use` rows and do not download selected grid files. Manifest retrieval can still write/fetch `files.geojson` if it is absent or older than one day. |
| `--all` | Select all missing transform grids. It cannot be combined with `--list-files`, `--source-id`, `--area-of-use`, `--bbox`, or `--file`. |
| `--target-directory DIR` | Use `DIR` for the manifest and grid files. It cannot be combined with `--system-directory`; the directory must be usable by the process. |
| `--system-directory` | Use the main PROJ data directory rather than the user-writable directory. Treat this as an explicit privileged/system write decision. |
| `-v`/`--verbose` | Print one `Downloading: URL` line per grid download. |

The default download target is `pyproj.datadir.get_user_data_dir(True)`, which
may create the user PROJ directory. Use `--list-files` with a pre-existing,
controlled target when an operation must be observational. If no target is
specified, do not assume that the user directory is empty or writable.

Examples:

```bash
# Read parser help; no grid operation is selected.
python -m pyproj --help
python -m pyproj sync --help

# Inspect a filtered manifest; review output before allowing a download.
python -m pyproj sync --file us_noaa_alaska --list-files \
  --include-already-downloaded
python -m pyproj sync --bbox 2,49,3,50 --exclude-world-coverage --list-files

# Explicitly request a filtered download only after preflight approval.
python -m pyproj sync --file us_noaa_alaska \
  --target-directory /chosen/proj-data --verbose
```

The last example is intentionally not a wrapper: the caller owns directory
creation, network permission, disk budget, and review of the selected file.

## Validation signals

A successful help check contains `-v, --verbose` and `sync`. A list check starts
with exactly:

```text
filename | source_id | area_of_use
----------------------------------
```

A successful verbose report contains `pyproj:`, `PROJ (runtime):`,
`PROJ (compiled):`, `data dir`, `user_data_dir`, `System`, and `Python deps`.
A download with verbose mode reports its URL; absence of that line means no
selected file was downloaded, not necessarily that no manifest was accessed.
