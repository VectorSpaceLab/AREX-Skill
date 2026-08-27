# Web-interface workflows

## 1. Build and launch

The application entrypoint should do the work in this order:

1. Load environment variables and the medical assistant prompt.
2. Resolve a writable, private temporary directory. Create it before making the
   interface; do not use a world-writable directory or a client-provided path.
3. Initialize the selected tools and the chat model, then construct the agent.
   Pass the same initialized tool instances to `create_demo(agent, tools_dict)`.
4. Build the Gradio `Blocks` object. Keep upload and display components separate
   from the chat history component.
5. Validate launch configuration with the bundled checker when applicable.
6. Call `demo.launch(...)` only after reviewing bind address, port, share mode,
   queue/concurrency settings, and the intended audience.

`create_demo` creates a `ChatInterface` instance whose callbacks close over that
instance. The text event chain is:

```text
textbox.submit(add_message)
    -> then(process_message)
    -> then(re-enable textbox)
```

`add_message` appends a user message containing the selected file path (if any)
and then appends the text. The path chosen by the current code is
`original_file_path or display_image`. `process_message` receives the current
text, displayed image, and messages-style `ChatMessage` history, creates a
thread ID when none exists, calls `agent.workflow.stream`, and yields UI
updates. Treat this object as single-session unless its state is moved into
Gradio session state.

## 2. Image upload

An ordinary image upload should follow this sequence:

1. Reject missing input, unsupported suffixes, oversized files, and paths that
   are not regular files.
2. Copy it to the controlled upload directory under a generated basename while
   preserving a safe lower-case suffix.
3. Set both the agent path and display path to the validated copy.
4. Return only the display path to the image component.
5. When the user submits text, put the agent path in the `image_path:` message
   and use the display path for the multimodal image payload.

Do not assume a browser path remains available after the callback returns. Do
not render an arbitrary string returned by a tool as a file without checking
that it is an expected file and, where possible, inside the private result
root.

## 3. DICOM upload with separate paths

The current adapter copies a `.dcm` file and calls
`tools_dict["DicomProcessorTool"]._run(saved_path)`. The expected interface
contract is a two-value return whose first value is a mapping containing
`image_path`; that image path is assigned to `display_file_path`.

The robust message sequence is:

```text
original_file_path = private/upload/upload_<id>.dcm
display_file_path  = private/result/<converted>.<viewable-suffix>

path message      -> image_path: private/upload/upload_<id>.dcm
image_url payload -> bytes from display_file_path, with image/png (or actual MIME)
image component   -> display_file_path
```

This preserves DICOM metadata and the original file for tools while giving a
vision-capable model viewable pixels. Reading `original_file_path` and labeling
those bytes as `image/jpeg`, as the unadapted implementation does, is unsafe
and can produce an invalid multimodal request. If conversion fails, retain the
original path only for a diagnostic response; do not show the DICOM bytes as an
image.

If DICOM is optional, disable the DICOM upload control when the processor is not
in `tools_dict`, or return a precise UI error before copying the file. Generic
`file_types=["file"]` is intentionally broader than DICOM and must be followed
by suffix and content validation.

## 4. Streaming events

The expected event families in the adapter are:

```python
{"process": {"messages": [latest_message, ...]}}
{"execute": {"messages": [tool_message, ...]}}
```

For `process`, append non-empty latest content as an assistant message. For
`execute`, append a compact, human-readable tool result and, for an emitted
`image_visualizer` result, append a message whose content is the validated
image path. Yield after each meaningful event so the UI streams progress.

The current result code uses `eval(message.content)[0]`. Replace it with one of:

- a structured mapping returned directly by the tool;
- a JSON decoder when the contract is JSON; or
- `ast.literal_eval` only for a legacy Python-literal contract, followed by
  strict type, key, suffix, and root checks.

Never parse model-controlled content as executable Python. Normalize result
text without leaking private paths or sensitive metadata. Preserve a consistent
three-element output tuple on success, provider errors, tool errors, and
cancellation.

## 5. Chat state transitions

- **First submit:** allocate a unique thread ID and use it in the
  `configurable.thread_id` option on every stream call for that session.
- **Additional submit:** reuse the session thread so the graph checkpointer can
  maintain context; do not infer graph state from the rendered Gradio list.
- **Clear Chat:** clear rendered messages and image. Decide whether to rotate
  the thread; for a true privacy/conversation reset, rotate it and discard
  path references.
- **New Thread:** rotate the thread ID while retaining the selected image only
  if the UI explicitly supports that workflow. Never retain a stale thread ID
  after presenting a new conversation.
- **Upload during a stream:** disable or serialize uploads for that session, or
  snapshot the paths at submit time. Otherwise a later upload can change the
  instance fields while an earlier request is still running.

A timestamp alone is not a sufficient multi-user identifier. Use a random UUID
(or an equivalent server-generated opaque ID) and scope it to a browser session.
Do not put patient identifiers in a thread ID, filename, or event log.
