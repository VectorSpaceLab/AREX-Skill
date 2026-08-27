# Wikidata Processing and Relation CSVs

This reference covers conversion and analysis after Wikidata triples have already been crawled. It intentionally stops before final Neo4j import; import order, constraints, and graph queries belong to graph-query-and-data-management.

## Relation conversion workflow

The conversion script reads line-delimited `entityRelation.json` triples and writes three CSVs:

| Output | Header | Meaning |
| --- | --- | --- |
| `new_node.csv` | `title,lable` | Entities found from Wikidata that are not already Hudong graph nodes. The second column is misspelled `lable` in source output and normally has value `newNode`. |
| `wikidata_relation.csv` | `HudongItem1,relation,HudongItem2` | Relations where both ends already exist as `HudongItem` nodes. |
| `wikidata_relation2.csv` | `HudongItem,relation,NewNode` | Relations from an existing `HudongItem` to a newly discovered node. |

Source behavior to preserve or account for:

- Run the conversion from `wikidataSpider/wikidataProcessing/` if using the original script layout.
- The script expects `../wikidataRelation/entityRelation.json`.
- It connects to Neo4j to decide whether `entity1` and `entity2` already exist as `HudongItem` nodes. Without a loaded graph, the conversion cannot reproduce the original split between `wikidata_relation.csv` and `wikidata_relation2.csv`.
- It removes commas and double quotes from relation names and `entity2` values before writing CSV, then converts `entity2` to simplified Chinese.
- It writes raw comma-separated rows rather than using a quoting CSV writer, so later validation should flag embedded commas, quotes, and newlines before import.
- The script contains hard-coded Neo4j connection settings; replace them in a local working copy before running against a user service.

## Safe validation before import

Use the bundled script when the user asks whether generated CSVs are structurally safe:

```bash
python scripts/validate_relation_csvs.py --root path/to/csv-export-directory
python scripts/validate_relation_csvs.py --root path/to/csv-export-directory --json
python scripts/validate_relation_csvs.py --self-test
```

The script expects these five files in the same `--root` directory unless individual paths are supplied:

- `wikidata_relation.csv`
- `wikidata_relation2.csv`
- `new_node.csv`
- `weather_plant.csv`
- `city_weather.csv`

If the Wikidata and weather CSVs are stored in separate directories, pass per-file overrides shown by `--help` rather than copying large files into the skill tree.

## Relation CSV invariants

Before handing CSVs to the graph import route, check at least:

| File | Required checks |
| --- | --- |
| `wikidata_relation.csv` | Header exactly identifies two Hudong endpoints and one relation; all fields are non-empty; each row has exactly three columns; duplicate triples are understood before import. |
| `wikidata_relation2.csv` | Header identifies Hudong source, relation, and new-node target; all fields are non-empty; every `NewNode` value should appear in `new_node.csv`. |
| `new_node.csv` | Header includes `title` and source-compatible `lable`; titles are non-empty and unique; label/lable values are `newNode` unless deliberately changed. |

Treat malformed headers as a hard failure. Treat duplicate triples and delimiter characters inside fields as review warnings unless the user chooses strict failure on warnings.

## Relation distribution analysis

The `wikidataAnalyse` relation counter reads `wikidata_relation.csv`, counts relation names, sorts by count descending, and writes `staticResult.txt`. This is useful for:

- identifying dominant relation types before importing;
- spotting accidental header rows or empty relation labels;
- selecting relation labels for downstream relation extraction.

It is not a graph validation check and should not be used as proof that CSV endpoints exist in Neo4j.

## Attribute extraction workflow

Attribute extraction reads Hudong page CSV basic-info fields and writes:

```text
Entity,AttributeName,Attribute
```

The source filters attributes so that the attribute value appears in the known entity set from new Wikidata nodes and predicted labels. Use this artifact as an additional relation table; final import and label-specific matching still belong to the graph import route.

When regenerating attributes:

1. Run from the attribute-analysis directory expected by the source layout.
2. Confirm `new_node.csv`, predicted labels, and Hudong page CSVs are present.
3. Validate delimiter safety because basic-info values may contain punctuation, aliases, and inconsistent trailing colons.
