# Runtime Configuration

## Purpose

Read this when configuring model providers, API keys, default browser behavior,
custom model endpoints, UI theme, completion sound, or dependency prerequisites
for Open Interface.

## Installation and launch prerequisites

Open Interface is a Python desktop app. In a target checkout or source install,
the documented script path is:

```bash
python app/app.py
```

Use Python 3.12 or newer. The repository's dependency pins include OpenAI,
Google GenAI, Pillow, PyAutoGUI, ttkbootstrap, packaging, PyInstaller, PyAudio,
moviepy, and platform-specific macOS packages. Full GUI automation also needs:

- A real interactive desktop/display.
- Keyboard and mouse control permission where the OS requires it.
- Screen capture permission where the OS requires it.
- A configured model provider API key or compatible local endpoint.
- A primary display; the public notes warn that the app only sees the primary
  display when multiple monitors are connected.

Do not use this runtime configuration reference as a build/release dependency
plan. For PyInstaller and release artifacts, route to `../packaging/`.

## Settings file behavior

The settings object stores configuration under the user's home directory at:

```text
~/.open-interface/settings.json
```

Important behavior:

- The settings directory is created automatically.
- `save_settings_to_file()` merges new keys into any existing JSON file.
- `load_settings_from_file()` base64-decodes the stored `api_key` value when it
  is present.
- The API key is base64-encoded for storage, which prevents casual plain-text
  display but is not encryption. Treat the settings file as sensitive.
- Provider/model changes require restarting the app before the `LLM` object is
  reconstructed.

Observed setting keys:

| Key | Written by | Meaning |
|---|---|---|
| `api_key` | Settings window | OpenAI/Gemini/custom provider key. It is stored base64-encoded and exposed to the runtime after decoding. |
| `default_browser` | Settings window | Browser hint inserted into the model context when not empty; UI choices are Safari, Firefox, and Chrome. |
| `play_ding_on_completion` | Settings window | When true, `Core` prints a terminal bell after the model returns a `done` string. |
| `custom_llm_instructions` | Settings window | Extra user-provided context appended to the model prompt. |
| `theme` | Settings window | ttkbootstrap theme, such as `superhero`, `darkly`, `cyborg`, `journal`, or `solar`. |
| `base_url` | Advanced Settings window | Custom OpenAI-style API base URL. The runtime strips trailing slashes and appends one final slash. |
| `model` | Advanced Settings window | Provider/model selector; see the provider routing table below. |

## Provider and model selection

Default values:

- `model`: `gpt-5.2` when no model is saved.
- `base_url`: `https://api.openai.com/v1/` when no base URL is saved.
- `api_key`: no default; missing or invalid keys surface as startup/provider
  errors.

Built-in UI model options include:

| UI/model value | Backend route | Notes |
|---|---|---|
| `gpt-5.2` | GPT-5 Responses API | Default in the current code. |
| `computer-use-preview` | OpenAI computer-use preview tool | Converts returned computer actions into normal step dictionaries. |
| `gemini-3-pro-preview`, `gemini-3-flash-preview` | Google GenAI | Uses the API key with the Google client rather than an OpenAI base URL. |
| Older GPT-4o/GPT-4o-mini/GPT-4v/GPT-4-turbo values | OpenAI Assistants or chat completion variants | Kept as deprecated choices in the advanced settings UI. |
| Custom | GPT-4v-style OpenAI-compatible chat completion route | Useful for Llava, Llama, or other local endpoints exposed through an OpenAI-style API. |

Custom model caveats:

- The runtime requires some API-key value even for many local OpenAI-compatible
  endpoints; the public setup notes suggest a dummy value such as `xxx` when the
  local service ignores credentials.
- The custom base URL should point at an OpenAI-compatible API root and often
  needs a `/v1/` suffix.
- Non-OpenAI-compatible LLMs need an adapter/proxy that speaks the expected API.

## Prompt context inputs

The LLM context combines:

- The bundled text prompt resource that describes the JSON command contract and
  safety guidelines.
- Locally installed application names, when the platform allows listing them.
- The OS/platform string.
- Primary screen size from pyautogui.
- Optional default browser.
- Optional custom user guidance.

This means settings, OS permissions, and display availability can change the
prompt even when the same user request is submitted.

## OS-specific permission checklist

macOS:

- Grant Accessibility permission so the app can operate keyboard and mouse.
- Grant Screen Recording permission so screenshots can be captured.
- For unsigned or unverified binaries, use the normal macOS security approval
  flow before launching.
- The build notes mention extra care when Python from pyenv lacks Tk support.

Linux:

- Run from an interactive graphical session with a usable `DISPLAY` or
  equivalent display setup.
- PyAutoGUI and Tk dependencies may need system packages such as Tk development
  libraries or display-related packages, depending on the environment.

Windows:

- Use a normal interactive desktop session.
- If packaged as a onefile executable, route packaging-resource issues to the
  packaging sub-skill and runtime provider/screenshot issues back here.

## Safe configuration validation

Without launching the GUI or using credentials, you can still validate the
runtime contract helper:

```bash
python scripts/inspect_action_map.py --pretty
```

For settings changes, inspect the JSON shape and avoid printing secrets. Never
copy API keys into reports, prompts, logs, or generated skill files.
