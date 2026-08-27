# Desktop Runtime Workflows

## Purpose

Read this for practical runtime flows: safe inspection, manual launch, request
execution, stop/retry behavior, contract validation, and manual smoke-test
boundaries.

## Workflow 1: Safe runtime contract inspection

Use this when the task is to debug JSON/action conversion without moving the
real mouse or calling a provider.

1. Open this sub-skill directory in the generated skill tree.
2. Run the bundled helper:

   ```bash
   python scripts/inspect_action_map.py --pretty
   ```

3. Confirm the report returns `"ok": true` for built-in mapping cases.
4. To validate a saved computer-use action or LLM response, save it to a JSON
   file and run:

   ```bash
   python scripts/inspect_action_map.py --input-json sample.json --pretty
   ```

5. If you know the expected steps, save them to another JSON file and add
   `--expect-json expected.json`; the helper returns non-zero on mismatches.

This workflow is safe in headless environments because the helper does not
import pyautogui, create a Tk window, capture screenshots, or contact model
providers.

## Workflow 2: Manual launch in a target checkout

Use this only after confirming a real interactive desktop and provider settings
are available.

1. Create or activate a Python environment compatible with the application,
   preferably Python 3.12 or newer.
2. Install runtime dependencies for the selected platform. The public runtime
   path is the pinned dependency file, but be aware that PyAudio, Tk, and
   platform packages may need system packages.
3. Configure provider settings in the app UI or by preparing the settings JSON
   carefully. Avoid logging secrets.
4. Launch from the target checkout:

   ```bash
   python app/app.py
   ```

5. In the GUI, enter a low-risk request first, such as asking for a simple
   status or opening a harmless application. Do not start with destructive file
   edits or account actions.
6. Watch the status label. The app forwards each step's
   `human_readable_justification` from the model to the UI.
7. If behavior looks unsafe or stuck, press Stop or move the cursor to an OS
   safety corner if PyAutoGUI fail-safe behavior is available in the current
   setup.

## Workflow 3: Understand the request execution loop

The high-level runtime loop is:

1. `UI.MainWindow.execute_user_request()` reads the text entry and queues the
   request.
2. `App.send_user_request_from_ui_to_core()` reads the queue. If the request is
   `stop`, it interrupts and closes; otherwise it starts a daemon thread running
   `Core.execute_user_request()`.
3. `Core.execute_user_request()` stops any previous request, waits briefly, then
   calls `Core.execute(user_request, step_num=0)`.
4. `Core.execute()` calls the selected `LLM` backend with the user request,
   step number, prompt context, and screenshot.
5. The backend returns JSON containing `steps` and `done`.
6. `Core` processes each step through `Interpreter.process_command()`.
7. If `done` is a string, `Core` displays it and optionally plays a terminal
   bell. If `done` is `null`, `Core` queues another model call with
   `step_num + 1` and a fresh screenshot.

Key implication: when the model has completed the user task, it must set
`done` to a string and stop adding action steps. Otherwise the app can loop.

## Workflow 4: Manual smoke-test boundary

The repository includes a simple GUI smoke pattern that constructs an `App`,
starts a background thread, queues `Hello`, waits, then queues `Open Chrome`.
That pattern is useful evidence, but it is not an automated default for this
skill because it launches a GUI, needs a display, may use provider credentials,
and can move the real desktop.

If a future user explicitly approves an interactive smoke test, use this
checklist before adapting that pattern:

- Confirm the machine is an interactive desktop, not a headless SSH/CI session.
- Confirm the correct provider API key and model are configured.
- Confirm Accessibility and Screen Recording permissions on macOS.
- Start with harmless requests and keep the Stop button visible.
- Avoid modifying or overwriting user data.
- Record only high-level pass/fail and non-secret symptoms.

## Workflow 5: Diagnose provider or contract failures without live automation

1. Capture the provider response or action object if available, with secrets
   removed.
2. Validate JSON shape with the bundled helper.
3. Compare failures to the response schema in
   [api-reference.md](api-reference.md).
4. If the provider returns prose around JSON, malformed JSON, unsupported
   function names, or omits `done`, fix the provider prompt/configuration first;
   do not debug pyautogui until the schema is valid.
5. If schema is valid but a pyautogui action fails only on a live desktop, move
   to [troubleshooting.md](troubleshooting.md) for display, permissions, active
   window, and platform-specific checks.

## Workflow 6: Stop and recover from an unsafe or looping request

- Use the GUI Stop button for normal interruption. It queues a `stop` message,
  calls `Core.stop_previous_request()`, and destroys the main window.
- `Core.stop_previous_request()` sets `interrupt_execution = True`. The current
  `Core.execute()` loop checks the flag before each step, reports
  `Interrupted`, resets the flag, and returns.
- If the UI is unresponsive, use OS-level process controls or the pyautogui
  fail-safe corner if available. Prefer safe interruption over trying more
  model calls.
- After interruption, restart the app before changing provider settings or
  retrying a task that depended on stale screenshots.
