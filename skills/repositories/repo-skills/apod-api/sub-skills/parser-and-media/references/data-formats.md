# APOD JSON and media formats

## Single-object response

A normal REST APOD request returns one JSON object. The common shape is:

```json
{
  "date": "2014-10-01",
  "explanation": "...",
  "media_type": "image",
  "service_version": "v1",
  "title": "...",
  "url": "https://..."
}
```

`hdurl` may be present for an image with a high-resolution source, but it is
not guaranteed. `copyright` is also optional; its absence is normal and does
not by itself mean the response is malformed. `thumbnail_url` is optional and
is primarily relevant to video responses when the API request asks for
thumbnails. Other service-level fields documented by the Flask API, such as
`resource`, `concept_tags`, and `concepts`, are not required by the standalone
accessors.

The source `static/default_apod_object.json` is a fallback image-shaped example:
it has `explanation`, `hdurl`, `media_type`, `title`, and `url`, but no `date`,
`service_version`, `copyright`, or `thumbnail_url`. It is therefore useful for
checking optional-key handling, not for asserting that every normal response
has every accessor key.

The minimum keys for the source accessors are:

- `date`
- `explanation`
- `media_type`
- `service_version`
- `title`
- `url`

The inspector reports missing keys rather than guessing defaults. It reports
these fields as optional: `hdurl`, `copyright`, and `thumbnail_url`.

## Count and date-range responses

A request using `count` or a `start_date`/`end_date` range returns a JSON array
of APOD objects. Each element follows the single-object shape, subject to the
same optional fields. The array itself is not a response mapping:

```json
[
  {"date": "2006-04-15", "media_type": "image", "title": "...", "url": "...", "explanation": "...", "service_version": "v1"},
  {"date": "2013-07-22", "media_type": "image", "title": "...", "url": "...", "explanation": "...", "service_version": "v1"}
]
```

Iterate over the list and inspect each element before calling an accessor. Do
not call `get_date(response)` on the list and then interpret its `KeyError` as a
missing date in every item. The bundled inspector emits an index for every
invalid or incomplete element and returns a non-zero status when required keys
are missing.

## Media branching

- `media_type == "image"`: `url` is the normal image asset and `hdurl`, when
  present, is the preferred high-resolution image URL.
- `media_type == "video"`: `url` generally identifies a video or embed. It is
  not a Pillow image input. A `thumbnail_url` may be returned when thumbnail
  behavior was requested and the upstream page supports it; it may be empty or
  absent.
- Any other value should be treated as an unsupported/unknown media case and
  not downloaded blindly.

The HTML scraper in `apod/utility.py` is a different pipeline. Its
`parse_apod(dt, use_default_today_date=False, thumbs=False)` fetches and parses
HTML from the APOD website with BeautifulSoup, constructs a dictionary, and
may derive video thumbnails from YouTube or Vimeo. It is not the JSON response
parser and its network-sensitive behavior, HTML schema assumptions, and
fallback-date option must not be substituted for the REST helper. Route HTML
scraping regressions to [api-service](../../api-service/SKILL.md) or the root
troubleshooting guide as appropriate.
