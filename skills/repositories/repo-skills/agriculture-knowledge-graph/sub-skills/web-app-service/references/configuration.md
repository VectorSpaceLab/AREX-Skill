# Configuration and prerequisites

## Runtime baseline

This demo is a legacy Django 1.11-era application. A working environment needs a Python 3.x interpreter that can load the older dependency set, especially:

- `Django>=1.11.7`
- `thulac>=0.1.2`
- `py2neo==4.1.0`
- `pyfasttext==0.4.5`
- `pymongo>=3.6.1`
- `pinyin>=0.4.0`

Modern Django or py2neo releases are not a drop-in replacement for this codebase.

## Service prerequisites

| Service | Expected local endpoint | Used by |
| --- | --- | --- |
| Neo4j | `http://localhost:7474` | `demo/Model/neo_models.py`, most read-only pages, QA, tagging, entity detail, relation queries |
| MongoDB | `localhost:27017` | relation tagging queue in `demo/demo/tagging.py` |

`demo/Model/neo_models.py` uses a hard-coded Neo4j login (`neo4j` / `123456`). If those credentials differ in the target environment, update the wrapper before launching the demo.

## Bundled assets loaded at startup

`demo/toolkit/pre_load.py` eagerly opens and reads these local files as soon as the view modules import it:

- `demo/toolkit/predict_labels.txt`
- `demo/toolkit/vector_15.txt`
- `demo/toolkit/micropedia_tree.txt`
- `demo/toolkit/leaf_list.txt`
- `demo/toolkit/id2obj.txt`
- `demo/toolkit/relationStaticResult.txt`

Additional runtime files used by the UI:

- `demo/label_data/city_list.txt`
- `demo/label_data/labels.txt`
- `demo/label_data/word_list.txt`
- `demo/db.sqlite3`

## Django settings highlights

- `DJANGO_SETTINGS_MODULE` is `demo.settings`
- `BASE_DIR` is the inner `demo/` directory
- templates are loaded from `BASE_DIR/templates`
- static files are expected under `BASE_DIR/static`
- SQLite is configured as `db.sqlite3`
- `DEBUG=True`
- `ALLOWED_HOSTS` contains localhost and the historical deployment hostnames

## Working-directory rule

Run service commands from the `demo/` directory unless the script explicitly changes into it. Several modules use `os.getcwd()` or plain relative paths when opening `toolkit/` and `label_data/` files.

## Launch order

1. Verify the local files above.
2. Start Neo4j.
3. Start MongoDB if relation tagging is needed.
4. Run the preflight script.
5. Only then start Django.

`demo/django_server_start.sh` is only a bare `python3 manage.py runserver` wrapper, so the preflight step is the safer entry point.
