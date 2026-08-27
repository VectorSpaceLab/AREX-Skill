# Question answering and tagging

## Question answering flow

`question_answering.question_answering` uses THULAC tokenization plus four regex buckets to decide which helper path to run.

| q_type | Example cues | Helper path | Graph relations used | Result shape |
| --- | --- | --- | --- | --- |
| `0` | `适合种什么`, `种什么好` | `get_shi_plant` / `get_xian_plant` | `适合种植`, `属于`, `气候` | Plant answers plus location chain |
| `1` | `气候是什么`, `属于哪种气候`, `是什么天气`, `哪种天气`, `天气...` | `get_shi_weather` / `get_xian_weather` | `气候`, optional `首都`, `属于` | Weather answers plus location chain |
| `2` | `有哪些营养`, `含...成分`, `含...元素` | `get_nutrition` | `营养成分` | Nutrient answers |
| `3` | `植物学`, `知识` | `get_plant_knowledge` | `科`, `属`, `门`, `纲`, `目`, `亚目`, `亚科` | Taxonomy answers |

Behavioral notes:

- Questions outside those buckets render the empty-answer fallback.
- The template expects `ret['answer']` for the table and `ret['list']` for the ECharts graph.
- Location questions rely on `city_list.txt` plus administrative-level lookups in Neo4j.
- Weather and plant answers are assembled from graph traversal, not from a separate model.

## Entity labeling page

`tagging_data_view.showtagging_data` renders one Neo4j `HudongItem` at a time.

### Inputs and files

- GET field: `title`
- Reads `label_data/labels.txt` to count already labeled samples
- Uses `baseInfoKeyList`, `baseInfoValueList`, and `openTypeList` fields from the Neo4j node
- Splits those Neo4j fields on `##`

### Label set

| id | UI label |
| --- | --- |
| `0` | Invalid |
| `1` | Person |
| `2` | Location |
| `3` | Organization |
| `4` | Political economy |
| `5` | Animal |
| `6` | Plant |
| `7` | Chemicals |
| `8` | Climate |
| `9` | Food items |
| `10` | Diseases |
| `11` | Natural Disaster |
| `12` | Nutrients |
| `13` | Biochemistry |
| `14` | Agricultural implements |
| `15` | Technology |
| `16` | other |

### Write-back flow

`tagging_data_writefile_view.tagging_push` expects GET fields `label` and `title`.

- It appends `title label` to `label_data/labels.txt` when the title is new.
- It samples the next title from `label_data/word_list.txt`.
- It renders `tagging_cache.html`, which immediately redirects to `tagging_data?title=...`.

## Relation tagging page

`tagging.tagging` is a Mongo-backed annotation queue.

### GET behavior

- Samples a random record from the `train_data` collection.
- Skips records until it finds one whose shape matches the expected 7-field payload.
- Renders `taggingSentences.html` with the `statement`, `entity1`, `relation`, and `entity2` fields.

### POST behavior

- Accepts JSON fields: `statement`, `entity1`, `entity1Pos`, `relation`, `entity2`, `entity2Pos`.
- Inserts the submitted row into `test_data`.
- Deletes the corresponding row from `train_data`.
- The page buttons are `True`, `Change One`, and `Submit`.

### Important data contract

The page is an annotation workflow, not a training endpoint. It assumes the queue records already contain entity positions and sentence text in the expected schema.
