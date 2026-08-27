# Crawler Workflows

This reference covers the source crawlers and acquisition scripts that create the raw Hudong/Baike, Wikidata, weather, and tree artifacts. The repository is an old, un-packaged research/demo checkout; most scripts assume a specific current working directory and write files next to themselves.

## Safety and execution policy

- Do not run broad crawls by default. These workflows contact external sites such as Baike/Hudong, CKCEST, and Wikidata and may run for a long time.
- Inspect existing outputs first. The repository already contains many generated JSON/CSV artifacts; most future tasks can validate or transform these instead of recrawling.
- If the user approves a live crawl, lower concurrency, respect site policies, set a clear user agent where appropriate, and stop on repeated HTTP errors or blocks.
- Keep crawler output in a work directory under the user's active checkout or a temporary directory. Do not write into the generated skill tree.
- Run no final Neo4j import from this sub-skill; after validated CSVs exist, route import/query work to graph-query-and-data-management.

## Working-directory map

| Workflow | Run from | Primary command | Main inputs | Main outputs | Notes |
| --- | --- | --- | --- | --- | --- |
| Hudong page crawl | `MyCrawler/` | `scrapy crawl hudong` | `crawled_leaf_list.txt` in the Scrapy project package | `MyCrawler/data/hudong_pedia.json` | Uses `HudongPipeline`; output path is relative to the run directory. Network-heavy. |
| CKCEST agriculture wiki crawl | `MyCrawler/` | `scrapy crawl agri` | generated URL range in the spider | configured pipeline output | The source settings enable `HudongPipeline` by default; switch to `AgriPipeline` or Scrapy feeds if you need `agri_economic.json`. |
| Classification tree DFS | `dfs_tree_crawler/` | `python dfs_crawler.py` | Baike classification root `农业` | `treenode_list.txt` | Recursive network crawler; no throttle or retry policy in source. |
| Leaf list crawl | `dfs_tree_crawler/` | `python leaf_list_crawler.py` | `treenode_list.txt` | `leaf_list.txt` | Reads every non-leaf category and appends leaves. |
| Crawled leaf filter | `dfs_tree_crawler/` | `python create_leaflist.py` | `leaf_list.txt`, live Neo4j HudongItem graph | `crawled_leaf_list.txt` | Requires Neo4j; filters out leaves already present in the graph. |
| Wikidata property crawl | usually `wikidataSpider/` with settings module, or a checkout that provides a Scrapy config | `SCRAPY_SETTINGS_MODULE=wikidataCrawler.settings scrapy crawl relation` | Wikidata property summary page | `relation.json`, `chrmention.json` | The package in this checkout lacks a `scrapy.cfg`; set the settings module if Scrapy cannot find the project. |
| Wikidata entity search | `wikidataSpider/wikientities/` | `scrapy crawl entity` | predicted-label entity list | `entities.json` | Replace the source's hard-coded absolute input path with a relative entity-label file before running. |
| Wikidata entity relation crawl | `wikidataSpider/wikidataRelation/` | `python preProcess.py`, then `scrapy crawl entityRelation` | `entities.json`, relation-label mapping | `readytoCrawl.json`, `entityRelation.json`, `entity1_entity2.json` | Network-heavy; existing resume logic is path-sensitive. |
| Legacy token/table scripts | `data processing/` | direct Python module execution | `agri_economic.json`, THULAC | `table*.txt`, `article*.txt`, `merge_table3.txt` | README marks this area obsolete; use only for understanding historical word-table artifacts. |

## Main Hudong/CKCEST Scrapy project

Project settings are selected by `MyCrawler/scrapy.cfg` and `MyCrawler/MyCrawler/settings.py`.

### Spiders

| Spider | Source responsibility | Output item fields |
| --- | --- | --- |
| `hudong` | Builds Baike/Hudong URLs from `crawled_leaf_list.txt`, fetches pages, extracts title, URL, image, open-category tags, summary/detail text, and basic-info table fields. | `title`, `url`, `image`, `openTypeList`, `detail`, `baseInfoKeyList`, `baseInfoValueList` |
| `agri` | Crawls CKCEST agriculture wiki terminologies from a numeric URL range and extracts title, images, detail text, and URL. | `title`, `imageList`, `detail`, `url` |

### Pipeline behavior

- `HudongPipeline` writes a JSON array to `MyCrawler/data/hudong_pedia.json`, skips items whose title is `error`, and prints elapsed crawl time.
- `AgriPipeline` writes a JSON array to `MyCrawler/data/agri_economic.json`, but it is not enabled by default in the checked settings.
- The generated `hudong_pedia.csv` and `hudong_pedia2.csv` are downstream CSV forms with columns:

```text
title,url,image,openTypeList,detail,baseInfoKeyList,baseInfoValueList
```

`openTypeList`, `baseInfoKeyList`, and `baseInfoValueList` use `##` as an internal separator in the source data.

## DFS tree crawler sequence

The tree crawlers populate the agricultural concept hierarchy used by other parts of the project.

1. From `dfs_tree_crawler/`, run the DFS category crawler only if a live Baike crawl is approved. It appends category names to `treenode_list.txt`.
2. Run the leaf crawler to create `leaf_list.txt`; each row is a parent category plus a leaf page name separated by a space.
3. Run the leaf filter only with a working Neo4j graph; it writes `crawled_leaf_list.txt` for Hudong page crawling.
4. Copy or synchronize `crawled_leaf_list.txt` to the Hudong Scrapy project's expected input location if necessary.

## Wikidata Scrapy project sequence

### Property labels

The property crawler extracts two line-delimited JSON files:

| File | Fields |
| --- | --- |
| `relation.json` | `rid`, `rtype`, `rsubtype`, `link`, `rmention` |
| `chrmention.json` | `rid`, `chrmention` |

The source repository used a notebook to merge these into `result.json` / `relationResult.json`. If reproducing this step, keep the merge deterministic and preserve both the Wikidata property id and the Chinese mention when available.

### Entity search

The entity spider searches Wikidata for each predicted-label entity and writes line-delimited `entities.json` rows with:

| Field | Meaning |
| --- | --- |
| `jsonItem` | Raw Wikidata API search response for the query. |
| `jsonNumber` | Entity label/category id from the predicted-label source. |
| `entityOriginName` | Original search term from the predicted-label source. |

Before running, replace any absolute, developer-machine input path in the source with a relative entity-label file in the active checkout.

### Entity relation crawl

`preProcess.py` filters `entities.json` to exact language/text matches and writes line-delimited `readytoCrawl.json` rows containing `entity`, `entityOriginName`, and `jsonNumber`. The `entityRelation` spider then visits Wikidata entity pages and writes:

| File | Fields | Use |
| --- | --- | --- |
| `entityRelation.json` | `entity1`, `relation`, `entity2` | Main relation triple input for CSV conversion. |
| `entity1_entity2.json` | `entity1`, `relatedEntityId` | Resume/dedup helper for already crawled entity pairs. |

The relation crawl mixes Scrapy responses with direct `requests` calls for related entity labels, so normal Scrapy throttling may not limit every network request.

## Legacy data-processing scripts

The `data processing/` scripts tokenize `agri_economic.json` with THULAC and build old word tables or word2vec inputs. The repository README marks this directory as no longer useful. Use these scripts only to explain historical artifacts such as `merge_table3.txt`, not as the default route for current graph construction.
