---
name: serving-clients
description: "Deploy and integrate ASRT HTTP/gRPC serving clients once trained
  weights are available."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Serving Clients

Use this sub-skill when the ASRT service boundary is the active problem: starting an already prepared HTTP/gRPC server, constructing request payloads, calling the service, interpreting responses, or debugging deployment and client integration failures.

## Route here

- Start or configure ASRT HTTP/gRPC service processes after trained acoustic weights and language-model assets are already present.
- Build HTTP JSON payloads for `GET /`, `POST /`, `POST /speech`, `POST /language`, and `POST /all`.
- Integrate gRPC clients for `Speech`, `Language`, `All`, and `Stream` using the `AsrtGrpcService` contract.
- Interpret ASRT response/status fields, including streaming partial status `206000` and final status `200000`.
- Debug endpoint paths, ports, base64 encoding, WAV metadata, protobuf stubs, and Docker CPU-only serving behavior.

## Not here

- Training, exporting, or selecting acoustic model weights.
- Dataset preparation or audio feature extraction beyond reading WAV metadata and sample bytes for service payloads.
- Language-model corpus construction, scoring internals, or pinyin-to-text quality tuning.
- Copying or rewriting ASRT server implementations.

## Read first

- [Deployment boundaries and startup](references/deployment.md)
- [HTTP JSON API](references/http-api.md)
- [gRPC API](references/grpc-api.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled runtime helpers

- `scripts/make_http_payload.py` builds JSON request bodies from a user-provided WAV file or pinyin sequence without importing ASRT.
- `scripts/asrt_http_client.py` calls the ASRT HTTP service with only Python standard-library networking and WAV handling.

Safe help checks:

```bash
python scripts/make_http_payload.py --help
python scripts/asrt_http_client.py --help
```

Example payload/client flow:

```bash
python scripts/make_http_payload.py --endpoint /all --wav sample.wav --pretty > all-payload.json
python scripts/asrt_http_client.py all --wav sample.wav --base-url http://127.0.0.1:20001
python scripts/asrt_http_client.py language --sequence-pinyin ni3 hao3 ya5
```

## Critical operating facts

- The original HTTP and gRPC server scripts instantiate `SpeechModel251BN`, load `save_models/SpeechModel251bn.model.h5`, and load `model_language` at module import time before serving requests.
- Those server scripts start long-lived listeners (`waitress.serve` for HTTP; `grpc.server(...).start()` plus an infinite sleep loop for gRPC). This generated runtime therefore bundles only client and payload helpers, not server copies.
- HTTP audio requests send raw WAV sample frames, not the RIFF/WAVE container, as URL-safe base64 text in `samples` with matching `sample_rate`, `channels`, and `byte_width` metadata.
- HTTP language requests send `sequence_pinyin` as a JSON list of pinyin syllable strings.
- gRPC audio requests send the same raw sample frames in `WavData.samples`; gRPC language requests send repeated `pinyins` in `LanguageRequest`.

## Evidence base

This sub-skill was revised from the serving evidence in `asrserver_http.py`, `asrserver_grpc.py`, `client_http.py`, `client_grpc.py`, `assets/asrt.proto`, `Dockerfile`, `README.md`, `README_EN.md`, and `utils/ops.py`.

## Routing notes

- Missing `save_models/SpeechModel251bn.model.h5` is a model-preparation problem; stop server/client debugging and route to acoustic-model work.
- Invalid WAV sample shape, sample rate, channel count, or sample width belongs to data/audio preparation after confirming the client payload mirrors the WAV metadata.
- Bad pinyin-to-text output with successful `/language` or gRPC `Language` responses belongs to language-model work.
- For protobuf, generated-stub, version, or service-method mismatches, use [gRPC API](references/grpc-api.md) and [Troubleshooting](references/troubleshooting.md) before changing application logic.
