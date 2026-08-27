# Service and REST API Reference

Presidio packages can be used directly from Python or exposed as Flask/Gunicorn HTTP services. Prefer Python APIs for library integration; use services when another process or language needs HTTP endpoints.

## Service map

| Service | Default in-container port | Primary endpoints | Package surface |
| --- | --- | --- | --- |
| Analyzer | `3000` | `GET /health`, `POST /analyze`, `GET /recognizers`, `GET /supportedentities` | `presidio_analyzer` |
| Anonymizer | `3000` | `GET /health`, `POST /anonymize`, `POST /deanonymize`, `GET /anonymizers`, `GET /deanonymizers` | `presidio_anonymizer` |
| Image redactor | `3000` | `GET /health`, `POST /redact` | `presidio_image_redactor` |

Common local host mappings from docs:

```bash
# Analyzer on localhost:5002
docker run -d -p 5002:3000 ghcr.io/data-privacy-stack/presidio-analyzer:latest

# Anonymizer on localhost:5001
docker run -d -p 5001:3000 ghcr.io/data-privacy-stack/presidio-anonymizer:latest

# Image redactor on localhost:5003
docker run -d -p 5003:3000 ghcr.io/data-privacy-stack/presidio-image-redactor:latest
```

Pin a release tag for production rather than relying on `latest`.

## Analyzer service

### Request shape

```json
{
  "text": "John Smith drivers license is AC432223",
  "language": "en",
  "score_threshold": 0.35,
  "entities": ["PERSON", "US_DRIVER_LICENSE"],
  "return_decision_process": false,
  "allow_list": ["ACME"],
  "allow_list_match": "exact"
}
```

`text` may be a string or list. For list input, the service batches with `BATCH_SIZE` and `N_PROCESS` environment variables.

### Example

```bash
curl -s http://localhost:5002/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"John Smith drivers license is AC432223","language":"en"}'
```

Configuration environment variables:

- `ANALYZER_CONF_FILE`
- `NLP_CONF_FILE`
- `RECOGNIZER_REGISTRY_CONF_FILE`
- `BATCH_SIZE`
- `N_PROCESS`
- `LOG_LEVEL`
- `PORT`

## Anonymizer service

### Request shape

```json
{
  "text": "John Smith drivers license is AC432223",
  "anonymizers": {
    "DEFAULT": {"type": "replace", "new_value": "<PII>"},
    "US_DRIVER_LICENSE": {
      "type": "mask",
      "masking_char": "*",
      "chars_to_mask": 4,
      "from_end": true
    }
  },
  "analyzer_results": [
    {"entity_type": "PERSON", "start": 0, "end": 10, "score": 0.85},
    {"entity_type": "US_DRIVER_LICENSE", "start": 30, "end": 38, "score": 0.65}
  ]
}
```

Example:

```bash
curl -s http://localhost:5001/anonymize \
  -H 'Content-Type: application/json' \
  -d '{"text":"John Smith drivers license is AC432223","analyzer_results":[{"entity_type":"PERSON","start":0,"end":10,"score":0.85}],"anonymizers":{"DEFAULT":{"type":"replace","new_value":"<PII>"}}}'
```

REST safety note: the anonymizer service rejects custom lambda operators. Use the Python package API when you need in-process custom functions.

## Image redactor service

`POST /redact` accepts either multipart form upload or JSON containing a base64 image.

Multipart example:

```bash
curl -X POST http://localhost:5003/redact \
  -H 'content-type: multipart/form-data' \
  -F 'image=@input.png' \
  -F 'data={"color_fill":"255"}' \
  > out.png
```

JSON mode accepts an `image` field containing base64 bytes and optional `analyzer_entities`.

The default service path uses Tesseract OCR and the default analyzer model inside the service environment. If the service responds with generic internal errors for valid images, check those prerequisites first.

## When not to use services

Use Python package APIs instead when:

- You need custom Python lambdas or in-process custom operators.
- You need to inject a custom `AnalyzerEngine`, `ImageAnalyzerEngine`, OCR object, or recognizer registry.
- You need direct DataFrame/JSON structured anonymization.
- You do not want long-running processes or container orchestration.

## Verification checklist

1. `curl http://host:port/health` for the target service.
2. Run the smallest endpoint payload for the selected service.
3. For analyzer/image services, verify model/OCR prerequisites in the service environment, not only on the host.
4. For anonymizer, validate span offsets against the exact text sent in the same request.
