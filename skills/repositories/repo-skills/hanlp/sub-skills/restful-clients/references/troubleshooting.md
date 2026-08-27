# RESTful Troubleshooting

- `400 Bad Request`: unsupported language/task, text too long, or incompatible payload.
- `401 Unauthorized`: missing/invalid auth; pass `auth` or set `HANLP_AUTH`.
- `422 Unprocessable Entity`: JSON body or content type cannot be parsed.
- `429 Too Many Requests`: rate limit or quota exceeded.
- Timeout/SSL errors: endpoint, network, proxy, `timeout`, or `verify` issue.

Payload checks: `text` may be a string or list of strings; `tokens` must be `list[list[str]]`; at least one of `text` or `tokens` is required. Build payloads locally with `scripts/restful_payload_preview.py` before debugging live service behavior.
