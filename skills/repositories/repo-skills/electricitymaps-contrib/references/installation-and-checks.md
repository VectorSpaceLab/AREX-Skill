# Installation and Checks

## When to read

Read this when setting up a checkout, choosing focused validation commands, or
diagnosing missing CLI/dependency errors before using a sub-skill.

## Recommended setup

The repo is a uv workspace with the main distribution `electricitymap-contrib`
and the workspace member `electricitymap-contrib-types` under `libs/types`.
Parser work needs the `parsers` optional extra; test/lint work needs the `dev`
dependency group.

```bash
uv sync --extra parsers --group dev
```

If your uv version includes the dev group by default, `uv sync --extra parsers`
may be enough, but adding `--group dev` makes test dependencies explicit.

### Pip fallback

Use pip only when uv is unavailable. The repo's `dev` dependencies are a
PEP-style dependency group, not a pip extra, so `.[dev]` is not valid.

```bash
python -m pip install -e libs/types
python -m pip install -e ".[parsers]"
python -m pip install "pytest>=9,<10" "syrupy>=5,<6" \
  "requests-mock>=1.12,<2" "testfixtures>=7.0.0,<8" \
  "click>=8,<9" "ruff==0.15.4"
```

Install the `scripts` dependency group or `xmltodict` only if a user explicitly
asks to run the legacy ENTSO-E capacity script; it is not needed for the normal
`capacity_update` workflow.

## Console entry points

`pyproject.toml` exposes these repo commands:

| Command | Purpose | Typical owner |
| --- | --- | --- |
| `uv run test-parser ZONE [DATA_TYPE]` or `uv run test_parser ...` | Execute a live parser smoke check. Defaults to production, or exchange when the zone contains `->`. | `parsers` |
| `uv run capacity_update --zone ZONE --target_datetime YYYY-MM-DD` | Mutate capacity config for one zone through a capacity parser. | `capacity` |
| `uv run capacity_update --source SOURCE --target_datetime YYYY-MM-DD` | Mutate capacity config for all zones in a capacity source group. | `capacity` |
| `uv run format` | Run Ruff auto-fix and formatter. | root/configuration |
| `uv run lint` | Run Ruff checks. | root |
| `uv run test` | Run the full pytest suite. | root |
| `uv run check` | Run format check, lint, and tests. | root |

Use the bundled scripts in this skill when you need safer inspection modes from
an arbitrary current working directory:

```bash
python scripts/check_environment.py --repo-root <checkout>
python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> --list
python sub-skills/capacity/scripts/capacity_update.py --repo-root <checkout> --list-sources
python sub-skills/configuration/scripts/validate_config_filenames.py --repo-root <checkout>
```

## Focused native checks by workflow

Run focused checks after modifying the corresponding area. Prefer these before
`uv run test` unless the user asks for full-suite confidence.

### Parser changes

```bash
uv run pytest tests/test_parser_interface.py -q
uv run pytest electricitymap/contrib/parsers/tests/test_<PARSER>.py -q
```

Representative high-signal parser tests include ENTSOE, FR, EIA, ESIOS,
OPENNEM, and US_ERCOT because they exercise token handling, mocked HTTP,
XML/JSON/CSV parsing, exchange direction, and snapshots.

### Capacity changes

```bash
uv run pytest tests/test_capacity.py tests/test_update_capacity_configuration.py -q
uv run pytest electricitymap/contrib/capacity_parsers/tests/test_ONS.py \
  electricitymap/contrib/capacity_parsers/tests/test_OPENELECTRICITY.py -q
```

### Configuration changes

```bash
uv run pytest tests/config/test_config_model.py tests/config/test_config_zones.py -q
uv run pytest tests/test_zones_json.py tests/test_exchanges_json.py -q
uv run pytest tests/config/test_data_center_model.py tests/config/test_emission_factors.py \
  tests/test_co2eq_parameters.py -q
```

Use `uv run format` after YAML/JSON/Python edits when the diff is understood.
For capacity updates, remember that the repo CLI runs `npx --yes prettier@2` on
`config/zones`; missing Node/npm can fail after the Python update has already
changed files.

## Import-path diagnostic

Some config model code lazily imports live parser functions through top-level
names such as `parsers.FR.fetch_production`. If a normal package install cannot
resolve those names, run repo commands through uv from the checkout or use the
bundled scripts with `--repo-root`; they add both the checkout root and the
`electricitymap/contrib` source root for diagnostics without hard-coding any
local path.
