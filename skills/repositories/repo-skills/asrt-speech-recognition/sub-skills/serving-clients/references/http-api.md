# HTTP JSON API

Use this reference to build clients for ASRT's Flask/Waitress HTTP service. The client helpers in `../scripts/` intentionally avoid importing ASRT; they only read WAV metadata and sample frames with Python's `wave` module and send JSON.

## Endpoints

| Method | Path | Purpose | Request body | Success response |
| --- | --- | --- | --- | --- |
| `GET` | `/` | Return the default HTML page. | None. | HTML, not JSON. |
| `POST` | `/` | Health/ping-style JSON response. | Ignored; `{}` is safe. | JSON with `status_code`, `status_message`, `result`. |
| `POST` | `/speech` | Acoustic model only: WAV samples to pinyin sequence. | Audio payload. | JSON with pinyin list in `result`. |
| `POST` | `/language` | Language model only: pinyin sequence to text. | Language payload. | JSON with text in `result`. |
| `POST` | `/all` | Full pipeline: WAV samples to pinyin, then pinyin to text. | Audio payload. | JSON with text in `result`. |

The server route is `/<level>` for `speech`, `language`, and `all`. Any other one-segment POST path enters the error branch and returns an ASRT JSON client-error status instead of invoking a model.

## Audio payload shape for `/speech` and `/all`

The server expects raw PCM sample frames from inside the WAV file, not the full RIFF/WAVE container. Read the file with `wave.open(...)`, call `readframes(getnframes())`, then URL-safe-base64 encode those bytes and decode the base64 result to JSON text.

Required fields:

```json
{
  "samples": "<urlsafe-base64-text-of-wav-sample-bytes>",
  "sample_rate": 16000,
  "channels": 1,
  "byte_width": 2
}
```

Field details:

- `samples`: URL-safe base64 text for the WAV sample bytes. Send a plain JSON string, not a Python byte-literal string such as `b'...'`.
- `sample_rate`: integer frame rate from the WAV header.
- `channels`: integer channel count from the WAV header.
- `byte_width`: integer sample width in bytes from the WAV header. ASRT's decode helper supports `2` and attempts `4`; other widths raise an error.

## Language payload shape for `/language`

The HTTP language endpoint reads `sequence_pinyin` and passes it to the language model.

```json
{
  "sequence_pinyin": ["ni3", "hao3", "ya5"]
}
```

Use a JSON array of syllable strings. Avoid a comma-separated string unless an outer application explicitly converts it to a list first.

## HTTP JSON response fields

ASRT HTTP responses use these JSON field names:

```json
{
  "status_code": 200000,
  "status_message": "all level",
  "result": "..."
}
```

Observed success messages are `ok` for `POST /`, `speech level` for `/speech`, `language level` for `/language`, and `all level` for `/all`. `result` is an empty string for `POST /`, a pinyin list for `/speech`, and text for `/language` or `/all`.

## Status codes

The server code defines the same ASRT status-code family used by serving clients:

| Code | Meaning |
| --- | --- |
| `200000` | OK / final success. |
| `206000` | Partial OK for streaming; used by gRPC streaming, not ordinary HTTP responses. |
| `400000` | Client error, including unsupported HTTP level/path. |
| `400001` | Client data format error constant. |
| `400002` | Unsupported client configuration constant. |
| `500000` | Server error; HTTP wraps exceptions with this code and `status_message` set to the exception string. |
| `500001` | Server running error constant. |

## Bundled helper usage

Create a payload without sending it:

```bash
python ../scripts/make_http_payload.py --endpoint /speech --wav sample.wav --pretty
python ../scripts/make_http_payload.py --endpoint /language --sequence-pinyin ni3 hao3 ya5 --pretty
```

Call a running HTTP server:

```bash
python ../scripts/asrt_http_client.py health --base-url http://127.0.0.1:20001
python ../scripts/asrt_http_client.py post-root --base-url http://127.0.0.1:20001
python ../scripts/asrt_http_client.py speech --wav sample.wav --base-url http://127.0.0.1:20001
python ../scripts/asrt_http_client.py language --sequence-pinyin ni3 hao3 ya5 --base-url http://127.0.0.1:20001
python ../scripts/asrt_http_client.py all --wav sample.wav --base-url http://127.0.0.1:20001
```

If the response is `500000`, check [Troubleshooting](troubleshooting.md) before changing the client request shape.
