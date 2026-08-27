# Configuration Reference

`set.ini` is a simple key-value file. The parser ignores blank lines and `;` comments, then interprets values like this:

- `true` / `false` become booleans
- digit-only values become integers
- comma-separated values become lists
- every other value is lowercased before use

That lowercasing matters for any string value you expect to remain case-sensitive.

## Key fields

| Key | Default | Effect | Notes |
| --- | --- | --- | --- |
| `web_address` | `127.0.0.1:9977` | Host and port passed to the WSGI server. | Use a plain `host:port` value, not a URL. |
| `lang` | locale-derived `zh` or `en` | Chooses the UI language. | Blank means the app inspects the system locale; Chinese locale maps to `zh`, everything else to `en`. This does **not** choose the transcription language. |
| `devtype` | `cpu` | Selects the Whisper device. | Set to `cuda` only when the CUDA stack is ready. If the host has CUDA but you want CPU mode, leave this on `cpu`. |
| `cuda_com_type` | `float32` | Parsed and exposed in config. | The observed `start.py` model creation path does not pass this into `WhisperModel`, so it has no current inference effect. |
| `beam_size` | `5` | Beam-search width used during transcription. | Lower values usually use less memory. |
| `best_of` | `5` | Sampling fallback depth used during transcription. | Lower values usually use less memory. |
| `vad` | `true` | Enables voice activity detection. | `false` can reduce resource use. |
| `temperature` | `0` | Controls API-path temperature sampling. | The GUI worker path does not pass this into `WhisperModel`; the API path does. |
| `condition_on_previous_text` | `false` | Controls whether later segments depend on prior text. | `false` is the safer low-memory default. |
| `initial_prompt_zh` | simplified Chinese prompt | Initial prompt for Chinese runs. | When blank, the app fills a default prompt; `opencc` can change the prompt text between simplified and traditional. |
| `model_list` | a comma-separated model list | Populates the model dropdown in the browser UI. | Values should match valid Faster-Whisper model names or pre-downloaded cache folders. |
| `opencc` | `t2s` | Text conversion mode. | `t2s` converts traditional text to simplified; `s2t` does the reverse. Any other value disables OpenCC conversion. |

## Device selection

`devtype` is the main startup switch:

- `cpu` starts the server in CPU mode.
- `cuda` asks Faster-Whisper to use CUDA.

The app does not auto-switch `devtype` based on detected hardware. A machine can have CUDA available and still run in CPU mode if `devtype=cpu` stays in `set.ini`.

## Language defaults

Two different language decisions happen at runtime:

1. `lang` in `set.ini` decides whether the interface uses Chinese or English labels.
2. The per-request transcription language comes from the browser selector or API form data.

When `lang` is blank, the UI language falls back to the system locale. When `lang` is `zh`, the app also points Hugging Face downloads at the `hf-mirror.com` endpoint.

## Model list and first-run downloads

`model_list` controls the visible model choices. The startup code then loads the chosen model lazily:

- the GUI queue path loads the model when the first transcription task arrives
- the API path loads the model for that request

If the corresponding model folder is missing from `models/`, Faster-Whisper may try to download it. That is normal for a fresh setup, but it becomes a startup problem when the host is offline or the selected model cannot be fetched.

## Practical defaults

For a first launch:

- leave `lang` blank if you want locale-based UI labels
- keep `devtype=cpu` until the CPU launch works
- keep `beam_size`, `best_of`, and `condition_on_previous_text` at their defaults
- keep `opencc=t2s` unless you specifically need traditional output
