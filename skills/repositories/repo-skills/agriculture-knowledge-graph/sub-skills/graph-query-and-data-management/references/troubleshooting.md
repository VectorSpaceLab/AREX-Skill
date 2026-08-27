# Graph Query and Data Management Troubleshooting

Use this page for failures specific to Neo4j imports, graph query semantics,
CSV schemas, hierarchy files, and vector utilities.

## Neo4j import issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Couldn't load the external resource` or file URL errors | CSV is not in Neo4j's configured import directory, or the file name in Cypher was not adapted. | Copy or symlink the CSV into the configured import directory, then use `file:///name.csv` style URLs. Do not use machine-local absolute paths in reusable templates. |
| JVM heap or transaction memory errors during Hudong import | Large `hudong_pedia*.csv` files and long detail fields. | Import in batches, use `USING PERIODIC COMMIT` on older Neo4j, increase heap temporarily, or pre-trim columns for a task-specific graph. |
| Uniqueness constraint fails | Duplicate or blank `title` values across Hudong files or repeated imports with `CREATE`. | Deduplicate first, switch node imports to `MERGE`, and check titles before creating/enforcing constraints. |
| Attribute import creates fewer edges than rows | Endpoint titles in `attributes.csv` do not match any loaded `HudongItem` or `NewNode`. | Count unmatched `Entity` and `Attribute` values before import; load missing `NewNode` rows or accept that unmatched rows are skipped by `MATCH`. |
| Weather relation import has no rows | Missing `Weather` nodes or plant/city titles were not loaded as graph nodes. | Import `static_weather_list.csv` first; verify `weather_plant.csv.Plant` and `city_weather.csv.city` titles exist in loaded nodes. |
| City-weather import is slow | The source pattern matches `(city {title: ...})` without a label, so indexes may not be used. | If the data is known to use a label, run label-specific imports; otherwise create per-label title indexes or split by known labels. |

## Query and relation-search issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Entity detail search is empty after import | The detail view uses `HudongItem`; importing into `Item` or another label will not match. | Confirm nodes are labeled `HudongItem` and have the exact `title` property. |
| Exact relation search misses valid `NewNode` triples | The historical code checks `answer is None`; `py2neo` returns `[]` on no rows, so later label-combination fallbacks may not run. | Replace fallback logic with `if not rows` or use a single cross-label `MATCH`/`UNION` query. |
| Weather edges appear in direct searches but not shortest paths | Direct searches match any relationship label, while shortest path uses only `:RELATION*`. | Broaden the path query intentionally if weather edges should participate. Document the changed semantics. |
| Relation search with `relation` input returns nothing | Relationship `type` comparison is exact. The UI lowercases input, but stored values can be Chinese or case-sensitive strings. | Inspect stored `rel.type` values, normalize consistently, or avoid lowercasing for non-Wikidata relation classes. |
| Sorted result order looks surprising | Results are sorted by `relationStaticResult.txt` counts; missing relations get count `0`. | Regenerate or bypass the frequency file if ranking by relation prevalence is not desired. |
| Cypher errors on titles with quotes | Historical wrapper concatenates strings into Cypher. | Use parameterized queries for any new or user-facing code. |

## CSV and encoding issues

- Read CSVs with a real CSV parser and UTF-8 handling; details and values are
  long and can contain punctuation.
- Preserve the exact header names. `new_node.csv` uses `lable`, but the graph
  import only needs `title`.
- Do not split `openTypeList`, `baseInfoKeyList`, or `baseInfoValueList` on
  commas; split those serialized list fields on `##`.
- Empty base-info lists are valid and should not block node import.

## Hierarchy tree issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_path` returns `[]` for an existing entity | Entity is not listed as a leaf under any category reachable from root `农业`. | Check `leaf_list.txt` for the entity and `micropedia_tree.txt` for a complete category path from `农业`. |
| Loader raises index errors | A line has fewer than two space-separated tokens. | Validate edge/leaf files before loading; remove blank or malformed lines. |
| Results differ across calls with `unique=True` | Source behavior shuffles candidate paths before overlap pruning. | Use `unique=False` for exhaustive deterministic debugging, or set a random seed in a controlled wrapper. |
| Generated UI contains unsafe text | Source HTML concatenates category names directly. | Escape text when serving untrusted data in a modernized web app. |

## Vector utility issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` in `get_simi_top` | Requested word is missing from the loaded vector dictionary. | Check the vector file before calling, or return a fallback when the word is absent. |
| Similar-word results are not reproducible | The source randomly skips about 70% of candidates. | Use a deterministic full scan for evaluation tasks; reserve the source helper for demo tag clouds. |
| `cos_simi` returns `None` | One vector has zero norm. | Filter zero vectors or return a configured minimum similarity. |
| Slow preload or memory pressure | Vector file can be large and is loaded fully into a dictionary. | Use a reduced-dimensional file, memory-map a modern format, or avoid vector preload for graph-only tasks. |

## Service boundary reminders

- Do not start or debug the Django server from this sub-skill; route that to
  `../web-app-service/`.
- Do not rerun network crawlers or Wikidata processors from this sub-skill;
  route acquisition/regeneration questions to `../crawlers-and-wikidata-pipelines/`.
- Do not treat PCNN relation extraction as graph import; route it to
  `../relation-extraction-pipeline/`.
