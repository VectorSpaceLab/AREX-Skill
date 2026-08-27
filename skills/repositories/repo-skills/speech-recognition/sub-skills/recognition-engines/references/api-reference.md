# Recognizer transcription API reference

All methods below are called on `speech_recognition.Recognizer()` with an `speech_recognition.AudioData` object unless noted. The signatures reflect SpeechRecognition 3.17.0 source and installed inspection facts used during skill construction.

## Exceptions and validation

- `UnknownValueError`: the engine request/inference completed but no intelligible or usable transcript was found.
- `RequestError`: service request, network, credential, SDK import, or engine installation problem for most non-new recognizers.
- `SetupError`: newer wrappers use this for missing setup such as missing Vosk model, missing `openai`, missing `groq`, or missing `cohere` package.
- `ValueError`/`AssertionError`: invalid local arguments such as non-`AudioData`, missing grammar file, invalid keyword sensitivities, or wrong credential argument type.
- `TranscriptionNotReady` / `TranscriptionFailed`: async legacy services (`recognize_amazon`, `recognize_assemblyai`) use these to signal polling state and terminal failure.

Prefer catching the narrow expected errors around one engine call, not around unrelated audio acquisition or conversion.

## Current recognizer modules

| Method | Verified signature summary | Main parameters | Return when default | Raw/detail return | Primary exceptions |
| --- | --- | --- | --- | --- | --- |
| `recognize_google` | `(audio_data, key=None, language='en-US', pfilter=0, show_all=False, with_confidence=False, *, endpoint=...)` | optional API `key`; RFC/IETF language tag; `pfilter` `0` or `1`; custom endpoint | `str` transcript | `show_all=True` returns the selected Google result dict with `alternative` list and `final`; `with_confidence=True` returns `(transcript, confidence)` when not `show_all` | `UnknownValueError`, `RequestError`, `ValueError` |
| `recognize_google_cloud` | `(audio_data, credentials_json_path=None, **kwargs)` | `language_code='en-US'`; `preferred_phrases`; `show_all`; `model`; `use_enhanced`; service-account path or ADC | joined `str` transcript from result alternatives | `show_all=True` returns `google.cloud.speech.RecognizeResponse` and enables word time offsets | `UnknownValueError`, `RequestError` |
| `recognize_sphinx` | `(audio_data, language='en-US', keyword_entries=None, grammar=None, show_all=False)` | bundled language code or `(hmm_dir, lm_file, dict_file)` tuple; keywords; grammar path | `str` hypothesis | `show_all=True` returns `pocketsphinx.pocketsphinx.Decoder` | `UnknownValueError`, `RequestError`, `ValueError`, `AssertionError` |
| `recognize_vosk` | `(audio_data, *, verbose=False)` | local model path is fixed by package model location | `str` from parsed Vosk JSON `text` field | `verbose=True` returns parsed dict, currently shaped like `{"text": "..."}` | `SetupError`; package import errors from `vosk` can also surface if the extra is absent |
| `recognize_whisper` | `(audio_data, model='base', show_dict=False, load_options=None, **transcribe_options)` | Whisper model name; load options; transcribe options such as `language`, `task`, `temperature`, `fp16` | `str` from `result['text']` | `show_dict=True` returns dict with `text`, `segments`, `language` | import/runtime errors from `whisper`, `soundfile`, `numpy`, `torch`; `ValueError` for non-`AudioData` |
| `recognize_faster_whisper` | `(audio_data, model='base', show_dict=False, init_options=None, **transcribe_options)` | Faster-Whisper model name; init options such as `device`, `compute_type`, `download_root`; transcribe options such as `language`, `task`, `beam_size` | `str` made by joining segment text with spaces | `show_dict=True` returns dict with `text`, `segments`, `language` | import/runtime errors from `faster_whisper`, `soundfile`, `numpy`; `ValueError` for non-`AudioData` |
| `recognize_openai` | `(audio_data, *, model='whisper-1', **kwargs)` | `model`; provider kwargs such as `language`, `prompt`, `response_format='json'`, `temperature` | `str` from SDK transcription `.text` | no `show_all` in this wrapper | `SetupError` if `openai` missing; SDK errors for credentials/network/base URL; `ValueError` for non-`AudioData` |
| `recognize_groq` | `(audio_data, *, model='whisper-large-v3-turbo', **kwargs)` | Groq model; provider kwargs such as `prompt`, `response_format`, `temperature`, `language` | `str` from SDK transcription `.text` | no `show_all` in this wrapper | `SetupError` if `groq` missing; SDK errors for credentials/network; `ValueError` for non-`AudioData` |
| `recognize_cohere_api` | `(audio_data, *, language, model='cohere-transcribe-03-2026')` | required keyword-only `language`; Cohere model | `str` response text | no `show_all` in this wrapper | `SetupError` if `cohere` missing; SDK errors for credentials/network; `ValueError` for non-`AudioData` |

### Google legacy parsing details

- Audio is encoded as FLAC; sample rates below 8 kHz are converted up to 8 kHz and width is converted to 16-bit.
- The response parser ignores blank newline blocks and chooses the first non-empty `result` entry.
- `show_all=False` returns the first usable hypothesis text. In this release, the source checks confidence presence on the list object, so it ordinarily chooses the first alternative rather than ranking alternatives by confidence.
- If a selected hypothesis lacks `confidence`, `with_confidence=True` uses a fallback confidence of `0.5`.

### Google Cloud parsing details

