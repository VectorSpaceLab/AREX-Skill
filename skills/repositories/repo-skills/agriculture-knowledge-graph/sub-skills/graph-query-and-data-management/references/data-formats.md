# Data Format Guide

This repository stores most graph artifacts as UTF-8 CSV or plain-text files.
Large source artifacts are not bundled into the skill; this page records the
schemas and quirks needed to rebuild, validate, or troubleshoot them.

## Core graph CSVs

| File name | Header | Typical row count in source evidence | Purpose | Import target |
| --- | --- | ---: | --- | --- |
| `hudong_pedia.csv` | `title,url,image,openTypeList,detail,baseInfoKeyList,baseInfoValueList` | 113,037 | Main Hudong encyclopedia pages. | `(:HudongItem)` |
| `hudong_pedia2.csv` | same as `hudong_pedia.csv` | 36,892 | Additional Hudong pages. | `(:HudongItem)` |
| `attributes.csv` | `Entity,AttributeName,Attribute` | 81,711 | Attribute-derived entity relations. | `[:RELATION {type: AttributeName}]` |
| `new_node.csv` | `title,lable` | 96,670 | Wikidata-only target nodes. | `(:NewNode {title})`; `lable` is misspelled and ignored by README imports. |
| `wikidata_relation.csv` | `HudongItem1,relation,HudongItem2` | 58,962 | Wikidata relations between two Hudong entities. | `(:HudongItem)-[:RELATION]->(:HudongItem)` |
| `wikidata_relation2.csv` | `HudongItem,relation,NewNode` | 166,059 | Wikidata relations from Hudong entities to new Wikidata nodes. | `(:HudongItem)-[:RELATION]->(:NewNode)` |
| `static_weather_list.csv` | `title` | 144 | Weather/climate terms. | `(:Weather {title})` |
| `weather_plant.csv` | `Weather,relation,Plant` | 851 | Climate-to-plant suitability relations. | `(:Weather)-[:Weather2Plant]->(:HudongItem)` |
| `city_weather.csv` | `city,relation,weather` | 463 | City-to-climate relations. | `(city)-[:CityWeather]->(:Weather)` where `city` is any node with a matching `title`. |

## Field conventions

- CSV delimiter is comma. Use a CSV parser; do not split lines on commas because
  details and values can contain punctuation and long text.
- Text is Chinese/English UTF-8. Prefer `utf-8-sig` while validating headers so
  a byte-order mark does not corrupt the first column name.
- `HudongItem.openTypeList`, `baseInfoKeyList`, and `baseInfoValueList` are
  serialized list fields joined by `##`.
- `baseInfoKeyList` and `baseInfoValueList` are parallel arrays. They can be
  blank or have mismatched lengths; the web detail view renders blanks when a
  key lacks a value.
- `attributes.csv` endpoints are ambiguous until matched against labels. The
  README import handles this by trying every `HudongItem`/`NewNode` source and
  target label combination.
- Relationship `type` properties are strings. Wikidata relations are usually
  lowercase English; attribute and weather relations may be Chinese.

## Hierarchy files

| File name | Format | Meaning |
| --- | --- | --- |
| `micropedia_tree.txt` | `parent child` separated by a single space | Non-leaf classification tree edges. The root used by the API is `农业`. |
| `leaf_list.txt` | `category entity` separated by a single space | Leaf entities under each category. |

The hierarchy API ignores exact duplicate lines. Avoid category/entity names
containing spaces unless you also update the parser, because the source parser
uses `line.strip().split(' ')` and reads only the first two tokens.

## Vector files

The vector API expects a plain text embedding file with no header:

```text
word 0.12 -0.03 0.44 ...
```

Each line's first token is the word and all remaining tokens are parsed as
floats. The demo preload references a reduced-dimensional vector file, while
comments also mention a larger vector file. Do not claim vector availability
unless the target runtime actually has the file.

## Relation frequency file

`relationStaticResult.txt` is a tuple-like text file, one relation count per
line:

```text
('instance of', 9381)
('country', 5749)
```

The relation page parses it with simple comma splitting and then sorts search
results by count descending. If you regenerate this file, keep the same simple
format or update the parser. Relation names containing commas would break the
historical parser.

## Lightweight validation checklist

Before importing or debugging graph data, verify:

1. Required CSV file names match the Cypher template or have been adapted.
2. Headers exactly match the expected names, including the historical `lable`
   spelling in `new_node.csv`.
3. `title`, endpoint, and relation fields are non-empty after trimming.
4. `hudong_pedia.csv` and `hudong_pedia2.csv` do not contain conflicting titles
   if a uniqueness constraint will be enforced.
5. `wikidata_relation2.csv` endpoints that are not Hudong items have matching
   `NewNode` rows.
6. Weather relation endpoints have matching `Weather` and plant/city nodes.
7. Hierarchy files use two whitespace-separated tokens per line and preserve
   `农业` as the root unless code is intentionally changed.
