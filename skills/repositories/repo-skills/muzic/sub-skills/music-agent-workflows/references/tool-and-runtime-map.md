# MusicAgent tool and runtime map

## Internal runtime stages

MusicAgent is driven by four prompt bundles inside the wrapper.

| Stage | Role | Output |
|---|---|---|
| TaskPlanner | Turn the user request into a JSON task list with ids, dependencies, and arguments. | A task array, or `[]` if the request cannot be parsed. |
| ToolSelector | Choose one tool from the loaded candidate list for a task. | A strict JSON object with the selected pipe id and a reason. |
| Responder | Summarize the task graph and inference results for the user. | A friendly final response plus a compact process log. |
| ChatBot | Fallback when no task is detected or task parsing fails. | Direct chat answer. |

## Planner vocabulary versus loaded pipes

The planner can mention tasks that do not currently have a loaded pipe implementation. Those tasks will fail later unless the plugin layer is extended.

| Planner task | Candidate tool ids | Loaded pipe in current wrapper? | Notes |
|---|---|---|---|
| `lyric-generation` | ChatGPT fallback | Yes, via the chat path | This task bypasses the pipe registry. |
| `text-to-sheet-music` | `sander-wood/text-to-music` | No | The task vocabulary exists, but the loader does not instantiate a matching pipe. |
| `text-to-audio` | `cvssp/audioldm-m-full` | Yes | AudioLDM-backed text-to-audio. |
| `music-classification` | `lewtun/distilhubert-finetuned-music-genres`, `dima806/music_genres_classification` | Yes | `candidate_tools` limits the shortlist before selection. |
| `lyric-to-melody` | `muzic/roc`, `muzic/telemelody` | Partial | ROC is loaded; the TeleMelody candidate is not currently instantiated. |
| `lyric-to-audio` | `DiffSinger` | Yes | GPU-oriented initialization in the current code. |
| `web-search` | `google-search` | Yes | Uses Google Custom Search credentials. |
| `artist-search` | `spotify` | Yes | Spotify API search. |
| `track-search` | `spotify` | Yes | Spotify API search. |
| `album-search` | `spotify` | Yes | Spotify API search. |
| `playlist-search` | `spotify` | Yes | Spotify API search. |
| `separate-track` | `demucs` | Yes | Shells out to the Demucs CLI. |
| `lyric-recognition` | `jonatasgrosman/whisper-large-zh-cv11` | Yes | The current loader is CUDA-leaning and should be treated carefully on CPU-only hosts. |
| `score-transcription` | `basic-pitch` | Yes | Shells out to the Basic Pitch CLI. |
| `timbre-transfer` | `ddsp` | Yes | Uses the local DDSP/TF stack and a soundfont. |
| `accompaniment` | `getmusic` | No | The task vocabulary exists, but there is no matching pipe in the current wrapper. |
| `audio-mixing` | `basic-merge` | Yes | Local merge helper. |
| `audio-crop` | `basic-crop` | Yes | Local crop helper. |
| `audio-splice` | `basic-splice` | Yes | Local splice helper. |

## Loaded pipe keys and runtime notes

The `disabled_tools` setting is matched against the pipe keys, not against the planner's task names.

| Pipe key | Backend / asset family | Runtime note |
|---|---|---|
| `muzic/roc` | Fairseq LM, ROC helper code, checkpoint tree, ROC database, and `MS Basic.sf3` | Needs the helper tree to satisfy its imports. |
| `cvssp/audioldm-m-full` | Diffusers audio generation cache | GPU-leaning and heavyweight. |
| `DiffSinger` | DiffSinger model bundle | CUDA-oriented initialization in the current code. |
| `dima806/music_genres_classification` | Hugging Face audio classifier | CPU inference after the model cache is present. |
| `lewtun/distilhubert-finetuned-music-genres` | Hugging Face audio classifier | CPU inference after the model cache is present. |
| `jonatasgrosman/whisper-large-zh-cv11` | Hugging Face ASR cache | Large model; keep an eye on device availability and memory. |
| `spotify` | Spotify Web API | Requires client credentials and network access. |
| `ddsp` | DDSP / TensorFlow / soundfont | Local cache plus the audio synthesis runtime. |
| `demucs` | Demucs CLI | Shells out to the external command. |
| `basic-merge` | Local audio mixing | Pure local helper, no model cache. |
| `basic-crop` | Local audio trimming | Pure local helper, no model cache. |
| `basic-splice` | Local audio concatenation | Pure local helper, no model cache. |
| `basic-pitch` | Basic Pitch CLI | Shells out to the external command. |
| `google-search` | Google Custom Search API | Requires API key and custom search engine id. |

## Tool-selection troubleshooting

- If the task planner returns a supported task but the tool selection fails, check whether the pipe key is listed in `disabled_tools`.
- If the task planner returns a task with no loaded pipe, the wrapper will emit an "unloaded models" path. That is expected for the aspirational task ids listed above.
- If multiple pipes are available for a task, `candidate_tools` limits the shortlist before the semantic tool selector runs.
- If the UI or CLI finds the wrong tool, remember that the selector only sees loaded pipe ids and the task description; it cannot choose a pipe that was never instantiated.
- For the current snapshot, `text-to-sheet-music`, `lyric-to-melody` via TeleMelody, and `accompaniment` are the main planner-vs-loader mismatches to watch.
