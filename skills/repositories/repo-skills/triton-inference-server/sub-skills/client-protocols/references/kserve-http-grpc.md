# KServe HTTP and gRPC

## Common endpoints

- `GET /v2/health/live`
- `GET /v2/health/ready`
- `GET /v2/models/<model>/ready`
- `GET /v2/models/<model>/config`
- `GET /v2/models/<model>` metadata via HTTP/REST
- Inference endpoints under `/v2/models/<model>/infer` for HTTP and the equivalent gRPC inference API.

## Request shape reminders

- The request tensor name must match the model's input name.
- Shape and datatype must match repository/config expectations.
- `parameters` are used for protocol-specific extensions such as binary body sizes.
- BYTES payloads are encoded differently from numeric tensors.
- Binary payloads and shared-memory payloads change how the body or data buffer is built, but they do not replace correct tensor metadata.

## Status and error mapping

Triton maps model/server errors to HTTP and gRPC status codes. When a request fails, the first diagnosis step is to decide whether the failure is:

- bad endpoint or missing server readiness,
- request format/shape/datatype mismatch,
- repository/config mismatch,
- model/backend runtime failure,
- or a transport/security restriction.

## Safe request-building rule

Use a request descriptor helper to construct the JSON or client call first. Then validate it against repository metadata or config before sending it to a live server.
