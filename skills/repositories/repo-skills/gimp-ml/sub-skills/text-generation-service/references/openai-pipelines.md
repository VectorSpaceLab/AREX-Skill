# Pipeline and provider boundaries

The four service selectors are thin wrappers around remote OpenAI image
operations. This document records source behavior for planning and failure
classification; it is not permission to make a live call.

## `text_to_image`

The text-to-image tool posts to the OpenAI image generations endpoint and
requests `dall-e-3`, one image, with the prompt. The service passes the
request's `model` value as the provider `quality` value. The legacy bridge
presents `standard` and `hd` choices. The requested `image_shape` is used only
to select an aspect-ratio bucket:

- near square: provider size `1024x1024`;
- substantially taller: `1024x1792`;
- otherwise: `1792x1024`.

The source does not perform the commented final resize in this tool, so do
not promise that the returned shape equals the requested shape. The returned
remote image is opened into a NumPy array and converted to raw base64 output.

## `text_edit_image`

The edit tool creates an OpenAI client and calls `images.edit` with model
`dall-e-2`, one image, a prompt, and `1024x1024`. It derives an alpha mask from
black pixels in the supplied mask and may resize the downloaded result to the
service's `image_shape`. The observed implementation currently builds an
RGBA buffer and sends the same in-memory PNG buffer for both the `image` and
`mask` parameters. Treat this as an important source limitation: successful
provider completion does not establish that the intended source image was
sent.

## `text_extend_image`

The extend tool makes a transparent 1024-based canvas, copies an edge slice of
the input into the generation mask, and calls DALL-E 2 image edit at
`1024x1024`. `ext_side` must be exactly one of `Right`, `Bottom`, `Left`, or
`Top`. It then pastes the returned image into a larger composite. The
service does not pass `output_size` for this pipeline.

## `text_outpaint_image`

The outpaint tool copies the input and uses alpha-zero pixels as the
transparent region, then calls DALL-E 2 image edit at `1024x1024`. It expects
to index an alpha channel before the provider call, so an RGB-only input is
not safe for the observed implementation. The service does not pass
`output_size` for this pipeline.

## Credentials and network policy

The generation tool reads an OpenAI key from local configuration. The edit,
extend, and outpaint tools also initialize the OpenAI SDK from the process
credential environment. They then use `requests` to download the provider's
returned image URL. The checked configuration has an empty key. Never copy a
key into a skill, request fixture, shell history, report, or error message;
never log authorization headers; and never substitute a real endpoint in a
smoke test.

A safe verification can list the inspector's bundled static route contract or
validate a local request fixture. The inspector's optional network operation is
restricted to `GET /status` on an explicit loopback host and port. It never
issues either model POST route and must not call provider SDK methods or remote
URLs. No model weights or successful provider response are assumed by this
skill.

## Failure classification

- Missing key or SDK credential error: configuration/permission failure.
- DNS, connection, timeout, or returned-URL download error: network failure.
- Provider HTTP/API error, invalid prompt, quota, or model rejection: remote
  API failure; preserve sanitized status information only.
- A response with no usable `data[0].url`: provider response-shape failure.
- A decoded result that cannot match its advertised shape: local protocol
  failure after the provider response.

The service currently catches some tool exceptions only while constructing or
loading and returns a generic `Error!`; image-call failures are printed by
the tools and may leave no usable `self.image`. Do not treat a generic
`Loaded.` response as proof that any of these boundaries succeeded.
