# Dataset format

DeepDanbooru discovers records from a SQLite file and derives image paths; it
does not use a separate manifest. The SQLite file may have any filename, but it
must be in the same directory as `images/`.

## Directory and filename rule

```text
DATASET/
├── images/
│   ├── 00/
│   │   └── 00000000000000000000000000000000.jpg
│   ├── 01/
│   │   └── 0100000000000000000000000000000000.png
│   └── ff/
│       └── ff000000000000000000000000000000.jpeg
└── any-name.sqlite
```

For a `posts` row, the loader constructs:

```text
DATASET/images/<md5 first two characters>/<md5>.<file_ext>
```

The value need not be a cryptographic MD5. It is used literally as the file
stem and first-two-character directory name. Keep it at least two characters,
avoid path separators, and use the exact extension text stored in SQLite.
Training record selection accepts only `png`, `jpg`, and `jpeg`; other
extensions are ignored by the loader.

## Required training schema

The converted/training database must contain a table named `posts` with at
least these columns:

| Column | Expected kind | Meaning |
|---|---|---|
| `id` | INTEGER, primary key | Stable ordering and row identity. |
| `md5` | TEXT | Image stem and directory prefix source. |
| `file_ext` | TEXT | Lowercase `png`, `jpg`, or `jpeg` for eligible images. |
| `tag_string` | TEXT | Space-separated tags, for example `1girl ahoge long_hair`. |
| `tag_count_general` | INTEGER | Compared with `minimum_tag_count`. |

The source database used by `make-training-database` must additionally contain:

```text
rating TEXT
score <numeric or compatible SQLite value>
is_deleted <integer/boolean-compatible value>
```

The converter selects source columns `id, md5, file_ext, tag_string,
tag_count_general, rating, score, is_deleted`. It creates a new `posts` table
with only the five training columns above. `score` is read but currently not
turned into a system tag.

## Selection and tags

The dataset loader executes the equivalent of:

```sql
SELECT md5, file_ext, tag_string
FROM posts
WHERE (file_ext = 'png' OR file_ext = 'jpg' OR file_ext = 'jpeg')
  AND (tag_count_general >= ?)
ORDER BY id;
```

The parameter is `project.json`'s `minimum_tag_count`. A row can pass the SQL
filter and still fail later because its derived image file is absent or not a
decodable image. A high threshold can legitimately produce zero records; use a
small, intentional threshold for a smoke test rather than silently changing
production settings.

`tag_string` is split downstream on spaces. Keep tags in the same spelling as
`tags.txt`; do not encode a multi-word tag as literal spaces. Rating system tags
are appended by the converter as `rating:general`, `rating:sensitive`,
`rating:questionable`, or `rating:explicit`.

## Source versus converted database

A source Danbooru-like export normally has the five training columns plus
`rating`, `score`, and `is_deleted`. Run the read-only checker in source mode
before conversion:

```console
python scripts/validate_danbooru_sqlite.py SOURCE.sqlite --mode source
```

Then create a new file and validate the result:

```console
deepdanbooru make-training-database SOURCE.sqlite TRAINING.sqlite
python scripts/validate_danbooru_sqlite.py TRAINING.sqlite --mode training
```

Do not point output at source. Existing output is preserved unless
`--overwrite` is explicitly passed; that flag removes the output before any
new table is created. The converter does not copy images, check that images
exist, or supply `tags.txt`.

## Read-only layout checks

The bundled SQLite checker can optionally inspect derived image paths without
modifying the database:

```console
python scripts/validate_danbooru_sqlite.py TRAINING.sqlite \
  --check-images --dataset-root /path/to/DATASET
```

Use `--minimum-tag-count N` with this optional check to match the project
threshold. Missing image paths are reported as failures; unsupported
extensions and below-threshold rows are reported as skipped rather than
silently treated as valid training data.
