# Tags files and tag download

## Offline `tags.txt` contract

`tags.txt` should be a UTF-8 text file with one model vocabulary tag per line.
The project loader strips surrounding whitespace and ignores blank lines, then
preserves the remaining order. Use a stable, duplicate-free list with no
internal spaces:

```text
1girl
ahoge
long_hair
rating:general
rating:sensitive
```

`create-project` does not create this file. A manually curated file is valid;
review its spelling against each row's space-separated `tag_string`. Duplicate
or whitespace-padded lines are accepted by the low-level loader after
normalization but are a likely modeling/configuration error. Check them with:

```console
python scripts/validate_tags_txt.py PROJECT_PATH/tags.txt
python scripts/validate_tags_txt.py PROJECT_PATH/tags.txt --require-system-tags
```

The `--require-system-tags` option is useful after database conversion, because
that converter appends the four rating tags. It is not mandatory for every
custom vocabulary.

## Network command

The exact public command is:

```console
deepdanbooru download-tags PROJECT_PATH \
  --limit 10000 --minimum-post-count 500 \
  --username DANBOORU_USERNAME --api-key DANBOORU_API_KEY
```

The command requires both credential options and requests the Danbooru
`tags.json` endpoint. There is no offline/dry-run mode in the application CLI;
the generated validation scripts intentionally do not call it. Treat a request
to use this command as an explicit network and credential boundary.

Before running it:

* confirm the user wants current remote tags rather than a checked-in or
  manually curated vocabulary;
* use an approved credential-handling method and avoid copying secrets into
  logs, fixtures, or skill files;
* confirm the project directory and whether replacing its tag file is allowed;
* preserve a backup of existing files if reproducibility matters.

If no network request is authorized, stop at a curated local `tags.txt` and
report that remote freshness was not verified. Do not substitute fabricated
remote data.

## Files and ordering produced by the implementation

The command downloads only the enabled `general` and `character` categories.
For each category it writes:

* `tags-general.txt` (when at least one tag is returned),
* `tags-character.txt` (when at least one tag is returned), and
* the combined `tags.txt`.

The combined file contains naturally sorted general tags, then naturally
sorted character tags, followed by these system tags in this exact order:

```text
rating:general
rating:sensitive
rating:questionable
rating:explicit
```

It also writes `tags_log.json` with the timestamp, limit, and minimum post
count, and `categories.json` with web-category start indexes. Tags named
`loli`, `shota`, and `toddlercon` are filtered from downloaded responses.
Artist and copyright category blocks exist in source history but are disabled
by the current command and should not be promised.

`--limit` applies per enabled category before the combined system tags are
added. `--minimum-post-count` is sent as the post-count filter. The remote
response and authentication behavior are external dependencies; local scripts
can validate only the resulting file syntax.

## Overwrite and recovery behavior

Without `--overwrite`, an existing `tags.txt` causes a failure before the
combined file is opened. With `--overwrite`, the command replaces the combined
file and can replace category files. It may write the log and category metadata
as part of the run, so keep a backup if the current vocabulary is valuable.
If a network request fails partway through, keep the prior known-good
vocabulary, inspect the resulting files, and retry only after diagnosing the
network/authentication issue. A failed or empty category is not proof that the
Danbooru category is empty; it may reflect a request or credential problem.
