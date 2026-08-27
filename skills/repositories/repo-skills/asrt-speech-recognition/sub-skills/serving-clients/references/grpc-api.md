# gRPC API

Use this reference when integrating a gRPC client with ASRT. The authoritative service contract comes from `assets/asrt.proto`; this sub-skill records the exact service, methods, messages, and status-code semantics needed by a client.

## Package and service

```proto
syntax = "proto3";
package asrt;

service AsrtGrpcService {
  rpc Speech (SpeechRequest) returns (SpeechResponse) {}
  rpc Language (LanguageRequest) returns (TextResponse) {}
  rpc All (SpeechRequest) returns (TextResponse) {}
  rpc Stream (stream SpeechRequest) returns (stream TextResponse) {}
}
```

Methods:

- `Speech`: unary request/response. Sends WAV samples and receives a repeated pinyin result.
- `Language`: unary request/response. Sends pinyin syllables and receives text.
- `All`: unary request/response. Sends WAV samples and receives final recognized text.
- `Stream`: bidirectional streaming. Sends a stream of `SpeechRequest` chunks and receives a stream of `TextResponse` partial/final text updates.

## Messages

```proto
message SpeechRequest {
  WavData wav_data = 1;
}

message SpeechResponse {
  int32 status_code = 1;
  string status_message = 2;
  repeated string result_data = 3;
}

message LanguageRequest {
  repeated string pinyins = 1;
}

message TextResponse {
  int32 status_code = 1;
  string status_message = 2;
  string text_result = 3;
}

message WavData {
  bytes samples = 1;
  int32 sample_rate = 2;
  int32 channels = 3;
  int32 byte_width = 4;
}
```

`WavData.samples` is raw WAV sample-frame bytes, not base64 text and not the whole WAV container. Populate `sample_rate`, `channels`, and `byte_width` from the WAV header so the server can reshape/decode samples consistently.

## Expected client construction

A Python gRPC client normally needs generated modules equivalent to `asrt_pb2.py` and `asrt_pb2_grpc.py`, then constructs an `AsrtGrpcServiceStub` against host/port `127.0.0.1:20002` or the configured service endpoint.

Generation pattern:

```bash
python -m grpc_tools.protoc -I proto-dir --python_out=generated-dir --grpc_python_out=generated-dir proto-dir/asrt.proto
```

Keep the generated stubs and the runtime `grpcio`/`protobuf` versions compatible. If imports fail, regenerate the stubs from the same proto used by the server and adjust package paths before debugging model code.

## Status codes

| Code | Meaning | Serving notes |
| --- | --- | --- |
| `200000` | OK / final success. | Used by unary methods and final stream responses. |
| `206000` | Partial OK. | Used by `Stream` for intermediate partial text. |
| `400000` | Client error. | Defined for malformed/unsupported requests. |
| `400001` | Client data format error. | Defined for request format failures. |
| `400002` | Unsupported client configuration. | Defined for unsupported metadata/configuration. |
| `500000` | Server error. | General server-side exception status. |
| `500001` | Server running error. | Defined for runtime serving failures. |

The implemented gRPC methods directly return success statuses when model calls complete. Transport-level errors, import errors, generated-stub mismatches, or model-load failures usually surface before a structured ASRT response is produced.

## Method-specific result fields

- `Speech` returns `SpeechResponse.result_data`, a repeated string pinyin sequence.
- `Language` returns `TextResponse.text_result`, recognized text from pinyin.
- `All` returns `TextResponse.text_result`, recognized text from audio.
- `Stream` yields multiple `TextResponse` messages. Treat `206000` as partial and `200000` as final or finalized chunk.

For startup and port details, see [Deployment](deployment.md). For version and stub failures, see [Troubleshooting](troubleshooting.md).
