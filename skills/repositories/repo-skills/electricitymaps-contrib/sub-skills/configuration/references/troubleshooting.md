# Configuration Troubleshooting

## Filename and key failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ERROR: <file> is not uppercase` | Zone or exchange filename contains lowercase letters. | Rename to uppercase and rerun the bundled filename validator. |
| `ERROR: <exchange> is not sorted` | Exchange filename parts are not lexicographically sorted. | Rename `B_A.yaml` to `A_B.yaml`; loaded keys still use `A->B`. |
| Exchange test says a zone is missing | Exchange references a zone key not present in `config/zones`. | Add the missing zone config, correct the exchange filename, or remove obsolete exchange config. |
| Geo test says a zone in `world.geojson` is missing from zones | Geometry references a zone without a config file. | Add/restore the zone YAML or update geometry if the zone was intentionally removed. |

## Pydantic/model validation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `extra fields not permitted` | YAML/JSON contains a key not declared by the config model. | Check spelling and aliases such as `subZoneNames`, `bypassedSubZones`, `_source`, `_url`, and `_comment`. Add model support only if the new field is intentional. |
| Invalid `currency` | Zone currency is not a valid ISO 4217 code. | Correct the currency or omit it when not needed. |
| Parser model field mismatch | `ParserDataType` enum and `Parsers`/`ExchangeParsers` model fields diverged. | Update enum, pydantic model, registry tests, and parser interface tests together. |
| `get_function()` import failure while validating model | Parser mapping resolves to a module/function that cannot be imported. | Use parser sub-skill diagnostics; check `MODULE.function`, parser dependencies, and top-level `parsers` path handling. |
| Data-center model failure | Required data-center fields, zone references, or uniqueness constraints are violated. | Validate the JSON shape and run the data-center model test after a minimal edit. |

## Source and emission-factor failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Emission-factor test reports missing required source | A co2eq estimate references a source not listed under the zone's `sources` and not in the known global allowlist. | Add the source link to the zone `sources` map or use a global reference exactly as accepted by tests. |
| Power-origin ratios do not sum to approximately one | Fallback mix values violate the model root validator. | Normalize values so the total is within tolerance; avoid silently dropping unknown/other modes. |
| Direct/lifecycle mismatch | Edit was made in the wrong co2eq section or only one basis was updated. | Check both direct and lifecycle models and rerun co2eq tests. |

## Aggregate and destructive workflow failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Aggregate helper skips capacity modes | Subzone capacity values are missing, nonnumeric for the target date, or structured timelines require capacity-specific handling. | Use the capacity sub-skill to normalize/update timelines; rerun aggregate helper with an explicit `--target-datetime`. |
| Aggregate helper output loses comments | The bundled helper generates YAML and does not preserve source comments. | Treat dry-run output as a draft; manually merge comments if they matter before `--write`. |
| Zone removal leaves references behind | Removal is broad: zone YAML, parent `subZoneNames`, exchange files, parser archive, geo, tests, docs. | Do not run destructive removal without explicit approval. Search for the zone key and validate every config/parser test group after cleanup. |
| Bulk zone-name synchronization rewrites many files | The source utility updates many zone YAMLs from JSON. | Use only for explicit bulk synchronization tasks and require a diff review. |

## Validation sequence after recovery

1. Rerun the bundled filename validator.
2. Run the focused model/zone/exchange/data-center/emission-factor tests that
   match the changed files.
3. If parser mappings changed, also run parser interface tests.
4. If capacity fields changed, also run capacity merge/lookup tests.
5. Only then run `uv run format`, `uv run lint`, or `uv run check` for broader
   confidence.
