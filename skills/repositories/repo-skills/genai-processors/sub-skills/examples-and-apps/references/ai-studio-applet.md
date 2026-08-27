# AI Studio applet and WebSocket protocol

The applet examples use a Python processor backend and a browser frontend. The
backend is built with `genai_processors.dev.live_server.run_server`, and the
browser connects over WebSocket, usually `ws://localhost:8765`.

## Backend shape

```python
from genai_processors import processor
from genai_processors.dev import live_server


def processor_factory(config: dict) -> processor.Processor:
    # Read applet config and return a processor instance.
    return my_processor

await live_server.run_server(processor_factory, port=8765)
```

`processor_factory` receives the initial applet config. Do not read credentials
from the WebSocket payload unless the user intentionally designs that security
model; examples usually read API keys from server-side environment variables.

## Client-to-server messages

Every message is a JSON representation of a `ProcessorPart`.

- Initial config: send a part with MIME type `application/x-config` and config
  values in metadata.
- Text input: send text in the `part.text` field.
- Binary media: base64-encode bytes in `part.inline_data.data` and set
  `part.inline_data.mime_type`, for example `audio/l16;rate=24000`.
- Realtime media usually uses substream `realtime`.
- Control messages such as reset or mic off are metadata-only parts.

## Server-to-client messages

The server streams JSON `ProcessorPart` objects back. Clients should handle:

- `text/plain` for text output,
- `audio/*` for playable audio buffers,
- image MIME types for generated illustrations,
- `text/html` or UI-specific function-response blobs for widgets,
- internal state metadata such as `generation_complete`, `interrupted`, or
  `health_check`.

## Reserved or direct-output substreams

Some examples use reserved/direct substreams to bypass the model prompt and send
status or UI updates straight to the client. Preserve these substreams when
adapting widgets, live illustrator, or applets that stream status updates.

## Browser requirements

- Request microphone/camera permissions in the applet metadata when needed.
- Use browser echo cancellation for live voice apps when possible.
- Keep a visible connection status and handle WebSocket reconnects.
- Decode base64 audio/media and associate tool responses with their originating
  function call IDs when widgets or async tools are used.

## Server runtime cautions

- Avoid binding public interfaces unless the user explicitly wants remote access.
- Do not log API keys, microphone audio, camera frames, or private media.
- Add trace size limits for audio/video apps.
- Stop the server cleanly before restarting on the same port.
