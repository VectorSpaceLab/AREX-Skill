# Capacity Troubleshooting

## CLI and registry errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Either zone or source must be set` | Capacity update command was called without a target. | Provide exactly one of `--zone ZONE` or `--source SOURCE`. |
| `Zone and source cannot be both set` | Mutually exclusive scopes were combined. | Split into separate runs; prefer the smaller zone-specific run when possible. |
| `target_datetime must be specified` | The updater needs the date from which capacity is valid. | Pass an ISO date such as `--target-datetime 2023-01-01`. |
| `No capacity parser developed for ZONE` | The zone has no `productionCapacity` parser registered. | Inspect source mappings with `scripts/capacity_update.py --list-sources`. Add a capacity parser and zone config mapping, or perform a manual config update with review. |
| `No capacity parser developed for SOURCE` | The source group is not in the current `productionCapacity` registry. | Use `--list-sources` to see valid groups. Check spelling/case: EIA, EMBER, ENTSOE, IRENA, ONS, OPENNEM, REE, etc. |

## Data and aggregate errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No capacity data for ZONE in DATE` | Source parser returned no data for that zone/date. | Check source coverage, target date, token/network response, and parser-specific tests. Do not write empty values as if they were zero. |
| Aggregate update says all capacity configs must have the same type | Parent subzones mix legacy scalar, dict, and list capacity shapes. | Normalize subzones to compatible timeline lists before aggregating, or document why a manual parent update is required. |
| Aggregate warning says not all capacities are available for a datetime | Some subzones lack a value for the target date. | Choose a date where every subzone has data or update missing subzone entries first. |
| New values duplicate previous entries | Timeline helper may intentionally skip or deduplicate redundant points. | Compare the generated list with [data-formats.md](data-formats.md); this is expected when value/date would add no new information. |
| Parent capacity looks wrong after subzone update | `--update-aggregate` may have summed incompatible modes or stale subzone config. | Re-run helper tests, inspect each subzone mode and date, and avoid manual parent edits until inputs are consistent. |

## Token, network, and formatting issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `EIA_KEY`, `ENTSOE_TOKEN`, `EMBER_CAPACITY_KEY`, `OPENELECTRICITY_TOKEN`, or `FINGRID_TOKEN` | Live capacity parser needs source credentials. | Use mocked native tests if credentials are unavailable. For live runs, set only the needed token and keep it out of diffs/logs. |
| HTTP/API errors from a source group | Source outage, schema change, token issue, or date not available. | Narrow to one zone and target date, add/adjust a mocked capacity parser test, and do not bulk-write partial data. |
| `npx`/prettier failure after update | Formatting step needs Node/npm or network/cache access. | Inspect the Python-generated diff first. Then run the repo prettier command once Node/npm is available, or leave a clear formatting blocker. |
| EMBER all-years update would replace entire capacity sections | The legacy bulk script intentionally overwrites `capacity` with EMBER data. | Do not run it by default. Ask for explicit approval and narrow to a zone when possible. |
| Legacy ENTSO-E capacity script asks for `xmltodict` or CSV/token details | It is a separate maintainer path, not the generic capacity_update flow. | Use the generic capacity parser workflow unless the user specifically requests the legacy script. Install the scripts dependency only then. |

## Verification after a fix

- Pure capacity lookup/merge change: `uv run pytest tests/test_capacity.py tests/test_update_capacity_configuration.py -q`.
- Source-specific parser change: add that parser's capacity test module.
- Zone YAML changes from capacity update: also run configuration model checks.
- Bulk source update: sample affected zones and document source/date/trend
  rationale before broad tests.
