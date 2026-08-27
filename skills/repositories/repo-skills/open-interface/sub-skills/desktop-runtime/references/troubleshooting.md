# Desktop Runtime Troubleshooting

## Purpose

Use this reference when Open Interface fails to launch, cannot configure a
provider, loops on a request, produces malformed JSON, cannot screenshot, or
runs the wrong desktop action.

## Quick triage

1. Separate contract failures from live desktop failures.
   - Contract failures can be checked with `python scripts/inspect_action_map.py
     --input-json sample.json --pretty`.
   - Desktop failures require a real display, OS permissions, and careful manual
     approval.
2. Separate provider configuration from action execution.
   - Missing keys, invalid base URLs, provider errors, or malformed JSON happen
     before pyautogui matters.
   - Active-window, screenshot, mouse/keyboard, and display failures happen
     after the provider returns usable steps.
3. Never paste API keys into logs, prompts, or test reports.

## Missing or invalid API key

Symptoms:

- Startup status says to set an OpenAI API key and restart.
- Provider client construction or first request raises authentication errors.
- Gemini or custom endpoints fail immediately despite a valid-looking request.

Likely causes:

- `api_key` is absent from settings.
- Key belongs to the wrong provider.
- The custom OpenAI-style endpoint expects a dummy key but none was provided.
- Settings were changed but the app was not restarted, so the old `LLM` object
  is still active.

Recovery:

1. Open Settings and enter the provider key, or prepare the settings JSON
   without exposing the secret.
2. For Gemini model names, use a Gemini API key. For OpenAI and OpenAI-style
   models, use the OpenAI-compatible key expected by that endpoint.
3. Restart the app after changing `api_key`, `model`, or `base_url`.
4. If the account needs billing or model access, resolve it outside the app.

## Custom model base URL failures

Symptoms:

- Custom model requests fail with connection, 404, unsupported route, or schema
  errors.
- Local Llama/Llava-style server receives no request or rejects the path.

Likely causes:

- Base URL does not expose an OpenAI-compatible API.
- Missing `/v1/` suffix.
- Model name does not match the local server.
- The server ignores keys but the runtime still needs a placeholder key value.

Recovery:

1. Confirm the endpoint implements OpenAI-style chat completions for the chosen
   custom model path.
2. Include the correct `/v1/` base path when required.
3. Set a provider-accepted model name.
4. Enter a non-empty dummy key only when the local server documentation says it
   ignores credentials.

## Malformed JSON response or missing `done`

Symptoms:

- Console prints JSON parsing errors.
- `Core` retries with an added valid-JSON reminder.
- The app keeps looping even though the user task is complete.
- A response contains prose before or after the JSON object.

Likely causes:

- The model did not follow the strict response contract.
- `done` is missing, not `null`, or never set to a completion string.
- The prompt context is too long or a custom model lacks reliable JSON behavior.

Recovery:

1. Save the non-secret response body and validate it with the bundled helper.
2. Ensure the response is a single JSON object with `steps` and `done` keys.
3. When work is complete, set `steps` to an empty list and `done` to a string.
4. For custom models, strengthen system instructions or use a provider/model
   with reliable JSON output.

## Unsupported function or wrong parameters

Symptoms:

- Console says there is no such function in the interface interpreter.
- `Interpreter.process_command()` prints the command and then returns false.
- A pyautogui call raises a `TypeError` because parameter names are wrong.

Likely causes:

- The model returned a function name that is neither `sleep` nor a pyautogui
  function.
- Parameters use a name unsupported by pyautogui.
- The response used `write` with a non-text payload, or `hotkey` with malformed
  keys.

Recovery:

1. Validate the response schema first.
2. Use supported step shapes from [api-reference.md](api-reference.md).
3. For `write`, prefer `string` and a small `interval`.
4. For `press`, use `key` for a single key or `keys` for a list.
5. For `hotkey`, use a list of key names such as `["command", "space"]` on
   macOS Spotlight.

## Headless Linux or missing display

Symptoms:

- Importing modules that import pyautogui raises a `DISPLAY` key error or Xlib
  display connection error.
- Screenshot calls fail before any model request.
- Tk window creation fails in SSH/CI.

Likely causes:

- The app is running without an interactive graphical display.
- `DISPLAY` is unset or points to a missing X server.
- Container/SSH environment lacks desktop passthrough.

Recovery:

1. Do not run live GUI automation in headless production or CI by default.
2. Use bundled static helpers for contract checks.
3. If a real runtime test is required, move to an interactive desktop session
   with a working display and user approval.
4. Treat virtual display solutions as separate host setup; do not silently add
   them during repo-skill verification.

## macOS Accessibility or Screen Recording permissions

Symptoms:

- The app launches but cannot move/click/type.
- Screenshots are blank, stale, or unavailable.
- System prompts ask for Accessibility or Screen Recording access.

Likely causes:

- Permissions were not granted to the app or Python/interpreter process.
- The app was moved/rebuilt after permissions were granted and macOS treats it
  as a different executable.

Recovery:

1. Grant Accessibility permission to the launched app or Python executable.
2. Grant Screen Recording permission.
3. Restart the app after changing permissions.
4. For packaged apps, if permissions worked in source but not in the binary,
   route resource/signing/build identity questions to `../packaging/`.

## Screenshot or local-context failures

Symptoms:

- Provider prompt lacks correct screen size or local app names.
- `Screen.get_screenshot*()` fails.
- The model acts on stale or wrong visual state.

Likely causes:

- No screen permission/display.
- The wrong monitor or desktop is active; the app only sees the primary display.
- A window is not foregrounded before typing.

Recovery:

1. Confirm the primary display contains the target application.
2. Bring the correct app/window to the foreground before typing.
3. Prefer keyboard navigation and short model action batches.
4. Ask for a new screenshot after complex navigation rather than sending many
   blind actions.

## PyAutoGUI warm-up surprises

Symptoms:

- A `command` key press appears before the intended action.
- Headless tests fail even before executing the requested pyautogui function.

Likely cause:

- The interpreter intentionally calls `pyautogui.press("command", interval=0.2)`
  before executing each command as a warm-up.

Recovery:

1. Avoid live interpreter execution in automated tests unless the desktop is
   prepared for this behavior.
2. Use the bundled contract helper to validate JSON/action mapping without
   touching the keyboard.
3. If editing the app, consider making warm-up behavior platform-aware and
   covered by tests before changing it.

## Stop/interrupt appears ineffective

Symptoms:

- The UI Stop button closes the window but a background action continues briefly.
- Status says `Interrupted` only after the current action finishes.

Likely causes:

- The interrupt flag is checked between steps, not inside long pyautogui calls
  or `sleep` calls.
- Daemon threads may still be unwinding.

Recovery:

1. Prefer short action batches and short sleeps in model responses.
2. Use Stop early when behavior looks wrong.
3. For development changes, consider finer-grained cancellation only with a
   safe test plan.

## Provider API errors and cost/loop control

Symptoms:

- Provider returns rate-limit, billing, quota, overload, or model-access errors.
- A request requires many screenshots/model calls and costs more than expected.

Likely causes:

- Account billing/model access is not ready.
- Backend overloaded or transiently unavailable.
- The model performs too few or too many actions per screenshot loop.

Recovery:

1. Do not retry rapidly on quota or billing failures; fix account/provider state.
2. On transient overload, wait and retry the same safe request.
3. Keep model responses to a few simple steps, then request a new screenshot.
4. Ensure `done` is set promptly when complete.
