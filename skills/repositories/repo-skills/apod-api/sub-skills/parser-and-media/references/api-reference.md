# Parser and media API reference

## Prerequisites

The standalone helper uses `requests` and Pillow. Install the public project
runtime dependencies through the repository's supported environment workflow;
for this route the relevant packages are `requests` and `pillow`. The helper
also imports `json` and `os` from the standard library. Live `get_data` and
asset downloads need outbound HTTPS access to the selected NASA/APOD URL.
Never put an API key in a skill, command history copied into a report, fixture,
or script. Acquire and pass credentials through the caller's protected runtime
configuration when the live NASA API is intentionally used.

The declared package targets Python `>=3.12`. The repository's current
flat-layout metadata is not safely editable-installable with default setuptools
package discovery: top-level `apod`, `apod_parser`, `static`, `templates`, and
`skills` are ambiguous. That packaging fact is a deployment/install concern,
not a reason to copy the source module into a runtime skill.

## Exact standalone helper signatures

The helper exports these source-compatible call signatures:

```python
get_data(api_key)
get_date(response)
get_explaination(response)  # historical spelling is intentional
get_hdurl(response)
get_media_type(response)
get_service_version(response)
get_title(response)
get_url(response)
download_image(url, date)
convert_image(image_path)
```

`get_data(api_key)` performs a live `GET` of NASA's planetary APOD endpoint with
`api_key` as the query value, reads `.text`, parses JSON, and returns the
result. It does not validate HTTP status, normalize a list, or hide malformed
JSON. Call it only when live access and a protected key are available. The
other accessors take one mapping and use direct `response["..."]` indexing:

| Function | Indexed key | Typical value |
|---|---|---|
| `get_date` | `date` | `YYYY-MM-DD` string |
| `get_explaination` | `explanation` | text string |
| `get_hdurl` | `hdurl` | high-resolution image URL |
| `get_media_type` | `media_type` | `image` or `video` |
| `get_service_version` | `service_version` | service version string |
| `get_title` | `title` | title string |
| `get_url` | `url` | primary image/video URL |

A missing key therefore raises `KeyError`; it is not converted into `None`.
Check the response shape first with `inspect_apod_response.py` and use
`response.get("hdurl")` or an equivalent explicit optional-key branch for
optional fields.

`download_image(url, date)` is retained as source evidence only. Its
implementation downloads bytes with `requests.get` and writes a date-derived
JPEG in the process directory. Its existence check tests `<date>.png` but
writes `<date>.jpg`, so an existing JPEG can be replaced and a non-image URL
can be saved as if it were a JPEG. It also has no timeout, status check, output
root, path sanitization, or video guard. Do not present it as safe; use the
bundled downloader instead.

`convert_image(image_path)` opens the local path with `PIL.Image.open` and
saves a same-directory `.png` based on the input basename. It does not protect
against replacement, verify that the destination is distinct, or offer an
explicit destination. Use the bundled converter when safety and reproducible
output paths matter.

## Related service APIs

The Flask service has a separate endpoint and query contract. Route endpoint
construction belongs to [api-service](../../api-service/SKILL.md), not this
route. The service can return one object or an array for `count` and date-range
queries; accessors above are designed for one mapping and will fail or be
meaningless if handed the array itself.
