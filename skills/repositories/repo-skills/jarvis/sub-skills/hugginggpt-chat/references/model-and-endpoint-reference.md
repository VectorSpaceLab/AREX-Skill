# Model catalog, endpoint modes, and token helpers

Source evidence names: hugginggpt/server/awesome_chat.py; hugginggpt/server/models_server.py; hugginggpt/server/data/p0_models.jsonl; hugginggpt/server/get_token_ids.py; config.default.yaml; config.lite.yaml; config.gradio.yaml; config.azure.yaml.

## Catalog facts

The source catalog `p0_models.jsonl` contains 673 JSONL rows across 24 Hugging Face pipeline task labels. Most task labels have 30 candidate rows; document question answering has 22, visual question answering has 13, and text-to-video has 8.

Task labels present in the catalog:

- NLP: `text-classification`, `token-classification`, `text2text-generation`, `summarization`, `translation`, `question-answering`, `conversational`, `text-generation`, `sentence-similarity`, `tabular-classification`.
- Vision/document: `object-detection`, `image-classification`, `image-to-image`, `image-to-text`, `text-to-image`, `image-segmentation`, `depth-estimation`, `document-question-answering`, `visual-question-answering`, `text-to-video`.
- Audio: `text-to-speech`, `automatic-speech-recognition`, `audio-to-audio`, `audio-classification`.

High-like examples observed in the source catalog include `runwayml/stable-diffusion-v1-5` for text-to-image, `bigscience/bloom` for text-generation, `facebook/bart-large-cnn` for summarization, `sentence-transformers/all-MiniLM-L6-v2` for sentence similarity, `openai/whisper-large-v2` for ASR, `nlpconnect/vit-gpt2-image-captioning` for image-to-text, and `facebook/detr-resnet-50` for object detection. Do not dump the whole catalog into user-facing answers; summarize by task, availability, and a few relevant examples.

## ControlNet task labels are source-defined, not catalog rows

Task-planning prompts and execution logic also support ControlNet-style tasks:

- Preprocessor/control tasks: `canny-control`, `hed-control`, `mlsd-control`, `normal-control`, `openpose-control`, plus source model-server support for `midas-control` and `scribble-control`.
- Text-to-image control tasks: `canny-text-to-image`, `depth-text-to-image`, `hed-text-to-image`, `mlsd-text-to-image`, `normal-text-to-image`, `openpose-text-to-image`, `seg-text-to-image`.

These are local-only in the source chat controller. When a task ends with `-control` or `-text-to-image` and `inference_mode` is not `huggingface`, the controller chooses a local model id such as `canny-control` or `lllyasviel/sd-controlnet-canny`. When `inference_mode: huggingface`, the controller records an error saying the service related to ControlNet is unavailable and that ControlNet must be deployed locally.

For usability case 2 in the parent brief: if a user asks for canny/ControlNet generation while their config says `inference_mode: huggingface`, explain the local-only path and do not claim remote Hugging Face Inference API support.

## Candidate and availability algorithm

For non-ControlNet, non-LLM-direct tasks:

1. The controller groups catalog rows by `task` into `MODELS_MAP`.
2. For a planned task, it takes the first 10 candidate models for that task.
3. It probes availability depending on `inference_mode`:
   - If mode is not `local`, it calls the Hugging Face model status endpoint for candidates.
   - If mode is not `huggingface` and `local_deployment` is not `minimal`, it also calls local `/status/<model_id>`.
4. It stops after enough available models are found, bounded by `num_candidate_models`.
5. If no model is available, it records an inference error for that task.
6. If exactly one model is available, it uses that model.
7. If multiple models are available, it asks the controller LLM to choose one from truncated metadata.

Direct-controller tasks:

- `summarization`, `translation`, `conversational`, `text-generation`, and `text2text-generation` are delegated to the controller LLM rather than a Hugging Face expert model.

## Remote Hugging Face inference behavior

The remote path requires a valid Hugging Face token in config or `HUGGINGFACE_ACCESS_TOKEN`. Source behavior includes:

