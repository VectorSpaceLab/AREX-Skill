# Neo4j Import and Query Guide

This guide distills the repository's graph-loading and graph-query behavior into
a self-contained operating reference. It does not require the original checkout
unless the user explicitly wants to rebuild from the original data files.

## Graph shape

### Node labels

| Label | Source artifact | Important properties | Notes |
| --- | --- | --- | --- |
| `HudongItem` | `hudong_pedia.csv`, `hudong_pedia2.csv` | `title`, `url`, `image`, `openTypeList`, `detail`, `baseInfoKeyList`, `baseInfoValueList` | Main encyclopedia entities. `title` is the intended unique key. |
| `NewNode` | `new_node.csv` | `title` | Wikidata-only nodes. The CSV also has a misspelled `lable` column that is not used by the import snippets. |
| `Weather` | `static_weather_list.csv` | `title` | Climate/weather nodes used by weather-to-plant and city-climate relations. |

### Relationship labels

| Relationship label | Direction | `type` property | Source artifact | Notes |
| --- | --- | --- | --- | --- |
| `RELATION` | `HudongItem -> HudongItem` | Wikidata relation name | `wikidata_relation.csv` | Example relation names include `instance of`, `country`, and `taxon rank`. |
| `RELATION` | `HudongItem -> NewNode` | Wikidata relation name | `wikidata_relation2.csv` | Requires the `NewNode` endpoint import first. |
| `RELATION` | Any of `HudongItem`/`NewNode` to any of `HudongItem`/`NewNode` | Attribute name | `attributes.csv` | Imported with four label-specific `MATCH` variants because title indexes are label-specific. |
| `Weather2Plant` | `Weather -> HudongItem` | Usually `适合种植` | `weather_plant.csv` | Generic relation searches can see this edge; exact `findEntityRelation` does not because it matches only `:RELATION`. |
| `CityWeather` | Any node with matching `title` -> `Weather` | Usually `气候` | `city_weather.csv` | The source import intentionally matches the city without a label. |

## Import order

Use this order when building a fresh graph:

1. Put CSV files in Neo4j's configured import directory using the expected file
   names, or adapt the file URLs in the bundled Cypher template.
2. Create/merge `HudongItem` nodes from both Hudong CSV files.
3. Add a uniqueness constraint/index on `HudongItem.title` if your Neo4j version
   accepts it and the data has no duplicate titles. For repeatable imports,
   prefer creating the constraint first and using `MERGE`.
4. Create/merge `NewNode` nodes from `new_node.csv` and constrain `NewNode.title`.
5. Import Wikidata `RELATION` edges from `wikidata_relation2.csv`, then
   `wikidata_relation.csv`.
6. Import `attributes.csv` in four passes for `HudongItem/NewNode` endpoint
   combinations.
7. Create/merge `Weather` nodes from `static_weather_list.csv` and constrain
   `Weather.title`.
8. Import `Weather2Plant` edges, then `CityWeather` edges.

The source README imports some nodes with `CREATE` and adds constraints after
loading. That works only for a one-time clean import. For operational rebuilds,
use the idempotent `MERGE` patterns in [the bundled template](../scripts/cypher_import_templates.cypher).

## Source wrapper method map

The historical `Neo4j` wrapper is a thin `py2neo` class. It connects to
`http://localhost:7474` and returns `graph.run(...).data()` lists or `evaluate()`
objects. Preserve method intent, but use parameters in new code instead of
concatenating user text into Cypher.

| Method | Inputs | Query intent | Return shape |
| --- | --- | --- | --- |
| `connectDB()` | none | Connect to a local Neo4j HTTP endpoint with configured credentials. | Mutates `self.graph`. |
| `matchItembyTitle(value)` | title | Looks for `(n:Item {title: value})`. | List of rows with key `n`; this legacy label is not used by the README import. |
| `matchHudongItembyTitle(value)` | title | Looks for `(n:HudongItem {title: value})`. | List of rows with key `n`. |
| `getEntityRelationbyEntity(value)` | entity title | Direct outgoing edges from any node with matching title. | Rows with `rel` and `entity2`. |
| `findRelationByEntity(entity1)` | entity title | Direct outgoing edges from any node with matching title. | Rows with `n1`, `rel`, `n2`. |
| `findRelationByEntity2(entity2)` | entity title | Direct incoming edges to any node with matching title. | Rows with `n1`, `rel`, `n2`. |
| `findOtherEntities(entity, relation)` | source title, relation string | Direct outgoing edges whose relationship `type` property exactly matches the relation. | Rows with `n1`, `rel`, `n2`. |
| `findOtherEntities2(entity, relation)` | target title, relation string | Direct incoming edges whose relationship `type` property exactly matches the relation. | Rows with `n1`, `rel`, `n2`. |
| `findRelationByEntities(entity1, entity2)` | two titles | Shortest undirected path using only `:RELATION*` across `HudongItem`/`NewNode` label combinations. | List of dictionaries `{n1, n2, rel}` for each relationship on the path. |
| `findEntityRelation(entity1, relation, entity2)` | source title, relation string, target title | Exact directed `:RELATION {type: relation}` check across `HudongItem`/`NewNode` label combinations. | Rows with `n1`, `rel`, `n2`. |

## Relation search semantics

The Django relation-search page implements six modes. If the task is to recreate
or debug relation search, keep this decision table:

| Supplied fields | Wrapper method | Meaning |
| --- | --- | --- |
| `entity1` only | `findRelationByEntity` | Show direct outgoing relationships from `entity1`. |
| `entity2` only | `findRelationByEntity2` | Show direct incoming relationships to `entity2`. |
| `entity1 + relation` | `findOtherEntities` | Show targets reachable by a direct edge with exactly that `type`. |
| `entity2 + relation` | `findOtherEntities2` | Show sources with a direct edge of exactly that `type` into `entity2`. |
| `entity1 + entity2` | `findRelationByEntities` | Show shortest path between the two entities using only `:RELATION` edges. |
| `entity1 + relation + entity2` | `findEntityRelation` | Check the exact directed triple. |

Additional behavior to preserve or account for:

- The UI lowercases the relation input before querying. Most Wikidata relation
  names in the bundled counts are lowercase English, while Chinese relation
  values are unaffected by `.lower()`.
- Relation results are sorted by a frequency table parsed from
  `relationStaticResult.txt`; missing relation names receive count `0`.
- Exact triple checks and shortest paths only use the `RELATION` relationship
  label. Weather edges (`Weather2Plant`, `CityWeather`) are visible to generic
  direct-edge methods but not to those exact/shortest-path methods unless the
  query is intentionally broadened.
- In `py2neo` 4.x, `.data()` returns an empty list when no rows match. The
  historical fallback code tests `answer is None`, so some label-combination
  fallbacks in `findEntityRelation` will not run. Use an explicit `if not rows`
  fallback or a single `UNION` query when modernizing.

## Safer query patterns

Prefer parameterized Cypher in new tooling:

```cypher
MATCH (n:HudongItem {title: $title})
RETURN n
```

```cypher
MATCH (n1 {title: $source})-[rel]->(n2)
WHERE rel.type = $relation
RETURN n1, rel, n2
```

For cross-label exact relation checks, avoid procedural fallbacks:

```cypher
MATCH (n1)-[rel:RELATION {type: $relation}]->(n2)
WHERE n1.title = $source AND n2.title = $target
  AND (n1:HudongItem OR n1:NewNode)
  AND (n2:HudongItem OR n2:NewNode)
RETURN n1, rel, n2
```

Use label-specific `MATCH` forms when you need index-backed performance on older
Neo4j versions.
