# Parser and media workflows

## 1. Inspect before indexing

Use the offline inspector against a saved JSON fixture or stdin. It never makes
network calls:

```bash
python skills/disco/apod-api/sub-skills/parser-and-media/scripts/inspect_apod_response.py response.json
cat response.json | python skills/disco/apod-api/sub-skills/parser-and-media/scripts/inspect_apod_response.py - --field date --field media_type
```

The command identifies a single object versus a count/range list, prints
required-key gaps, reports optional-key presence, and can print selected field
values. Treat a non-zero exit as a fixture/response validation failure. A list
with one bad element is not safe to pass through the source accessors.

For Python callers that already have a validated single mapping:

```python
from apod_parser import apod_object_parser

response = ...
when = apod_object_parser.get_date(response)
summary = apod_object_parser.get_explaination(response)  # historical spelling
media_type = apod_object_parser.get_media_type(response)
asset_url = response.get("hdurl") or apod_object_parser.get_url(response)
```

Use `.get("hdurl")` deliberately because high-resolution imagery is optional.
Use the required accessors only after the required-key diagnostic succeeds.

## 2. Choose an asset explicitly

For images, choose `hdurl` when present and wanted; otherwise choose `url`. For
videos, do not infer that `url` is an image. Select `thumbnail_url` only when
present and the caller specifically requested a thumbnail. Confirm the media
branch before downloading.

The safe downloader makes the output directory and replacement policy explicit:

```bash
python skills/disco/apod-api/sub-skills/parser-and-media/scripts/download_apod_asset.py \
  'https://example.invalid/apod.jpg' \
  --output-dir ./apod-assets \
  --filename 2024-01-01.jpg \
  --dry-run
```

Remove `--dry-run` only when network access is intended. The script warns that
it performs a live request, accepts only `http`/`https`, streams bytes, checks
HTTP status, refuses an existing destination by default, and supports
`--overwrite` only as an explicit choice. A dry run is useful for deterministic
argument/path checks without contacting NASA or another host.

## 3. Convert a local image

Conversion is local and requires Pillow. Supply a distinct PNG destination:

```bash
python skills/disco/apod-api/sub-skills/parser-and-media/scripts/convert_apod_image.py \
  ./apod-assets/2024-01-01.jpg \
  --output ./apod-assets/2024-01-01.png
```

The converter checks that the input exists and is a regular file, refuses an
existing output unless `--overwrite` is present, rejects an output equal to the
input, and writes PNG through Pillow. It does not fetch URLs and cannot convert
a video or an HTML page. Keep the original until the output has been checked.

## 4. Use the source helper only for compatibility

If an existing caller requires `get_data(api_key)` or the historical accessor
names, preserve that interface and handle its direct `KeyError`/network/JSON
failures at the caller boundary. The source `download_image` and
`convert_image` functions document historical behavior but are intentionally
not the default safety path. The adapted scripts avoid their process-directory
and overwrite quirks.

## 5. Verification probes

Whole-skill integration can use a native `parser-module-import` probe to confirm
that the standalone module imports and exposes the exact historical signatures;
native tests are intentionally deferred until the integrated graph and prepared
environment are available. Keep `utility-live-html-regression` optional because
it needs live APOD HTML and may be skipped when the network or upstream markup is
unavailable.

Useful synthetic cases go beyond a happy-path object:

- inspect a two-element list where one element lacks `hdurl` and confirm the
  list shape is reported while required-key diagnostics remain per element;
- create a tiny local RGB image, convert it to PNG, then rerun without
  `--overwrite` and confirm the existing output is refused.

## 6. Keep HTML scraping separate

`apod.utility.parse_apod(...)` is an HTML scraper. It fetches APOD website HTML,
uses BeautifulSoup, distinguishes image/iframe/HTML5 video markup, and may
request a YouTube/Vimeo thumbnail. Use it only for a task explicitly about the
website HTML compatibility path. Do not pass its result assumptions back into
the standalone REST JSON parser without validating the mapping. Its live
regression candidate is network-sensitive and may be skipped.
