# Weather and Attribute Pipelines

This reference covers climate/city/weather artifacts and the Hudong attribute extraction route. These scripts are partly crawler-like and partly service-backed processing, so prefer existing CSV validation unless the user explicitly asks to regenerate them.

## Weather artifact map

| Artifact | Header or structure | Producer | Meaning |
| --- | --- | --- | --- |
| `city_list.txt` | one city per line | `citydata.py get_city_list` | City names selected from a city JSON source, usually names ending in `市`. |
| `city_weather.csv` | `city,relation,weather` | `citydata.py get_city_weather` | City-to-climate relation rows; source relation value is `气候`. |
| `static_weather_list.csv` | `title` | `citydata.py get_city_weather` | Distinct climate names observed in city Hudong page basic-info fields. |
| `weather_corpus.json` | JSON list with `title`, `summary`, `content` | `weatherCrawler.py` | Weather/climate page text fetched from Baike/Hudong. |
| `weather_plant.csv` | `Weather,relation,Plant` | `weatherPlant.py` | Climate-to-plant rows; source relation value is `适合种植`. |
| `weather2weather.txt` | `alias -> page-title` style mappings | manual/source data | Maps climate aliases to weather pages that have content. |

## City/weather extraction

Run only in a local working copy with the required input data:

```bash
cd wikidataSpider/weatherData
python citydata.py get_city_list
python citydata.py get_city_weather
```

Important behavior:

- `get_city_list` reads a city JSON file and writes `city_list.txt`.
- `get_city_weather` reads `city_list.txt` and a Hudong page CSV from the analysis area, then scans `baseInfoKeyList` / `baseInfoValueList` for climate keys such as `气候条件` and `气候`.
- It writes both `city_weather.csv` and `static_weather_list.csv`.
- The script uses pandas and Fire; those dependencies are not needed for the bundled validator.

## Weather page crawl and plant relation extraction

The weather page crawler fetches Baike/Hudong pages for climates from `static_weather_list.csv`, applies alias mappings from `weather2weather.txt`, and writes `weather_corpus.json`.

```bash
cd wikidataSpider/weatherData
python weatherCrawler.py
```

The plant relation extractor is service-backed:

```bash
cd wikidataSpider/weatherData
python weatherPlant.py
```

It reads `weather_corpus.json`, loads predicted entity labels for NER, calls the repository's NER helper, then queries Neo4j to confirm candidate entities are in the plant kingdom before writing `weather_plant.csv`. Do not run it as an offline smoke test; use the bundled CSV validator for no-service checks.

## Weather CSV invariants

| File | Required checks |
| --- | --- |
| `city_weather.csv` | Header `city,relation,weather`; non-empty city and weather; relation usually `气候`; each row has exactly three columns. |
| `weather_plant.csv` | Header `Weather,relation,Plant`; non-empty weather and plant; relation usually `适合种植`; duplicate rows are reviewed before import. |
| `static_weather_list.csv` | Header `title`; non-empty climate names; values should cover the distinct `weather` column in `city_weather.csv`. |

The bundled validator checks `city_weather.csv` and `weather_plant.csv` directly. Validate `static_weather_list.csv` manually or with a simple header check when regenerating it.

## Attribute extraction route

The attribute extraction script produces `attributes.csv` from Hudong page basic-info fields and known entity sets.

Expected header:

```text
Entity,AttributeName,Attribute
```

Use it when the user asks why an entity has attribute-like graph edges or how the repository derived relations from Hudong table fields. It is not a network crawler, but it is path-sensitive and depends on prior Wikidata/predicted-label artifacts.

Recommended checks before import:

- `Entity`, `AttributeName`, and `Attribute` are non-empty.
- Base-info key/value lists were split with the same `##` separator used by Hudong page CSVs.
- Attribute values are intended graph nodes, not long free-text descriptions.
- Duplicate rows are intentional or deduplicated before final import.
