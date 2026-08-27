# UI Workspace Troubleshooting

## Qt import warnings or crashes

Recovery:

- Set `QT_QPA_PLATFORM=offscreen` in headless shells.
- Use `QCoreApplication` before QObject/model imports.
- Use `QApplication` before widgets.
- Prefer static enum inspection when the full plugin cannot import.

## Generate button does nothing

Likely causes:

- Document color mode check failed.
- Connection is not `connected` or client models are unavailable.
- Current style is unsupported by discovered client models.
- Custom workflow validation error blocks generation.
- Upscale workspace `can_generate` is false.
- Live/custom mode is already active or waiting for queued work.

Recovery:

1. Inspect `DocumentModel.error` and `ConnectionState`.
2. Check whether supported styles were filtered after connection.
3. If custom workspace is active, route to `custom-graphs` and inspect
   validation errors.
4. If server resources are missing, route to `server-resources`.

## Job queued but no result appears

Likely causes:

- Server/client disconnect during generation.
- Job was canceled by `QueueMode.replace` or user action.
- Output was a text/custom output rather than an image history item.
- Apply behavior created a layer in an unexpected location.

Recovery:

- Check `JobState`, selected job, and progress kind.
- Inspect client/server events and `ErrorKind`.
- For custom outputs, inspect Graph workspace output nodes.
- For layer placement, inspect apply settings and document/layer APIs.

## Wrong workspace handles the task

Symptoms:

- A custom graph runs as regular generation.
- Upscale settings ignored.
- Live preview keeps generating when the user expects manual generation.

Recovery:

- Check `DocumentModel.workspace` and child workspace mode flags.
- Disable live mode before ordinary generation when necessary.
- Confirm Graph workspace `workflow_id` and mode.
- Confirm the active docker/workspace selection, not just visible controls.

## Validation warning appears

`ErrorKind.validation_warning` is used for non-fatal validation issues such as
custom graph problems. Do not treat it as a server crash. Route to the owning
workspace and fix the validation source; clearing the validation source clears
the warning.

## Reconnect behavior is confusing

A sporadic disconnect can cancel or lose the current job while a quick reconnect
allows new generation. Do not promise that a disconnected in-flight job will be
recovered unless the client/server protocol provides output after reconnect.
Collect the job state and connection event sequence before advising retry.
