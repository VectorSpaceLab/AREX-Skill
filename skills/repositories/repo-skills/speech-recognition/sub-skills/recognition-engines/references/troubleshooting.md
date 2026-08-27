# Recognition engine troubleshooting

Use this when a SpeechRecognition transcription engine fails after you already have an `AudioData` object. If the problem is file decoding, raw bytes, segmentation, FLAC conversion, or upload-size chunking, route to `../../audio-data/SKILL.md`. If the problem is microphone capture or calibration, route to `../../capture-listening/SKILL.md`.

## First triage

1. Confirm the object is `speech_recognition.AudioData`, not a file path, bytes object, microphone source, or open stream. Most engines validate this with `ValueError` or `AssertionError`.
2. Identify the exact engine and optional extra. Do not install all extras just to fix one engine.
3. Decide whether network access and credentials are expected. Offline engines should not silently fall back to cloud calls.
4. Catch and interpret:
   - `UnknownValueError`: recognition ran but produced no usable transcript.
   - `RequestError`: request, network, credential, SDK import, or engine installation failure for most older engines.
   - `SetupError`: newer setup failure such as missing `openai`/`groq`/`cohere` package or missing Vosk model.
5. If a raw/detail flag exists (`show_all`, `verbose`, `show_dict`), rerun with it to inspect alternatives and provider status when safe.

