# Recognition engine selection

This matrix is for SpeechRecognition 3.17.0 (`import speech_recognition as sr`). Start by creating `audio_data` from a file or capture flow, then call one `Recognizer` method. For file loading and conversion details, use `../../audio-data/SKILL.md`; for microphone capture, use `../../capture-listening/SKILL.md`.

## Quick choice guide

| Constraint or goal | Prefer | Why | Avoid or note |
| --- | --- | --- | --- |
| No account, quick web demo, small request | `recognize_google` | Base install; default Chromium-style key works for demos; simple `show_all` raw JSON. | Network required; generic key can be revoked or rate-limited; use explicit key/endpoint for production. |
| Fully offline and lightweight English support | `recognize_sphinx` | Local PocketSphinx; bundled `en-US` language data; supports keywords and grammars. | Needs `SpeechRecognition[pocketsphinx]`; out-of-box language is only `en-US`; accuracy is limited compared with modern models. |
| Fully offline with Vosk model | `recognize_vosk` | Local Vosk inference; `verbose=True` returns parsed Vosk dict. | Needs `SpeechRecognition[vosk]` and a downloaded model in the package model location; setup is routed to `../../cli-model-setup/SKILL.md`. |
| Fully offline modern transcription | `recognize_whisper` | OpenAI Whisper local models; `show_dict=True` returns text, segments, and language. | Needs `SpeechRecognition[whisper-local]`; model download/cache and CPU/GPU runtime can be large. |
| Faster local Whisper-style inference | `recognize_faster_whisper` | CTranslate2/faster-whisper backend; can pass init options such as `compute_type`. | Needs `SpeechRecognition[faster-whisper]`; model download/cache and device compatibility still matter. |
| Hosted Google Cloud Speech-to-Text V1 | `recognize_google_cloud` | Official `google-cloud-speech` SDK; supports `preferred_phrases`, `model`, `use_enhanced`, raw `RecognizeResponse`. | Needs `SpeechRecognition[google-cloud]`, GCP project/billing/API/credentials; V2 is not wrapped here. |
| Hosted OpenAI transcription or self-hosted OpenAI-compatible endpoint | `recognize_openai` | Official OpenAI SDK; supports OpenAI-compatible base URL via environment. | Needs `SpeechRecognition[openai]`; credentials/base URL must be explicit before cloud calls. |
| Hosted Groq Whisper API | `recognize_groq` | Official Groq SDK and Groq Whisper model names. | Needs `SpeechRecognition[groq]` and `GROQ_API_KEY`. |
| Hosted Cohere Transcribe | `recognize_cohere_api` | Official Cohere SDK; current wrapper requires an explicit language argument. | Needs `SpeechRecognition[cohere-api]` and `CO_API_KEY`; `language` is keyword-only and required. |
| Existing legacy integration | `recognize_wit`, `recognize_azure`, `recognize_houndify`, `recognize_ibm`, `recognize_api` | Still present for compatibility and raw `show_all` responses. | These are older web APIs with account/network dependencies; prefer maintained engines for new work. |
| AWS Lex bot integration | `recognize_lex` | Sends raw PCM to `lex-runtime` via `boto3`. | Requires AWS credentials/region/bot settings; returns only `inputTranscript`. |
| AWS Transcribe async job | `recognize_amazon` | Starts/polls Amazon Transcribe jobs through S3. | Async exception protocol, S3 side effects, public-read upload in source implementation; use carefully. |
| AssemblyAI async service | `recognize_assemblyai` | Starts/polls AssemblyAI transcripts. | Source implementation expects a file path for upload rather than `AudioData`; check status via job id. |
| Legacy command classification model | `recognize_tensorflow` | Loads an external TensorFlow graph/labels and returns top label. | Legacy TensorFlow 1.x-style API and external model files; not a general STT transcript engine. |

## Safe default pattern

```python
import speech_recognition as sr

recognizer = sr.Recognizer()
audio = sr.AudioData.from_file("input.wav")

try:
    text = recognizer.recognize_sphinx(audio)  # offline, if pocketsphinx extra is installed
except sr.UnknownValueError:
    text = None  # engine ran but found no intelligible transcript
except (sr.RequestError, sr.SetupError) as exc:
    raise RuntimeError(f"engine setup/request failed: {exc}") from exc
```

When using a cloud service, make the user's engine choice and credentials explicit. Do not silently fall back from an offline engine to a network engine or use placeholder keys.

## Offline engine notes

- **PocketSphinx**: best for small-vocabulary, keywords, and grammars. `keyword_entries` takes `(keyword, sensitivity)` pairs with sensitivity from `0` to `1`. If `keyword_entries` is provided, grammar content is ignored. `grammar` accepts a path to a JSGF or FSG grammar; a JSGF input may create a sibling `.fsg` file for faster later runs.
- **Vosk**: the wrapper looks for a Vosk model in SpeechRecognition's package model directory. The error message instructs users to run `sprc download vosk`; model download and location checks are owned by `../../cli-model-setup/SKILL.md`.
- **Whisper**: `model` defaults to `"base"`; use `load_options` for `whisper.load_model` options such as `device`, `download_root`, or `in_memory`; transcribe options pass through to Whisper, commonly `language`, `task`, `temperature`, and `fp16`.
- **Faster-Whisper**: `model` defaults to `"base"`; use `init_options` for `WhisperModel` options such as `device`, `compute_type`, or `download_root`; transcribe options pass through, commonly `language`, `task`, and `beam_size`.

## Cloud/service notes

- **Google legacy** (`recognize_google`) is convenient but not a production SLA. It encodes FLAC, sends it to the configured endpoint, and parses newline-delimited JSON responses.
- **Google Cloud** uses the Google Cloud Speech-to-Text V1 SDK. Use `credentials_json_path` for a service-account JSON file or rely on application default credentials configured outside the skill. `show_all=True` returns a SDK `RecognizeResponse`, not a plain dict.
- **OpenAI-compatible** uses `openai.OpenAI()`, so SDK environment variables such as `OPENAI_API_KEY` and `OPENAI_BASE_URL` control hosted versus compatible endpoints.
- **Groq** uses `groq.Groq()` and `GROQ_API_KEY`.
- **Cohere** uses `cohere.ClientV2()` and the SDK's `CO_API_KEY`; `language` is required.
- **Legacy services** generally raise `RequestError` for network/credential failures and `UnknownValueError` when the response has no recognizable text. Some return `(text, confidence)` tuples rather than plain text.

## Response-shape decision

If the downstream task needs alternatives, timestamps, raw fields, or service-specific diagnostics:

- Use `show_all=True` for Google legacy, Google Cloud, PocketSphinx, Wit.ai, Azure, Houndify, and IBM where supported.
- Use `verbose=True` for Vosk to return `{"text": ...}` instead of just the text.
- Use `show_dict=True` for local Whisper/Faster-Whisper to return `{"text": ..., "segments": ..., "language": ...}`.
- Use `with_confidence=True` only on `recognize_google`; it returns `(transcript, confidence)` when `show_all=False`.
- OpenAI, Groq, Cohere wrappers return text only in this release; pass provider kwargs only for supported request fields.
