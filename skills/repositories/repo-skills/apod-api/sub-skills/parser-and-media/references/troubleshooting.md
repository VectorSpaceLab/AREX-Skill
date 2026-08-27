# Parser and media troubleshooting

## `KeyError` for a response field

The source accessors use direct indexing and raise `KeyError` when a key is
absent. First run the offline inspector and identify whether the input is a
single object, a list, or an error envelope. Required fields are `date`,
`explanation`, `media_type`, `service_version`, `title`, and `url` for the
source accessor set. Handle `hdurl`, `copyright`, and `thumbnail_url` as
optional. A response can be valid without any one of those optional keys.

If the input is a list from `count` or a date range, iterate over elements. If
it is an API error object, do not pass it to the APOD accessors; route query,
credential, and Flask response issues to [api-service](../../api-service/SKILL.md).

## Historical parser spelling

Use `get_explaination(response)` when compatibility with the shipped helper or
its README is required. `get_explanation` is not a source export. A caller may
wrap the historical name in a correctly spelled application-level function,
but a skill instruction that claims the source has `get_explanation` is wrong.

## Missing `hdurl`

`hdurl` is conditional. Fall back to `url` only after confirming
`media_type == "image"` and deciding that standard resolution is acceptable.
Do not manufacture an HD URL by changing a filename. The fallback object in
`static/default_apod_object.json` demonstrates that response completeness can
vary.

## Video or missing thumbnail

A video `url` is not a Pillow-readable image. `thumbnail_url` is optional and
may be absent even when `media_type` is `video`; the service/API request must
be configured to ask for thumbnails where supported. Do not scrape or guess a
thumbnail URL in the REST parser route. If the task needs the HTML scraper's
YouTube/Vimeo thumbnail heuristics, route to the distinct `parse_apod` path and
expect live network sensitivity.

## Downloader refuses to write

The bundled downloader requires `--output-dir` and refuses an existing file by
default. Choose a new filename or make the replacement decision explicit with
`--overwrite`. It rejects path separators in `--filename` so a URL or caller
cannot escape the selected output directory. Use `--dry-run` to diagnose URL,
filename, and destination validation without a request.

The source `download_image(url, date)` should not be used as a safety model: it
checks for `<date>.png` but writes `<date>.jpg`, has no output directory or
status/timeout checks, and can save non-image/video bytes under a JPEG name.

## Pillow conversion fails

Check that the input is a real local image and that Pillow is installed. A
video, HTML error page, truncated download, or JSON response is not a valid
image. The safe converter requires an explicit output path, requires a `.png`
suffix, rejects same-file output and accidental overwrite, and reports Pillow
errors without deleting the source. Add `--overwrite` only after confirming
the destination is intentional.

## Network, credentials, and scraper confusion

`get_data` and downloads need external network access. An API key is required
for `get_data`; concept tagging in the Flask service is credential-bound to the
legacy `alchemy_api.key` credential and is disabled when that credential is
unavailable. No credential belongs in this runtime skill. HTTP failures, rate
limiting, or
NASA/APOD downtime should be diagnosed at the network/service boundary rather
than “fixed” by changing JSON keys.

`apod.utility.parse_apod` is an HTML scraper using Requests, urllib3, and
BeautifulSoup. It is distinct from the standalone JSON parser and can fail on
HTML layout changes, dates, or video thumbnail providers. Its live regression
is network-sensitive and may be skipped. For endpoint/startup behavior use
[api-service](../../api-service/SKILL.md); for installation and deployment use
[deployment-and-operations](../../deployment-and-operations/SKILL.md).