- Audio is encoded as FLAC with sample rate clamped into 8 kHz through 48 kHz and width converted to 16-bit.
- `preferred_phrases` becomes a `SpeechContext(phrases=...)`.
- `show_all=True` is passed into config construction by enabling `enable_word_time_offsets=True`, then returns the SDK response object unchanged.
- With default return, an empty `response.results` raises `UnknownValueError`; otherwise transcripts are stripped and joined with spaces from the first alternative of each result.

### PocketSphinx parsing details

- `language='en-US'` resolves to package data under `pocketsphinx-data/en-US`; a string for any other language must have matching installed package language data.
- A custom language tuple must contain `(acoustic_parameters_directory, language_model_file, phoneme_dictionary_file)`.
- `keyword_entries` is asserted to be `None` or pairs of `(str, sensitivity)` with `0 <= sensitivity <= 1`.
- If `keyword_entries` is present, the grammar is ignored.
- If `grammar` is JSGF and no sibling `.fsg` exists, PocketSphinx writes one at the grammar location.
- Default return is `decoder.hyp().hypstr`; no hypothesis raises `UnknownValueError`.

### Vosk parsing details

- The wrapper constructs `KaldiRecognizer(Model(model_path), 16000)`.
- Audio is passed as 16 kHz, 16-bit raw data.
- It calls `AcceptWaveform(...)`, then parses `FinalResult()` JSON.
- Default return is `result['text']`; `verbose=True` returns the whole parsed dict.

### Whisper and Faster-Whisper parsing details

- Both wrappers convert the input to WAV bytes at 16 kHz, read it with `soundfile`, cast to `numpy.float32`, and call a transcribe method.
- Local Whisper sets `fp16=torch.cuda.is_available()` only when `fp16` is not already supplied.
- Faster-Whisper adapts `(segments_generator, info)` into `{"text": " ".join(segment.text ...), "segments": list(segments), "language": info.language}`.
- `show_dict=False` returns the dict's `text`; `show_dict=True` returns the dict.

## Legacy and service methods in `speech_recognition.__init__`

These are compatibility surfaces and may be less maintained than the recognizer modules above. Many require external accounts and network access.

| Method | Signature summary | Default return | Raw/detail or async behavior | Notes |
| --- | --- | --- | --- | --- |
| `recognize_wit` | `(audio_data, key, show_all=False)` | `result['_text']` | `show_all=True` returns raw Wit.ai JSON dict | WAV upload; language configured in Wit.ai app. |
| `recognize_azure` | `(audio_data, key, language='en-US', profanity='masked', location='westus', show_all=False)` | `(Display, Confidence)` tuple from `NBest[0]` | `show_all=True` returns raw Azure JSON dict | Caches access token on recognizer for about 10 minutes; uploads 16 kHz WAV. |
| `recognize_houndify` | `(audio_data, client_id, client_key, show_all=False)` | `(Transcription, ConfidenceScore)` tuple | `show_all=True` returns raw Houndify JSON dict | HMAC authentication; current docs say only English. |
| `recognize_ibm` | `(audio_data, key, language='en-US', show_all=False)` | `(joined_transcript, confidence)` tuple | `show_all=True` returns raw IBM JSON dict | Source uses `username='apikey'` with API key as password. |
| `recognize_lex` | `(audio_data, bot_name, bot_alias, user_id, content_type='audio/l16; rate=16000; channels=1', access_key_id=None, secret_access_key=None, region=None)` | `response['inputTranscript']` | no `show_all` | Requires `boto3`; uses Lex Runtime `post_content`. |
| `recognize_amazon` | `(audio_data, bucket_name=None, access_key_id=None, secret_access_key=None, region=None, job_name=None, file_key=None)` | usually raises `TranscriptionNotReady` first; later returns `(transcript, confidence)` | pass `audio_data=None` and previous `job_name` to poll | Uses `boto3`, S3 upload, Amazon Transcribe; creates/deletes jobs and S3 objects. |
| `recognize_assemblyai` | `(audio_data, api_token, job_name=None, **kwargs)` | usually raises `TranscriptionNotReady` first; later returns `(text, confidence)` | pass `audio_data=None` and previous `job_name` to poll | Source upload helper expects a filename-like path for `audio_data`; not the same `AudioData` flow as most engines. |
| `recognize_tensorflow` | `(audio_data, tensor_graph='tensorflow-data/conv_actions_frozen.pb', tensor_label='tensorflow-data/conv_actions_labels.txt')` | top label string | no raw option | Loads TensorFlow graph/labels and runs `labels_softmax:0`; legacy TF API. |
| `recognize_api` | `(audio_data, client_access_token, language='en', session_id=None, show_all=False)` | `result['result']['resolvedQuery']` | `show_all=True` returns raw API.AI JSON dict | Deprecated/not recommended shim; currently assigned as a classmethod in source. |

## Minimal cloud call examples

```python
import os
import speech_recognition as sr

r = sr.Recognizer()
audio = sr.AudioData.from_file("speech.wav")

# Google legacy with an explicit key rather than an invisible placeholder.
text = r.recognize_google(audio, key=os.environ["GOOGLE_SPEECH_KEY"], language="en-US")

# Google Cloud V1 with application default credentials configured outside code.
text = r.recognize_google_cloud(audio, language_code="en-US", preferred_phrases=["project codename"])

# OpenAI-compatible endpoint. The SDK reads OPENAI_API_KEY and optionally OPENAI_BASE_URL.
text = r.recognize_openai(audio, model="whisper-1", language="en")

# Cohere requires language.
text = r.recognize_cohere_api(audio, language="en")
```

Do not store keys in code or generated skill files; read them from the user's environment or an approved secret manager at runtime.
