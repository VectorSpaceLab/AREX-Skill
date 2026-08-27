# API Contracts

## REST Routes

When configured for HTTP, PaddleSpeech includes REST routers based on `engine_list` tasks:

| Route | Method | Purpose | Main payload/result |
| --- | --- | --- | --- |
| `/paddlespeech/asr/help` | GET | ASR help | description, input/output fields |
| `/paddlespeech/asr` | POST | Offline ASR | base64 WAV input -> transcription |
| `/paddlespeech/tts/help` | GET | TTS help | text/audio description |
| `/paddlespeech/tts` | POST | Offline TTS | text/speed/volume/sample_rate/spk_id -> base64 audio and metadata |
| `/paddlespeech/tts/streaming` | POST | Streaming TTS over HTTP | streaming audio response |
| `/paddlespeech/tts/streaming/samplerate` | GET | TTS stream sample rate | sample rate |
| `/paddlespeech/cls` | POST | Audio classification | base64 WAV -> top-k labels/scores |
| `/paddlespeech/text` | POST | Punctuation restoration | text -> punctuated text |
| `/paddlespeech/vector` | POST | Speaker vector | base64 WAV -> vector list |
| `/paddlespeech/vector/score` | POST | Speaker score | enroll/test base64 WAV -> score |
| `/paddlespeech/asr/search` | POST | Audio content search / timestamps | base64 WAV -> transcription and word timing/search result |

The packaged clients handle base64 encoding for file inputs. For custom clients, match the request schemas and endpoint used by the client executor.

## WebSocket Routes

Streaming ASR:

- Route: `/paddlespeech/asr/streaming`.
- Client sends JSON `{"signal": "start"}` to establish a connection handler.
- Client sends PCM bytes chunks.
- Client sends JSON `{"signal": "end"}` to flush final result.
- Server returns partial results and final result/timestamps.

Streaming TTS:

- Route: `/paddlespeech/tts/streaming`.
- Client sends `{"signal": "start"}` to create a session.
- Client sends text payloads with `text` and `spk_id`.
- Server yields audio chunks until completion.
- Client sends `{"signal": "end"}` to close.

## Parameter Validation

TTS REST validates `speed` and `volume` in `(0, 3]`, `sample_rate` in `{0, 8000, 16000}`, and `save_path` ending in `.pcm` or `.wav` when provided. Respect those constraints in generated clients.
