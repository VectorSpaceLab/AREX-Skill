# Troubleshooting Crawler and Pipeline Failures

Use this reference for workflow-specific failures before escalating to graph import, Django service, NER/classification, or relation-extraction training routes.

## Scrapy cannot find the project settings

Symptoms:

- `Scrapy 2.x - no active project`
- `ModuleNotFoundError` for a project package
- outputs written to an unexpected directory

Recovery:

1. Confirm the working directory in [crawler-workflows.md](crawler-workflows.md).
2. For projects with `scrapy.cfg`, run from the directory containing that file.
3. For the Wikidata property crawler package, set `SCRAPY_SETTINGS_MODULE=wikidataCrawler.settings` from a directory where the package is importable if no `scrapy.cfg` is present.
4. Check pipeline output paths; most source pipelines open plain relative filenames.

## Missing crawler input files

Common missing inputs:

| Missing file | Likely workflow | Recovery |
| --- | --- | --- |
| `crawled_leaf_list.txt` | Hudong spider | Build or copy it from the DFS tree workflow, or use an approved tiny list for a bounded crawl. |
| `treenode_list.txt` | Leaf crawler | Run or restore the DFS category crawl output. |
| `entities.json` | Wikidata relation preprocessing | Run the entity search crawler or restore the generated artifact. |
| `readytoCrawl.json` | Wikidata relation crawler | Run `preProcess.py` from the expected Wikidata relation directory. |
| `weather_corpus.json` | Weather-to-plant extraction | Run the approved weather page crawler or restore existing weather corpus data. |

If the source code references an absolute developer-machine path for predicted labels, edit a working copy to use a relative input file supplied by the user. Do not recreate that absolute path.

## Live crawl fails or returns empty pages

Likely causes:

- target site markup changed;
- robots policy or anti-bot blocking;
- obsolete `allowed_domains` values that include a scheme;
- high concurrency or missing user agent;
- network timeout or redirect handling.

Recovery:

1. Stop broad crawling after repeated failures; do not keep retrying indefinitely.
2. Re-run only a tiny approved URL/entity fixture to inspect HTML/API shape.
3. Lower concurrency and add delays/autothrottle before any resumed broad crawl.
4. Verify selectors against the current response and update a working copy, not the generated skill tree.
5. If the task only needs existing CSVs, skip recrawl and validate the artifacts instead.

## `relationDataProcessing.py` produces empty or wrong CSVs

Symptoms:

- `wikidata_relation.csv` only has a header.
- Many expected existing entities become `NewNode` rows.
- Neo4j connection errors occur before any CSV rows are written.

Likely causes and fixes:

- The Hudong graph was not imported before conversion; load or point to the intended graph before rerunning.
- The script has hard-coded Neo4j connection details; replace them in a local working copy.
- `entityRelation.json` is not in the expected relative location.
- Title normalization differs between Hudong CSVs and Wikidata labels; inspect a few `entity1`/`entity2` values before broad conversion.

Use `validate_relation_csvs.py` after conversion to catch schema errors without connecting to Neo4j.

## CSV rows break Neo4j import later

Symptoms:

- `LOAD CSV` reports too many columns.
- A relation row appears shifted across columns.
- Quotes or commas appear inside relation/entity fields.

Recovery:

1. Run the bundled validator on all five key CSVs.
2. Treat embedded commas, quotes, carriage returns, and newlines as warnings that need human review for this repository's import style.
3. Regenerate with proper CSV quoting or with the source-compatible sanitizer before import.
4. Preserve the source-compatible `new_node.csv` header `title,lable` unless the graph import route is also updated.

## Weather-to-plant rows are missing

Likely causes:

- `weather_corpus.json` is missing or empty.
- `weather2weather.txt` alias mappings do not cover the climate names.
- THULAC/NER resources are unavailable.
- Neo4j is unavailable or lacks plant-kingdom relations used by the plant check.
- Candidate plant terms are filtered because predicted labels do not mark them as plant entities.

Recovery:

1. Validate `city_weather.csv` and `static_weather_list.csv` first.
2. Inspect one weather page corpus item and one expected plant term manually.
3. Confirm NER and graph services only if the user requested service-backed regeneration.
4. Do not mark this workflow verified from a CSV-only check; CSV validation proves structure, not NER/Neo4j recall.

## Attribute extraction emits few or no rows

Likely causes:

- The Hudong CSV column order does not match `title,url,image,openTypeList,detail,baseInfoKeyList,baseInfoValueList`.
- `baseInfoKeyList` and `baseInfoValueList` lengths differ after splitting on `##`.
- The known-entity set from new nodes and predicted labels is incomplete.
- Basic-info values are free text rather than graph node titles.

Recovery:

- Check several source rows before broad extraction.
- Keep only entity-like attribute values for graph relations.
- Validate the final `attributes.csv` header and non-empty fields before handing off to the graph import route.
