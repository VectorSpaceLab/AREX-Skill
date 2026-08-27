# Django routes and views

This service is a Django 1.11-era demo. Most view modules import `toolkit.pre_load` at module load time, so route import can trigger THULAC, Neo4j, MongoDB, vector, and tree initialization before any request is handled.

## URL map

| URL pattern | Method | View | Template | Main fields | Notes |
| --- | --- | --- | --- | --- | --- |
| `^$` | GET | `index_view.index` | `index.html` | none | Landing page for entity recognition. |
| `^ER-post` | POST | `index_ERform_view.ER_post` | `index.html` | `user_text` | Runs THULAC segmentation and `toolkit.NER.get_NE`; recognized titles link to `detail?title=...`. |
| `^detail` | GET | `detail_view.showdetail` | `detail.html` | `title` | Loads a Neo4j `HudongItem`, tag cloud, taxonomy path, and predicted entity class. |
| `^search_entity` | GET | `relation_view.search_entity` | `entity.html` | `user_text` | Entity-centered relation lookup sorted by `toolkit/relationStaticResult.txt`. |
| `^search_relation` | GET | `relation_view.search_relation` | `relation.html` | `entity1_text`, `relation_name_text`, `entity2_text` | Supports entity-only, relation-only, pairwise, and triple queries. |
| `^overview` | GET | `overview_view.show_overview` | `overview.html` | `node` | Taxonomy navigation with parent, branch, leaf, and tree-modal content. |
| `^qa` | GET | `question_answering.question_answering` | `question_answering.html` | `question` | Regex-driven QA plus graph rendering. |
| `^decision` | POST | `decisions_making.decisions_making` | `decisions_making.html` | `img_base64` | Image-to-entity matching through an external API and Neo4j graph lookup. |
| `^tagging_data` | GET | `tagging_data_view.showtagging_data` | `tagging_data.html` | `title` | Manual entity-labeling page for a Neo4j item. |
| `^tagging-get` | GET | `tagging_data_writefile_view.tagging_push` | `tagging_cache.html` | `label`, `title` | Appends one manual label line and prepares the next title. |
| `^tagging` | GET/POST | `tagging.tagging` | `taggingSentences.html` | GET none; POST JSON payload | Relation annotation queue backed by MongoDB. |
| `^404` | GET | `_404_view._404_` | `404.html` | none | Fallback page. |

## Request field glossary

- `user_text` — free-text entity recognition input.
- `title` — entity title used by detail and labeling pages.
- `entity1_text`, `relation_name_text`, `entity2_text` — relation query form fields.
- `node` — taxonomy node shown in the overview tree.
- `question` — QA prompt text.
- `img_base64` — uploaded image payload for the image-match page.
- `label` — manual entity class id chosen on the labeling page.
- `statement`, `entity1`, `entity1Pos`, `relation`, `entity2`, `entity2Pos` — relation-tagging JSON payload fields.

## View-level service notes

- `index_ERform_view.ER_post` links recognized entities to `detail?title=...`; temporary labels only get tooltip text.
- `detail_view.showdetail` depends on the pretrained word-vector model and taxonomy tree to build the tag cloud and agricultural path output.
- `relation_view.search_relation` lowercases the typed relation text before querying Neo4j.
- `question_answering.question_answering` returns `ret['answer']` for the table and `ret['list']` for the graph.
- `tagging_data_view.showtagging_data` expects Neo4j item fields split by `##` and builds a 17-class radio group.
- `tagging.tagging` samples a random MongoDB record on GET, then inserts the accepted annotation into `test_data` on POST.
- `decisions_making.decisions_making` calls an external image-recognition API, so network availability matters even when Neo4j is up.
