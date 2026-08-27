# Cloud, optional dependency, and engine reference

This reference collects runtime requirements that are easy to miss when selecting a SpeechRecognition engine. Optional extras are from `pyproject.toml` for SpeechRecognition 3.17.0.

## Optional extras by engine

Install only the extras needed for the selected workflow.

| Extra | Packages declared by the distribution | Enables | Notes |
| --- | --- | --- | --- |
| base install | `typing-extensions`; on Python 3.13+ also `standard-aifc`, `audioop-lts` | `AudioData`, `AudioFile`, `recognize_google`, legacy urllib-based web APIs | Base install can load files and call Google legacy, but still needs network for web recognizers. |
| `pocketsphinx` | `pocketsphinx` | `recognize_sphinx` | Uses bundled `en-US` Sphinx data; other languages require matching model files. |
| `vosk` | `vosk` | `recognize_vosk` | Also requires a downloaded Vosk model; route model download/setup to `../../cli-model-setup/SKILL.md`. |
| `google-cloud` | `google-cloud-speech` | `recognize_google_cloud` | Google Cloud Speech-to-Text V1 only in this wrapper. |
| `whisper-local` | `openai-whisper`, `soundfile` | `recognize_whisper` | Pulls model weights on first use unless cached; may use Torch CPU/GPU depending on environment. |
| `faster-whisper` | `faster-whisper`, `soundfile` | `recognize_faster_whisper` | Pulls/loads CTranslate2-compatible model weights; `init_options` controls device/compute type. |
| `openai` | `openai`, `httpx < 0.28` | `recognize_openai` | OpenAI hosted or OpenAI-compatible endpoints. |
| `groq` | `groq`, `httpx < 0.28` | `recognize_groq` | Groq-hosted Whisper API. |
| `cohere-api` | `cohere >= 5.21.0` | `recognize_cohere_api` | Cohere Transcribe API; `language` is required. |
| `assemblyai` | `requests` | `recognize_assemblyai` | Legacy async AssemblyAI wrapper. |
| not declared as an extra | `boto3`, `botocore` | `recognize_lex`, `recognize_amazon` | Required by source imports but not listed in SpeechRecognition optional extras. |
| not declared as an extra | `tensorflow` and compatible graph/labels | `recognize_tensorflow` | Legacy TensorFlow command-label classifier, not full STT. |

`audio` (`PyAudio >= 0.2.11`) is for microphone capture, not recognizer engine calls after an `AudioData` object already exists.

## Credential and network requirements

| Engine | Credential inputs | Network | Safe invocation guidance |
| --- | --- | --- | --- |
| Google legacy | Optional `key`; no key uses a bundled generic key | yes | For scripts or production, require a user-supplied key or an explicit acknowledgement to use the generic demo key. |
| Google Cloud | `credentials_json_path` or application default credentials | yes | Require a user-owned GCP project, API enabled, and billing/credentials configured outside skill files. |
| OpenAI | `OPENAI_API_KEY`; optional `OPENAI_BASE_URL` for compatible endpoint | yes unless self-hosted local endpoint | Require explicit engine choice and key/base URL in the user's environment or command args. |
| Groq | `GROQ_API_KEY` | yes | Require explicit engine choice and environment key. |
| Cohere | `CO_API_KEY` used by Cohere SDK | yes | Require explicit engine choice, key, and `language`. |
| Wit.ai | method `key` argument | yes | Language is configured in Wit.ai app settings, not in the call. |
| Azure | method `key`, plus `location`; optional `language`, `profanity` | yes | The wrapper first obtains/caches an access token, then submits audio to the regional STT endpoint. |
| Houndify | `client_id`, `client_key` | yes | Client key is base64-decoded for HMAC signing; currently English-only in source docs. |
| IBM | `key` argument in 3.17.0 source | yes | Some older docs/examples mention username/password, but current source uses `username='apikey'` internally and accepts a single API key. |
| Lex | AWS SDK credential chain or explicit access key/secret/region; bot name/alias/user id | yes | Requires an existing Lex bot and `boto3`; returns `inputTranscript`. |
| Amazon Transcribe | AWS SDK credential chain or explicit keys/region; S3 bucket/job names optional | yes | Has S3 and Transcribe side effects; first call usually raises `TranscriptionNotReady`. |
| AssemblyAI | `api_token`; job id for polling | yes | Source wrapper is async and expects path-like upload input in the start path. |
| API.AI/Dialogflow legacy | `client_access_token`; optional `language`, `session_id` | yes | Deprecated shim; use only for maintaining old integrations. |

Do not embed API keys, service-account JSON contents, bearer tokens, bucket names that reveal private projects, or endpoint credentials into generated skill files.

## Local model and data requirements

### PocketSphinx

