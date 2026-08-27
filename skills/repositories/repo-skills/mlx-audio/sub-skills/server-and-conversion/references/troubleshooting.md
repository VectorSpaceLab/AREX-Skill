# Server and Conversion Troubleshooting

## Missing Server Dependencies

Symptoms:

- `fastapi` missing
- `uvicorn` missing
- `python-multipart` missing
- `webrtcvad` missing or warning about `pkg_resources`

Fixes:

- install the `server` extra
- keep `setuptools<81` for the server and STS extras
- use the root install script to confirm the dependency surface first

## Server Startup or Routing Errors

Symptoms:

- 404 or 500 while loading a model
- an OpenAI client points at the wrong base URL
- websocket routing or turn detection behaves unexpectedly

Fixes:

- confirm the model id and the endpoint path
- check the model-selection order for realtime routes
- verify that the client and server agree on the response format and audio sample rate

## CORS and UI Issues

Symptoms:

- browser requests are blocked
- Studio UI does not start
- the user expects a different host or port

Fixes:

- set the allowed origins list explicitly
- confirm the host and port arguments
- treat UI launch as separate from API availability

## Conversion Flag Problems

Symptoms:

- quantize and dequantize are mixed
- the wrong domain is inferred
- the output directory is not what the user expects

Fixes:

- use the command builder to print the final command first
- choose one of quantize, dequantize, or dtype-only conversion
- force the model domain when auto-detection is ambiguous
