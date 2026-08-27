# CLI reference

The public entry point is `deepdanbooru=deepdanbooru.__main__:main`.
The forms below match the application Click command definitions.

## `create-project`

```console
deepdanbooru create-project PROJECT_PATH
```

* `PROJECT_PATH` is a directory argument and need not exist.
* The directory is created if missing.
* The command writes `PROJECT_PATH/project.json` with default settings.
* It does not create tags, SQLite data, images, or a model.
* Existing `project.json` is not protected by an application-level overwrite
  check; inspect the destination and back it up before rerunning.

## `download-tags`

```console
deepdanbooru download-tags [OPTIONS] PATH
```

| Option | Default | Required/meaning |
|---|---:|---|
| `--limit INTEGER` | `10000` | Maximum tags for each enabled category. |
| `--minimum-post-count INTEGER` | `500` | Minimum remote post count. |
| `--overwrite` | off | Permit replacement when `tags.txt` exists. |
| `--username TEXT` | none | **Required** Danbooru account name. |
| `--api-key TEXT` | none | **Required** Danbooru API key. |

`PATH` is a directory argument and need not exist. The command makes it, then
contacts Danbooru. Enabled categories are general and character. Outputs are
`tags.txt`, category files when nonempty, `tags_log.json`, and
`categories.json`. Without `--overwrite`, an existing combined `tags.txt`
fails. This is the only setup command in this sub-skill that performs network
I/O; do not run it in an offline or unapproved environment.

## `make-training-database`

```console
deepdanbooru make-training-database [OPTIONS] SOURCE_PATH OUTPUT_PATH
```

| Option | Default | Meaning |
|---|---:|---|
| `--start-id INTEGER` | `1` | Inclusive lower post id. |
| `--end-id INTEGER` | `sys.maxsize` | Inclusive upper post id. |
| `--use-deleted` | off | Include rows with a truthy `is_deleted`; default skips them. |
| `--chunk-size INTEGER` | `5000000` | Source fetch batch size. |
| `--overwrite` | off | Remove an existing output before creation. |
| `--vacuum` | off | Run SQLite `VACUUM` after insertion. |

`SOURCE_PATH` must exist; `OUTPUT_PATH` is expected not to exist. Equal source
and output paths are rejected. The source must provide all eight columns used
by the implementation: `id`, `md5`, `file_ext`, `tag_string`,
`tag_count_general`, `rating`, `score`, and `is_deleted`. The output table has
only the five training columns: `id`, `md5`, `file_ext`, `tag_string`, and
`tag_count_general`.

Rows are fetched in ascending id chunks beginning at `start-id`. Rows above
`end-id` are not inserted. If `is_deleted` is truthy they are skipped unless
`--use-deleted` is set. Ratings `g/s/q/e` append the matching `rating:*` tag;
other rating values append nothing. Score is currently ignored. The command
copies no images and does not apply `minimum_tag_count`.

## Command-line safety notes

All integer options are accepted by Click without the sub-skill adding policy
validation. Use positive `--chunk-size`, a sensible ordered id range, and
review paths before invoking. SQLite output creation is not transactional with
respect to the source: an invalid source or interrupted run can leave a
partial output. Use a new temporary output, validate it, then promote it with
an explicit filesystem operation when reproducibility matters.