## Missing optional modules

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RequestError: missing PocketSphinx module` | `pocketsphinx` extra absent | Install `SpeechRecognition[pocketsphinx]` in the runtime environment. |
| `ImportError: No module named vosk` or similar | `vosk` extra absent | Install `SpeechRecognition[vosk]`, then ensure the model is downloaded. |
| `SetupError: Vosk model not found ... sprc download vosk` | Vosk package exists but model files are absent | Use the CLI/model setup sub-skill for `sprc download vosk` and model path checks. |
| Missing `google-cloud-speech` message | `google-cloud` extra absent | Install `SpeechRecognition[google-cloud]`. |
| `SetupError: missing openai module` | `openai` extra absent | Install `SpeechRecognition[openai]`. |
| `SetupError: missing groq module` | `groq` extra absent | Install `SpeechRecognition[groq]`. |
| `SetupError: missing cohere module` | `cohere-api` extra absent | Install `SpeechRecognition[cohere-api]`. |
| `ModuleNotFoundError: soundfile`, `whisper`, `faster_whisper`, `numpy`, or Torch-related import errors | local Whisper/Faster-Whisper dependencies absent or incompatible | Install the matching local extra and resolve model/runtime dependencies for the selected backend. |
| `RequestError: missing boto3 module` | AWS Lex/Amazon dependencies absent | Install `boto3`/`botocore`; these are not declared as SpeechRecognition extras in 3.17.0. |
| `RequestError: missing tensorflow module` | TensorFlow legacy dependency absent | Use a compatible TensorFlow environment and provide graph/label files, or choose a maintained engine. |
| `ImportError` around `tqdm` when using `sprc` | CLI helper imports `tqdm` although it is not part of the base runtime dependency list | Route CLI setup to `../../cli-model-setup/SKILL.md`; install `tqdm` if the installed release/environment lacks it. |

On Python 3.13+, base package dependencies include `standard-aifc` and `audioop-lts`; import failures around `aifc`/`audioop` indicate an incomplete base install.

## Credentials and network errors

| Engine | Common failure | Action |
| --- | --- | --- |
| Google legacy | `RequestError` with HTTP/URL reason; generic key stops working | Pass a user-owned `key`, check internet/proxy, or choose offline engine. |
| Google Cloud | `RequestError` wrapping Google API error; ADC not found; permission denied | Confirm `google-cloud-speech` extra, GCP project/API/billing, `credentials_json_path` or application default credentials, and `language_code`. |
| OpenAI | SDK authentication error; 404/connection error with compatible endpoint | Set `OPENAI_API_KEY`; for compatible endpoints set `OPENAI_BASE_URL` to a `/v1` base and use a supported model name. |
| Groq | `groq.GroqError` or auth failure | Set `GROQ_API_KEY`, use `whisper-large-v3-turbo` or `whisper-large-v3`, and check network. |
| Cohere | SDK auth or validation error | Set `CO_API_KEY`, pass keyword-only `language`, and use a supported transcribe model. |
| Azure | credential request failure or recognition request failure | Check regional `location`, subscription key, token endpoint access, and `language`/`profanity` values. |
| Houndify | authentication failure | Confirm `client_id` and base64 `client_key`; HMAC signing fails if the key is malformed. |
| IBM | auth failure | Current source accepts `key` and sends it as API key basic auth; do not use outdated username/password examples without checking the installed version. |
| AWS Lex/Amazon | boto credential or region errors | Confirm AWS credential chain or explicit keys, region, service permissions, bot/job/bucket names, and S3 permissions. |
| AssemblyAI | status `error` or upload/status failure | Confirm API token, file upload path behavior, and poll using the returned job id. |
| API.AI legacy | non-success status | This deprecated shim may no longer match modern Dialogflow; use only for legacy systems. |

For networked engines, do not retry indefinitely on authentication errors. Retry only transient DNS/timeout/5xx errors and surface the provider response when available.

## UnknownValueError versus RequestError

- `UnknownValueError` means SpeechRecognition reached a parser or decoder result but did not find expected transcript fields or a hypothesis. Improve audio quality, specify language, inspect raw alternatives, try a more appropriate engine, or use keyword/grammar constraints for small vocabularies.
- `RequestError` means the engine or provider request could not be completed successfully. Fix installation, credentials, network, service settings, or language/model parameters first.
- `SetupError` means a newer wrapper detected missing local setup before recognition. Install the extra, download the model, or configure SDK credentials as appropriate.

Do not treat `UnknownValueError` as a network outage, and do not treat credential errors as unintelligible audio.

## Language code pitfalls

| Engine | Language parameter style | Common mistake |
| --- | --- | --- |
| `recognize_google` | IETF/RFC-style tag such as `en-US`, `fr-FR`, `zh-CN` | Passing Whisper language names like `english`. |
| `recognize_google_cloud` | `language_code`, BCP-47 tag such as `en-US` | Passing `language=` instead of `language_code=`. |
| `recognize_sphinx` | bundled language directory string such as `en-US`, or explicit data tuple | Expecting non-`en-US` languages without installing matching Sphinx data. |
| `recognize_whisper` | Whisper options: `language` can be full uncapitalized language name such as `english`; omit for auto-detect | Passing BCP-47 codes if the installed Whisper expects names. |
| `recognize_faster_whisper` | Faster-Whisper options: commonly two-letter codes like `en`, `fr` | Passing full language names when the backend expects codes. |
| `recognize_openai` / `recognize_groq` | provider API language field, commonly ISO language code such as `en` | Passing `en-US` when provider expects `en`, or using unsupported model/language pairs. |
| `recognize_cohere_api` | required keyword-only `language`, for example `en` or `ja` | Omitting `language` entirely. |
| Legacy Wit.ai | language configured in the app | Trying to pass `language` to `recognize_wit`. |

## Sphinx keyword and grammar failures

- `keyword_entries` must be a list/tuple of `(keyword, sensitivity)` pairs with sensitivity between `0` and `1`.
- If `keyword_entries` is present, `grammar` is ignored. Remove keywords when testing grammar behavior.
- A missing grammar path raises `ValueError` before recognition.
- A JSGF grammar can generate a `.fsg` file next to the grammar; use a writable working copy if you expect generation.
- Missing Sphinx data paths raise `RequestError` messages naming the missing HMM directory, language model file, or pronunciation dictionary.
- PocketSphinx keyword output can differ across PocketSphinx versions; compare words rather than exact order when appropriate.

Use `scripts/sphinx_keyword_grammar_template.py --help` for an argument-checked starting point.

## Vosk model not found

If `recognize_vosk` raises `SetupError` saying the Vosk model was not found:

1. Install the `vosk` Python extra if missing.
2. Use the CLI/model setup sub-skill for `sprc download vosk` because the model location is tied to the installed package layout.
3. Re-run a tiny file recognition with `verbose=True` to confirm the parsed JSON shape.

The wrapper does not accept a model path parameter in 3.17.0; changing model location requires package-level setup or code adaptation outside this operating skill.

## Local Whisper model/runtime issues

- First use may download model weights; budget time and disk space before calling it in production.
- For CPU-only environments, choose smaller models and pass backend-specific options such as `fp16=False` for Whisper or `init_options={"compute_type": "int8"}` for Faster-Whisper when appropriate.
- If `soundfile` cannot read the in-memory WAV, verify the input `AudioData` came from valid file/capture flow; route file format issues to `audio-data`.
- `show_dict=True` is useful for language detection and segment-level debugging.

## Async legacy service polling

`recognize_amazon` and `recognize_assemblyai` may raise `TranscriptionNotReady` instead of returning text on the first call. The exception carries a `job_name` attribute in source. Persist the job id outside secret-bearing logs and poll later with `audio_data=None` and that `job_name`. `TranscriptionFailed` signals provider-side terminal failure.

## Helper script safety

- `scripts/transcribe_file.py` defaults to inspect mode and does not contact cloud services unless `--engine` is explicitly set to a real engine.
- Cloud engines in the helper require explicit engine choice and, for engines with direct credential arguments, explicit credential options or environment variables.
- Use `--show-all`, `--verbose-result`, `--show-dict`, or `--with-confidence` only with engines that support them.
