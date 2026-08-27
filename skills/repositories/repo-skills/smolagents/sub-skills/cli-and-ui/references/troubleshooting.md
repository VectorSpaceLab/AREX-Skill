# Troubleshooting CLI And UI

## Console Script Missing

Symptoms:

- `smolagent: command not found`
- `webagent: command not found`

Checks and fixes:

```bash
python -c "import smolagents; print(smolagents.__version__ if hasattr(smolagents, '__version__') else 'import ok')"
python -m pip show smolagents
python -m smolagents.cli --help
python -m smolagents.vision_web_browser --help
```

If module help works but the script is missing, reinstall the package in the active environment so project entry points are generated. If neither import nor module help works, install smolagents in the environment being used by the shell.

## Invalid Model Type

`ValueError: Unsupported model type: ...` means the CLI model loader does not recognize the supplied name. Use one of the installed-version names shown by `smolagent --help`; common non-interactive names are `InferenceClientModel`, `OpenAIModel`, `LiteLLMModel`, and `TransformersModel`.

Be careful with `OpenAIServerModel` in interactive prompts: if the installed code path does not implement that alias in the loader, switch to a supported API-backed class or construct the model in Python.

## Model Credentials Or Provider Failures

- `InferenceClientModel` can use `HF_API_KEY` or a value passed with `--api-key`.
- `OpenAIModel` defaults to a Fireworks-compatible base URL unless `--api-base` is supplied and can use `FIREWORKS_API_KEY`.
- `LiteLLMModel` usually expects provider-specific environment variables or an explicit `--api-key`/`--api-base` depending on the target model.
- For public docs and shared scripts, never hard-code API keys; refer to environment variables.

## Tool Name Failures

`Tool ... is not recognized either as a default tool or a Space` means the `--tools` entry is neither a built-in default tool name nor a Hugging Face Space ID containing `/`.

Fixes:

- Run bare `smolagent` to view the interactive list of available default tools.
- Use exact built-in names such as `web_search` when the toolkit extra is installed.
- For a Space tool, pass the full `owner/space_name` string.
- Install extras needed by the selected default tool, such as `smolagents[toolkit]` for web-search/visit-page style tools.

## Additional Imports Do Not Work

`--imports pandas numpy` only authorizes imports for the code-agent executor; it does not install packages. Install the required libraries first, and route executor trust or sandbox concerns to `execution-and-safety`.

## Gradio Missing

Symptoms mention `Please install 'gradio' extra to use the GradioUI`.

Fix:

```bash
python -m pip install 'smolagents[gradio]'
```

If Gradio is installed but UI construction fails, check for incompatible Gradio major versions and avoid passing custom Chatbot/ChatInterface arguments that conflict with the version in use.

## Browser Agent Dependencies Missing

`webagent` requires optional browser packages and a working browser stack. Install the vision/browser extras and verify Chrome/WebDriver availability:

```bash
python -m pip install 'smolagents[vision]'
python -c "import helium, selenium, PIL; print('browser deps ok')"
webagent --help
```

Common runtime failures:

- No Chrome/Chromium installed or not discoverable by Selenium.
- WebDriver/browser version mismatch.
- Headless or display-less server cannot open the visible browser window used by the demo.
- Corporate proxy or network blocks pages the browser task needs.
- Model lacks vision/screenshot understanding for hard navigation tasks.

For reliable automation, adapt the Python workflow and set explicit Selenium options rather than relying on the demo defaults.

## Interactive Prompt Confusion

Bare `smolagent` launches a setup wizard because the positional prompt is optional. If automation appears stuck, provide the prompt as a positional argument or pipe scripted answers only when the exact prompt sequence is known. Prefer explicit flags for CI or reproducible examples.

## UI Server Hangs

If a Starlette/FastAPI/async server becomes unresponsive, check whether `agent.run(...)` is blocking the event loop. Run it in a worker thread, task queue, or background job. Also ensure external clients are disconnected during shutdown.
