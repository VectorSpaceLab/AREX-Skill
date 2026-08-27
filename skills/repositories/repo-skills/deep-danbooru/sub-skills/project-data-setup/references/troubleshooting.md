# Troubleshooting project and data setup

## CLI cannot start

Run `deepdanbooru --help` and check the installed environment before changing
data. The package imports TensorFlow and TensorFlow-IO at startup, so a missing
required dependency can prevent even setup commands from running. Install the
supported project dependencies in the active environment, then re-run the help
probe. CPU verification is the required baseline; do not infer GPU readiness
from a successful import.

## `project.json` is present but training cannot find data

1. Confirm the file is valid JSON.
2. Confirm `database_path` is not `null` and points to the intended SQLite file.
3. Confirm the SQLite parent contains `images/`.
4. Run the SQLite checker in `training` or `source` mode as appropriate.
5. Compare `minimum_tag_count` with actual `tag_count_general` values.
6. Derive a few paths using the rule in [`dataset-format.md`](dataset-format.md)
   and check the files exist and decode.

Do not solve a path problem by copying a database away from its image tree.

## SQLite schema errors

Use the read-only checker first:

```console
python scripts/validate_danbooru_sqlite.py FILE.sqlite --mode source
python scripts/validate_danbooru_sqlite.py FILE.sqlite --mode training
```

A source conversion requires `rating`, `score`, and `is_deleted` in addition to
the five training columns. A converted output intentionally does not retain
those three columns. If the source has a differently named deletion or rating
field, make an explicit transformation outside this skill; do not silently
pretend it satisfies the contract.

If `make-training-database` created a partial output, do not run training on it.
Move it aside or remove it only after confirming it is disposable, then rerun
with a fresh output path. `--overwrite` is destructive and is not a repair
operation by itself.

## Zero or unexpectedly few records

The loader filters on exact lowercase extension values and
`tag_count_general >= minimum_tag_count`. Check both. It orders by `id`, but
does not check image existence while fetching records. A post can therefore be
selected even when its derived file is missing. Use `--check-images` on the
checker and inspect reported paths. If deleted records were expected, remember
that the converter excludes them unless `--use-deleted` is set; including them
still requires their image files.

## Missing or malformed tags

`create-project` never creates `tags.txt`. Make a reviewed local file or use
`download-tags` only with explicit network and credential approval. Validate
encoding, duplicates, whitespace, and optional system tags:

```console
python scripts/validate_tags_txt.py PROJECT/tags.txt
python scripts/validate_tags_txt.py PROJECT/tags.txt --require-system-tags
```

Tags in data are space-separated. A tag containing an unescaped space cannot
be represented as one tag by the current loader. Keep file order stable; it is
the model output index order.

## Download authentication or network failure

The downloader calls the remote Danbooru endpoint and requires both
`--username` and `--api-key`. Do not retry automatically, paste secrets into
reports, or replace a failed response with invented tags. Preserve the previous
`tags.txt`, diagnose credentials/connectivity/API response behavior, and retry
only with authorization. The offline fixture and validators make no network
requests and cannot validate remote freshness.

## Source/output collision or overwrite prompt

`SOURCE_PATH == OUTPUT_PATH` is rejected. If the output already exists, the
normal command fails; inspect it before deciding whether replacement is safe.
With `--overwrite`, the existing output is removed before the new schema is
created. Prefer a new output path, validate it, and retain the original source.

## Fixture or validator reports a failure

The tiny fixture is intentionally small and is designed to exercise schema,
filtering, rating, deleted-row, and path behavior—not accuracy or model
training. Run each script's `--help`, use a new output directory, and check
that the local Python can open SQLite. Validators are read-only; they do not
repair schemas, create missing images, or edit project files.
