---
name: parser-and-media
description: "Parse NASA APOD JSON with the standalone helper, inspect optional
  media fields, and safely download or convert an explicitly requested asset."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Parser and media

Use this route when the input is already NASA APOD JSON or when a caller has
explicitly asked for one media asset. Start with the bundled offline inspector;
then use the downloader or Pillow converter only when the corresponding
operation is requested. The parser helper is a convenience module, not a Flask
endpoint client and not the HTML scraper.

- [API signatures and prerequisites](references/api-reference.md)
- [Response shapes and optional keys](references/data-formats.md)
- [Safe inspection, download, and conversion workflows](references/workflows.md)
- [Parser/media troubleshooting](references/troubleshooting.md)
- For Flask routes, query parameters, or server startup, use [api-service](../api-service/SKILL.md).
- For uv, Gunicorn, Docker, or bounded load operations, use [deployment-and-operations](../deployment-and-operations/SKILL.md).
- For shared service failures, see the [root troubleshooting route](../../references/troubleshooting.md).

## Route rules

1. If the value is a JSON object or array from NASA's REST APOD API, inspect it
   with `scripts/inspect_apod_response.py` or use the exact accessors below.
2. If a required key is absent, diagnose the shape before indexing. `hdurl`,
   `copyright`, and `thumbnail_url` are optional in real responses.
3. Download only after the caller supplies an intended URL and destination.
   Prefer `scripts/download_apod_asset.py`; it requires an output directory,
   refuses accidental replacement, and makes network use visible.
4. Convert only a local image with `scripts/convert_apod_image.py`; it requires
   an explicit PNG destination and refuses overwrite unless explicitly enabled.
5. A video URL is not an image. Do not send it to Pillow. Use
   `thumbnail_url` only when the response supplies it (normally after the API
   request asks for thumbnails), and treat thumbnail availability as a caveat.

The source helper retains the historical misspelling `get_explaination`; do not
silently rename it when reproducing existing caller code. Detailed source
compatibility notes and safer adaptations are in the references.