- NLP tasks via `huggingface_hub.InferenceApi` for question answering, sentence similarity, classification, token classification, text2text, summarization, translation, conversational, and text generation.
- Vision tasks via a mix of `InferenceApi` and HTTP requests to model-specific API-inference URLs.
- Audio tasks via `InferenceApi` or HTTP downloads of the audio URL.
- Generated artifacts are written under relative `public/images`, `public/audios`, or `public/videos` in the chat server's working directory when the source code saves remote outputs.

Remote mode is lightweight but fragile because availability depends on Hugging Face hosted model status and task support. A task that plans correctly may still fail in `/results` if no candidate model is loaded or if the Inference API shape differs for that model.

## Optional local model-server behavior, unverified here

The optional local expert server is implemented by `models_server.py`. This sub-skill read the source but did not install or execute the heavy local stack. Treat the following as source behavior requiring separate validation:

- Startup imports many heavyweight packages: Transformers, Diffusers, Torch, Torchaudio, datasets, ControlNet auxiliary detectors, ESPnet, Asteroid, SpeechBrain-related components, Flask, Waitress, and more.
- It reads `local_inference_endpoint.port`, `local_deployment`, `device`, and optional `proxy` from config.
- It serves:
  - `GET /running` returning `{"running": true}`;
  - `GET /status/<model_id>` returning `{"loaded": true}` only for loaded, non-disabled models;
  - `POST /models/<model_id>` for model-specific inference.
- `local_deployment: minimal` loads ControlNet-related pipes; `standard` adds common ASR, depth, segmentation, object detection, document QA, image-to-text, VQA, and similar pipelines; `full` adds additional image, video, audio, and diffusion pipelines.
- Local models are expected under a relative `models` folder in the server working directory.
- Device defaults to `cuda:0` in default-style configs. CPU use is not proven by this sub-skill.

Do not send a user into local model downloads or CUDA debugging for lite-mode credential failures. Use the config inspector first.

## Local endpoint payload patterns

Source-defined local payload shapes include:

| Model/task family | Local POST body shape |
|---|---|
| ControlNet text-to-image model ids beginning `lllyasviel/sd-controlnet-` | `{"img_url": "...", "text": "..."}` |
| Control preprocessors ending `-control` | `{"img_url": "..."}` |
| Text-to-video | `{"text": "..."}` |
| Question answering or sentence similarity | Original task `args` JSON. |
| Text classification/token classification/text2text/summarization/translation/conversational/text generation | Original task `args` JSON. |
| Depth, segmentation, image-to-image, object detection | Usually `{"img_url": "..."}`. |
| Image-to-text, image classification, document QA, VQA | `{"img_url": "...", "text": "..."}` when text is present. |
| Text-to-speech | Original task `args` JSON. |
| ASR/audio-to-audio/audio-classification | `{"audio_url": "..."}`. |

## Token helper facts

The source helper `get_token_ids.py` uses `tiktoken` encodings:

- `cl100k_base` for GPT-4 and GPT-3.5 chat models;
- `p50k_base` for `text-davinci-003` and `text-davinci-002`;
- `r50k_base` for earlier completion models.

Max context table highlights:

- `gpt-4`: 8192;
- `gpt-4-32k`: 32768;
- `gpt-3.5-turbo` and `gpt-3.5-turbo-0301`: 4096;
- `text-davinci-003` and `text-davinci-002`: 4096;
- earlier completion models listed in the helper: 2049.

Installed-package facts already verified for this repo-skill draft:

- `count_tokens(model_name, text)` and `get_max_context_length(model_name)` imported with `tiktoken==0.3.3`.
- `get_token_ids_for_task_parsing('text-davinci-003')` returned 67 unique ids.
- `get_token_ids_for_choose_model('text-davinci-003')` returned 6 unique ids.
- Full `awesome_chat.py` and `models_server.py` execution was not installed or verified because the local model stack is optional and out of scope for this sub-skill.

## When to explain catalog versus endpoint issues

- If `/tasks` returns a plausible plan but `/results` says no available models, focus on endpoint availability and candidate status checks.
- If the task label is not in `MODELS_MAP`, focus on planning prompt/task vocabulary mismatch.
- If the task is ControlNet-related and mode is `huggingface`, explain local-only ControlNet.
- If mode is `hybrid` and startup fails before any route is served, check the local `/running` gate before debugging model selection.
- If generated files are referenced with `/images/...`, `/audios/...`, or `/videos/...`, remember those are static paths served by the chat API's `public` folder.
