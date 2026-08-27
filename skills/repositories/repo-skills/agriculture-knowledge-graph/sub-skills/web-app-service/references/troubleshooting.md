# Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| App fails before the first request | `toolkit/pre_load.py` eagerly initializes THULAC, Neo4j, MongoDB, the word-vector model, and the taxonomy tree | Confirm the required data files exist and both services are reachable before starting Django. |
| `manage.py help` or `runserver` fails on a modern Python stack | Legacy Django 1.11-era dependency mismatch | Use a Python 3.x environment that can still install the pinned dependency set, or isolate the demo in a legacy-compatible environment. |
| `FileNotFoundError` for `toolkit/*.txt` or `label_data/*.txt` | Wrong working directory or missing bundled assets | Run from `demo/` or let the preflight script change into it. |
| `/qa` returns `暂未找到答案` | The question did not match one of the four regex buckets, or the graph lacks the expected relation names | Check the prompt wording and the Neo4j relation labels such as `气候`, `适合种植`, `营养成分`, `科`, `属`, `门`, `纲`, `目`, `亚目`, and `亚科`. |
| `/search_relation` finds nothing for obvious pairs | Relation names are exact-string lookups and the shortest-path query only traverses `RELATION` edges | Verify the stored relation text and the labels of both endpoints. |
| `tagging-get` crashes while choosing the next title | The next-title sampler assumes `word_list.txt` is non-empty and indexable | Check that the file is populated and that the current sample title is not already exhausted. |
| Relation annotations do not disappear from the queue | The delete filter in `demo/demo/tagging.py` is fragile and compares the wrong field for `entity2` in the current code | Compare the POST payload keys with the Mongo filter before trusting queue removal. |
| `/decision` returns no image matches | External image-recognition API or network is unavailable, or the API credentials need updating | Confirm outbound network access and the hard-coded app id/key path in `demo/toolkit/img_match.py`. |

## Workflow-specific notes

- If a route fails only after importing `demo.demo.urls`, suspect the shared preload module rather than the individual view body.
- If Neo4j is up but relation queries are empty, the graph import or relation naming is usually the real issue.
- If MongoDB is up but `tagging` keeps looping, inspect the expected training-document shape in the collection.