- `recognize_sphinx` requires the `pocketsphinx` Python module.
- `language='en-US'` uses bundled package data. Other string language codes require installed data with the same language directory name.
- A custom language tuple can supply exact Sphinx data paths: `(acoustic_parameters_directory, language_model_file, phoneme_dictionary_file)`.
- Keyword mode creates a temporary keyword search file from `(keyword, sensitivity)` pairs.
- Grammar mode accepts JSGF or FSG path. If the JSGF has no `.fsg` sibling, PocketSphinx writes one next to the grammar. Warn users before pointing grammar mode at read-only or shared directories.

### Vosk

- `recognize_vosk` requires the `vosk` Python module and a Vosk model in SpeechRecognition's package model directory.
- Missing model raises `SetupError` with guidance to run `sprc download vosk`.
- The wrapper forces 16 kHz, 16-bit raw audio before recognition.
- `verbose=False` returns only `result['text']`; `verbose=True` returns the parsed final JSON dict.

### Local Whisper

- `recognize_whisper` requires `openai-whisper`, `soundfile`, `numpy`, and the runtime dependencies of Whisper/Torch.
- `model='base'` by default; valid model names are those accepted by the installed `whisper` package.
- `load_options` are passed to `whisper.load_model`, for example `device`, `download_root`, or `in_memory`.
- If `fp16` is not supplied, the wrapper sets `fp16` based on CUDA availability.
- `show_dict=True` returns the full transcribe dict including `text`, `segments`, and `language`.

### Faster-Whisper

- `recognize_faster_whisper` requires `faster-whisper`, `soundfile`, and `numpy`.
- `init_options` are passed to `faster_whisper.WhisperModel`, for example `device`, `compute_type`, or `download_root`.
- `transcribe_options` are passed to `WhisperModel.transcribe`, for example `language`, `task`, or `beam_size`.
- The adapter consumes the segment generator, joins segment text with spaces, and returns a dict with `text`, `segments`, and `language` when `show_dict=True`.

### TensorFlow legacy command model

- `recognize_tensorflow` is a command-label classifier using an external frozen graph and labels file. It is not a general transcript engine.
- It uses TensorFlow 1.x-style APIs such as `tf.gfile`, `tf.GraphDef`, and `tf.Session`; modern TensorFlow compatibility may require extra adaptation.
- It loads a graph once per `tensor_graph` path and caches labels on the recognizer instance.

## Provider model defaults and accepted names

- `recognize_openai` defaults to `model="whisper-1"`; source type hints also list `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, and `gpt-transcribe`. OpenAI-compatible endpoints may accept different names, so use the endpoint's advertised model.
- `recognize_groq` defaults to `model="whisper-large-v3-turbo"`; source type hints also list `whisper-large-v3`.
- `recognize_cohere_api` defaults to `model="cohere-transcribe-03-2026"` and requires `language`.
- Local `recognize_whisper` and `recognize_faster_whisper` both default to `model="base"`; valid model names are controlled by the installed backend.

## Raw response and confidence behavior

| Method | Raw/detail flag | Shape |
| --- | --- | --- |
| `recognize_google` | `show_all=True` | selected parsed Google result dict with `alternative` list and `final`; not the entire newline response. |
| `recognize_google` | `with_confidence=True` | `(transcript, confidence)` if `show_all=False`; confidence defaults to `0.5` if absent. |
| `recognize_google_cloud` | `show_all=True` | `google.cloud.speech.RecognizeResponse` SDK object; word offsets are requested. |
| `recognize_sphinx` | `show_all=True` | PocketSphinx `Decoder` object. |
| `recognize_vosk` | `verbose=True` | parsed Vosk dict such as `{"text": "one two three"}`. |
| `recognize_whisper` / `recognize_faster_whisper` | `show_dict=True` | dict with `text`, `segments`, and `language`. |
| `recognize_wit` | `show_all=True` | raw JSON dict from Wit.ai. |
| `recognize_azure` | `show_all=True` | raw Azure JSON dict; default is `(Display, Confidence)`. |
| `recognize_houndify` | `show_all=True` | raw Houndify JSON dict; default is `(Transcription, ConfidenceScore)`. |
| `recognize_ibm` | `show_all=True` | raw IBM JSON dict; default is `(joined_transcript, confidence)`. |
| `recognize_api` | `show_all=True` | raw API.AI JSON dict; default is `resolvedQuery`. |

OpenAI, Groq, Cohere, Lex, TensorFlow, Amazon Transcribe, and AssemblyAI wrappers do not expose a `show_all` flag in this release.

## OpenAI-compatible endpoint pattern

`recognize_openai` constructs `openai.OpenAI()` with SDK defaults. To point to a compatible endpoint, set environment variables before calling the recognizer:

```python
import os
import speech_recognition as sr

os.environ["OPENAI_API_KEY"] = "dummy-or-real-key"
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"

r = sr.Recognizer()
audio = sr.AudioData.from_file("speech.wav")
print(r.recognize_openai(audio, model="whisper-1"))
```

Use the endpoint's expected model name if it differs from OpenAI hosted model names.
