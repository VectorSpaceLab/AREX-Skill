# Web-interface troubleshooting

## Gradio API drift

**Symptoms:** import failure for `ChatMessage`, rejected `type="messages"`,
changed upload callback values, or a `.then` chain with incompatible outputs.

**Checks and fixes:** inspect the installed Gradio version and run a tiny
component-construction smoke test before starting a model. Keep the messages
history representation consistent with the installed API. If the installed
version cannot support the current callback signatures, pin a compatible
version or add a narrow compatibility adapter; do not silently mix old tuple
history and messages-style history. Confirm every callback returns exactly the
components declared in `outputs`.

## Permission and asset failures

**Symptoms:** `PermissionError` creating the temporary directory or a missing
avatar/logo error during Blocks construction.

**Checks and fixes:** choose a user-writable private temporary root, verify it
before initialization, and avoid privileged execution as a workaround. Resolve
assets from packaged resources or disable the avatar when absent. Do not use a
relative asset path that changes meaning with the launch directory.

## Upload path and suffix failures

**Symptoms:** an upload works for PNG but not DICOM, two fast uploads overwrite
each other, or the agent receives a browser-side path that later disappears.

**Checks and fixes:** copy into a generated private name, preserve the lower-case
suffix, validate regular-file status and size, and use a UUID rather than a
seconds-only filename. Accept `.dcm` explicitly for DICOM. Keep the copied
original and converted display path in separate fields and snapshot both at
submit time.

## DICOM processor missing or conversion failure

**Symptoms:** DICOM upload raises a key lookup error, `_run` returns an
unexpected shape, or the image component cannot display the result.

**Checks and fixes:** disable the DICOM upload control unless
`DicomProcessorTool` is present in `tools_dict`. Check that the adapter returns a
mapping with a non-empty `image_path`, that the path is an expected viewable
file, and that the display file still exists. Preserve the original `.dcm` for
tools but use converted pixels for the multimodal image payload. Do not feed raw
DICOM bytes under an image/JPEG MIME label.

## Stale thread or cross-user state

**Symptoms:** Clear Chat appears empty but the next answer remembers the old
conversation, a New Thread still sees old context, or one user's image appears
in another user's request.

**Checks and fixes:** remember that the basic adapter stores thread and paths on
one `ChatInterface` object. Clear visible state and rotate the checkpointer
thread when a true reset is required. Use per-browser/session state and opaque
unique IDs for multi-user deployments. Snapshot paths and thread ID before
starting an async stream; serialize or disable uploads during that stream.

## Malformed tool output or unsafe evaluation

**Symptoms:** a tool result crashes while formatting, an image path is missing,
or the UI executes unexpected content.

**Checks and fixes:** never use `eval(message.content)`. Require structured
returns, or parse only a legacy literal/JSON representation with a constrained
parser. Validate mappings, required keys, path roots, file existence, and
allowed image suffixes. Render only validated result files. Keep the UI's error
message generic and record a redacted server-side diagnostic.

## Tool-name mismatch

**Symptoms:** image results are shown as text, or a visualizer result is never
rendered.

**Checks and fixes:** distinguish initializer keys such as
`ImageVisualizerTool` from the runtime `message.name` (the current branch
checks `image_visualizer`). Log or inspect the non-sensitive emitted name and
map it explicitly. Do not make DICOM support depend on a visualizer tool unless
the selected workflow actually requires it.

## Port, bind, share, and network exposure

**Symptoms:** the app is unreachable locally, the port is occupied, or a public
share URL appears unexpectedly.

**Checks and fixes:** start with `127.0.0.1`, `share=False`, and an approved
unused port. Check the launch log for the actual bind and share state. Use a
broad bind only with an intentional authenticated boundary; treat `share=True`
as public exposure. Never expose temporary upload/result directories directly.
The bundled checker can reject unsafe settings in strict mode.

## Model/API errors in chat

**Symptoms:** the stream yields an exception, the model endpoint rejects the
request, or the UI displays an error after upload.

**Checks and fixes:** verify the configured endpoint and that the required API
key is present without printing it. Check model name, base URL compatibility,
network policy, context size, and tool availability. For a CPU utility smoke
test, use a deterministic stub workflow or a reachable lightweight compatible
model; do not initialize every heavyweight tool just to test the UI. Sanitize
exception text before showing it in chat, and always return the expected
three-output tuple on error.
