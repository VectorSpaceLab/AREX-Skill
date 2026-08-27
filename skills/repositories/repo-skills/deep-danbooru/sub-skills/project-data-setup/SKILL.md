---
name: project-data-setup
description: "Set up and validate DeepDanbooru projects, tag files,
  Danbooru-like SQLite datasets, and training-database conversions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Project and data setup

Use this sub-skill before training when a DeepDanbooru project, tag vocabulary,
Danbooru-style SQLite database, or filtered training database is missing or
uncertain. It is deliberately CPU-safe and offline by default. The bundled
scripts use only the Python standard library and never contact Danbooru or read
the original source checkout.

## Fast path

1. Put a dataset SQLite file beside an `images/` directory. Validate it with
   [`validate_danbooru_sqlite.py`](scripts/validate_danbooru_sqlite.py).
2. Create a project in a new directory:
   `deepdanbooru create-project /absolute/path/to/project`.
3. Edit `project.json` so `database_path` points to the dataset SQLite file.
   Keep the path usable from the machine that will train; do not leave it as
   `null`. See [`project-json-reference.md`](references/project-json-reference.md).
4. Supply a reviewed newline-separated `tags.txt`, or explicitly authorize
   the network operation in the tag-download workflow below.
5. If system rating tags or deleted-post filtering is needed, make a separate
   SQLite output with `make-training-database`; never use the source file as
   its own output.
6. Run the checks in [`troubleshooting.md`](references/troubleshooting.md),
   then hand the prepared project to the sibling **model-training** sub-skill.
   After a model exists, hand images and the project to **inference-evaluation**.

## Exact command forms

Create a project (the destination must be a directory path accepted by Click):

```console
deepdanbooru create-project PROJECT_PATH
```

This creates the directory if necessary and writes only `project.json`; it does
not create `tags.txt`, a database, an images directory, or a model. It is
intended for a new project. Inspect and edit the generated JSON rather than
assuming the default `database_path` is usable.

Download tags only after an explicit user decision to make a network request:

```console
deepdanbooru download-tags PROJECT_PATH \
  --limit INTEGER --minimum-post-count INTEGER --overwrite \
  --username DANBOORU_USERNAME --api-key DANBOORU_API_KEY
```

`--limit` defaults to `10000` for each downloaded category and
`--minimum-post-count` defaults to `500`. `--overwrite` is a flag and is
required when an existing `tags.txt` may be replaced. `--username` and
`--api-key` are required by the CLI even though the bundled offline checks do
not need them. The command contacts `https://danbooru.donmai.us/tags.json`.
Do not put real credentials in fixtures, generated skills, logs, or an
unapproved shell history.

Convert a source Danbooru export into the smaller training schema:

```console
deepdanbooru make-training-database SOURCE_PATH OUTPUT_PATH \
  --start-id INTEGER --end-id INTEGER --use-deleted \
  --chunk-size INTEGER --overwrite --vacuum
```

Defaults are `start-id=1`, `end-id=sys.maxsize`, `chunk-size=5000000`, and all
three flags are off. `--overwrite` deletes an existing output before creating
it. `--vacuum` runs SQLite `VACUUM` after copying. Use a separate output path
and make a backup before destructive replacement.

## Contracts that must agree

* The project contract is `project.json` plus `tags.txt`; the full default
  context and path rules are in the project reference.
* A usable dataset has `posts(id, md5, file_ext, tag_string,
  tag_count_general)`. A source for conversion additionally has `rating`,
  `score`, and `is_deleted`; the converted output intentionally drops those
  source columns and adds rating tags into `tag_string`.
* Supported training image extensions are `png`, `jpg`, and `jpeg` (lowercase
  values in SQLite). For a row, the loader looks for
  `DATASET_DIR/images/MD5[:2]/MD5.FILE_EXT`, where `DATASET_DIR` is the SQLite
  file's parent directory. The `md5` text need not be a real hash, but it must
  match the file name and have a useful first-two-character directory prefix.
* Rows are selected only when `tag_count_general >= project.json`'s
  `minimum_tag_count`, and are ordered by `id`. The loader does not verify
  that files exist while building records; check the layout before training.
* Use UTF-8 for `tags.txt`, one tag per line. Blank/whitespace-only lines are
  ignored and surrounding whitespace is stripped; preserve a deliberate,
  duplicate-free order.

## Safe validation workflow

```console
python scripts/create_project_probe.py
python scripts/validate_tags_txt.py PROJECT_PATH/tags.txt
python scripts/validate_danbooru_sqlite.py DATASET_DIR/data.sqlite
python scripts/make_tiny_danbooru_sqlite.py --output-dir ./dd-fixture
python scripts/validate_danbooru_sqlite.py ./dd-fixture/source.sqlite --mode source
```

The tiny fixture is for local command and schema checks, not a training-quality
corpus. Its image payloads are deterministic fixtures; use real decoded images
for model work. All scripts refuse unsafe replacement by default and have
`--help`.

## Failure handling

* A missing or malformed `posts` schema is a data-preparation failure, not a
  reason to lower `minimum_tag_count` blindly. Validate the source in `source`
  mode before conversion and the output in `training` mode afterward.
* A source/output collision is always an error. If output already exists,
  omit `--overwrite` first and inspect it; only use the flag after an explicit
  replacement decision.
* Deleted rows are skipped by default. `--use-deleted` includes them, but it
  does not restore missing image files. Rating `g`, `s`, `q`, and `e` becomes
  `rating:general`, `rating:sensitive`, `rating:questionable`, or
  `rating:explicit`; score is currently not converted.
* Tag download failures can be authentication, network, API response, or
  filesystem failures. Keep the current local tag files, fix the cause, and
  retry only with consent. Offline scripts cannot prove remote tag freshness.
* A project can be structurally valid yet unusable when `database_path` is
  null, points elsewhere, has no adjacent `images/`, has missing files, or has
  no tags meeting the threshold. Report each condition separately.

## Handoff boundary

This sub-skill ends after the project/data contracts and checks pass. It does
not train a model, evaluate images, download credentials, or claim GPU
readiness. The next **model-training** step consumes the project and validated
SQLite/image layout. The **inference-evaluation** step consumes a trained model,
its matching `tags.txt`, and target files or folders.

See also:

* [`cli-reference.md`](references/cli-reference.md) for option defaults and
  side effects.
* [`dataset-format.md`](references/dataset-format.md) for schemas and paths.
* [`tag-download-and-tags-files.md`](references/tag-download-and-tags-files.md)
  for offline tag-file choices and network boundaries.
