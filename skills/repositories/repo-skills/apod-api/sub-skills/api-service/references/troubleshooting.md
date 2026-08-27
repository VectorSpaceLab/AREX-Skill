# Service troubleshooting

Start by separating **input validation**, **route/static lookup**, and
**backing APOD access**. They have different status codes and recovery steps.

## Fast diagnosis table

| Observation | Likely cause | Action |
|---|---|---|
| Launcher help exits without app output | Normal help path | No network should have occurred. Use `--inspect-routes` for an import-only check. |
| Route inspection cannot import `application` | Dependencies are absent, or the command was not launched with the project root on `sys.path` | Run the supported dependency setup, then retry from the project root. Do not use the broken default editable-install path. |
| Port bind error | Another local process owns the selected port | Stop that process or choose another explicit port; rerun the bounded wrapper. |
| `308`/redirect for `/v1/apod` | Missing endpoint trailing slash | Use `/v1/apod/` or configure the client to follow redirects. |
| `400` with allowed-field text | Unknown field, invalid boolean, or invalid selection combination | Remove `api_key` and other unknown names; use only the fields and combinations in `api-reference.md`. |
| `400` with a date/count message | Date parse/range or count validation failed | Use `YYYY-MM-DD`, dates from `1995-06-16` through the service's current date, and `1 <= count <= 100`. |
| `404` with `Sorry, Nothing at this URL.` | Route or static asset does not exist | Check the exact path, including `/v1/apod/` and the static asset name. |
| `404` with `No data available for date: ...` | Explicit single-date scrape returned no usable APOD data | Confirm the date and APOD availability; this is not fixed by adding `api_key`. |
| `500 Internal Service Error` | APOD request failed, the upstream HTML no longer matches the scraper, or concept tagging failed | Check external connectivity and logs, retry with `concept_tags=false`, and distinguish upstream failure from input errors. |
| `200` with a partial/empty array | Count or range mode skipped pages with no usable data | Inspect the requested dates and upstream availability; list modes do not convert every missing page into a top-level 404. |

## Input failures happen before scraping

The handler first checks field names, then validates `concept_tags` and `thumbs`,
then chooses one selection mode. These examples must be rejected with `400`:

```text
/v1/apod/?date=2014-10-01&count=2
/v1/apod/?date=2014-10-01&start_date=2014-10-01
/v1/apod/?end_date=2014-10-02
/v1/apod/?thumbs=1
/v1/apod/?count=0
```

The error body is JSON with `service_version`, `msg`, and `code`. The
unknown-field, boolean, and combination messages append the allowed-field
usage text; date and count `ValueError` messages do not necessarily append it.
`hd` is a legacy accepted field and is not boolean-validated, but it does not
change the returned high-resolution URL behavior.

The README's NASA JSON API examples include `api_key`; that field is not in the
Flask service's allowed list. A 400 for `api_key` is correct for this service.

## APOD upstream outages and parser drift

The service fetches `https://apod.nasa.gov/apod/` pages with the scraper in the
runtime application. It does not use NASA's JSON API key flow. DNS/TLS errors,
connection failures, upstream HTTP behavior, and HTML schema changes can all
make a page unparsable. The scraper also has no explicit request timeout, so a
client should set `--max-time`/an equivalent timeout and avoid broad range
requests during diagnosis.

Use this distinction:

1. Retry a known-good, historical date with `concept_tags=false` and a short
   client timeout. If it returns 400, the query is malformed; fix the query.
2. If a valid date reaches the scraper and raises, the handler normally returns
   500. This indicates an upstream/network/parser problem, not an input fix.
3. If APOD returns a 404 for the requested historical page, the single-date
   path can return a service 404 saying no data is available.
4. In count/range modes, unusable individual pages are skipped, so an empty or
   partial 200 array is possible.

Native HTML regression tests are network-sensitive and are deferred until
whole-skill integration. Do not claim an offline test has proved current APOD
HTML compatibility.

## Today behavior, fallback, and cache limits

The module keeps a process-local `RESULTS_DICT` cache. Keys vary by APOD date,
`concept_tags`, and `thumbs`; the cache is volatile, has no persistence or
invalidation policy, and is not shared across workers or restarts. A cached
object can therefore make a repeated request avoid a fresh upstream scrape,
while a new process starts empty.

When no `date` is supplied, the API asks the utility to scrape the current
`astropix.html` page and marks the request as a default-today lookup. The
utility's previous-day retry is only effective when it has a concrete date;
the omitted-date path passes `None`, so do not promise that a current-page
outage will automatically fall back. Random and range modes pass concrete
current-date values and may invoke the utility's previous-day attempt, but a
range still filters data whose returned date does not match the requested day.

`static/default_apod_object.json` and its image are static assets. The older
fallback-loading code is not active in the current utility path. Do not tell a
client that an upstream outage will return the default fixture; diagnose the
actual 404/500 response instead.

## Concept tags and credentials

The application looks for a local `alchemy_api.key` at process startup. Without
that credential, `concept_tags=true` remains a successful request but the
`concepts` field says `concept_tags functionality turned off in current
service`. With a credential, an additional external Alchemy request is made;
its failure can surface as a 500. Never copy, print, or embed the credential in
skill content or troubleshooting output. If concept tags are not essential,
retry with `concept_tags=false` to isolate APOD scraping from the optional
integration.

## CORS, root, and static checks

CORS is configured broadly for application routes and exposes two optional
rate-limit headers. A CORS response does not imply that the body was produced
successfully; inspect the HTTP status and JSON envelope as well.

If `/` returns a template error, verify that the runtime is launched with the
application's templates available. If only `/static/default_apod_object.json`
fails, verify the static asset installation separately. The custom 404 handler
returns JSON for missing pages, so an HTML 404 usually indicates a proxy or
other server in front of this Flask application.
