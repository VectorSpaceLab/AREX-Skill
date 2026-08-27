# Flask service API reference

## Service identity and routes

The declared distribution is `apod-api` version `1.1.0` and requires Python
`>=3.12`. The Flask application reports service version `v1`; the primary
route is therefore the exact, trailing-slash URL `GET /v1/apod/`.

| Request | Normal result | Behavior |
|---|---:|---|
| `GET /` | `200 text/html` | Renders the home page from `home.html`, including the service version, host, endpoint name, and a short usage example. |
| `GET /static/<asset_path>` | `200` when present | Serves an application static asset. A missing asset falls through to the JSON 404 handler. |
| `GET /v1/apod/` | `200 application/json` | Returns one APOD object, a random-count array, or a date-range array. |
| Any other unmapped URL | `404 application/json` | Uses the custom error envelope described below. |

Use the trailing slash in client code. Flask may redirect a no-slash request
such as `/v1/apod` before the handler runs; clients that do not follow
redirects should treat the documented `/v1/apod/` form as canonical.

Flask-CORS is enabled for `/*`. Cross-origin requests are allowed by the
application configuration, and the service exposes `X-RateLimit-Limit` and
`X-RateLimit-Remaining` if those headers are supplied by the serving stack.
CORS does not make the APOD upstream available when that site is down.

Flask also registers its default static rule in addition to the explicit
`/static/<asset_path>` handler, so route inspection can show both
`/static/<asset_path>` and `/static/<path:filename>`. They target the same
static directory; use the simple `/static/<asset>` URL in client examples.

## Query fields

The implementation accepts only these field names:

- `date`
- `count`
- `start_date`
- `end_date`
- `concept_tags`
- `thumbs`
- `hd`

An unknown field causes `400` before APOD scraping. In particular, the README
shows an `api_key` in examples copied from NASA's separate JSON API, but this
Flask service does **not** accept or forward `api_key`; sending it produces the
unknown-field 400 response.

### Date and selection rules

Dates must use `YYYY-MM-DD`. The accepted inclusive lower bound is `1995-06-16`.
The upper bound is the service process's current local date; tomorrow and later
are rejected. The following are the implemented selection modes:

| Query shape | Result |
|---|---|
| No `count`, `start_date`, or `end_date`, with optional `date` | One object. Omitting `date` asks for the current APOD page. |
| `count` only, with optional `concept_tags`/`thumbs`/`hd` | A JSON array of randomly selected dates. `count` is an integer from 1 through 100. |
| `start_date`, with optional `end_date` and flags | A JSON array covering the inclusive range. Omitting `end_date` uses the current date. `start_date` cannot be after `end_date`. |

These combinations are rejected with `400 Bad Request: invalid field
combination passed.`:

- `date` together with `count`;
- `date` together with `start_date` or `end_date`;
- `count` together with either range field;
- `end_date` without `start_date`;
- any other mixture that does not match one of the three modes.

`count` is converted with Python integer parsing. Non-integer text, zero, and
values above 100 are 400-level input errors. A range request can return an
empty or partial array when individual APOD pages have no usable data; that is
not the same response shape as a single-date no-data result.

### Boolean and legacy flags

Only `concept_tags` and `thumbs` are boolean-validated. Missing values become
`False`. Query strings are accepted case-insensitively only when their value is
exactly `true` or `false` (for example, `?thumbs=True`). Values such as `1`,
`yes`, or an empty string cause:

```text
400 Bad Request: concept_tags and thumbs must be boolean values.
```

`hd` is an allowed legacy field, but the current handler neither validates nor
uses its value. High-resolution URLs are returned whenever the scraped APOD
page supplies one, regardless of `hd`.

`concept_tags=true` asks for a `concepts` field. If the credential-bound
Alchemy integration is unavailable, the response instead contains the literal
message value `concept_tags functionality turned off in current service`.
The ordinary APOD request does not require that credential.

## Successful response shapes

A single-date response is a JSON object. The exact fields depend on the APOD
HTML page, but commonly include:

- `date`, `title`, `explanation`, `media_type`, and `url`;
- `hdurl` when a high-resolution link exists;
- `copyright` when the page exposes one;
- `thumbnail_url` for a video when `thumbs=true` and a thumbnail can be found;
- `concepts` only when concept tagging was requested (or its disabled message);
- `service_version`, normally `"v1"`.

The service adds `service_version` after scraping. The source parser does not
promise a `concept_tags` reflection field even though older README examples
show one; rely on fields actually present in the JSON response.

`count` and range modes return a JSON array of these objects. Random mode skips
individual dates without usable data until it reaches the requested count or
runs out of candidate dates. Range mode similarly skips unusable pages.

A bundled static fixture, `static/default_apod_object.json`, documents a
fallback-looking object with `title: "Default Image"`, `media_type: "image"`,
`url`, `hdurl`, and an explanation. It is available as a static asset at
`/static/default_apod_object.json`; it is **not** automatically substituted for
an upstream failure by the current API path. The corresponding default image
is a separate static asset.

## Error envelope and status semantics

Errors are JSON objects with this common shape:

```json
{"service_version": "v1", "msg": "...", "code": 400}
```

The `code` field mirrors the HTTP status. The message may include the allowed
field list for handler-generated usage errors.

| Status | Typical cause | Message behavior |
|---:|---|---|
| `400` | Unknown query field, invalid boolean, invalid combination, malformed/out-of-range date, reversed range, or invalid count | Describes the input error; unknown-field, boolean, combination, and custom 404 usage paths append the allowed-field text. |
| `404` | Unmapped route, missing static asset, or no single-date data | Unmapped routes use `Sorry, Nothing at this URL.`; a single-date no-data response uses `No data available for date: ...`. |
| `500` | Scraper/parser exception, upstream request failure, or failing concept-tag request | Uses `Internal Service Error` for handler failures, without the usage suffix. |

Malformed input is rejected before the backing APOD request in the normal
handler path. A network or HTML-schema failure is therefore not evidence that
the query was malformed; inspect the status and logs separately.
