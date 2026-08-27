# Raw image JSON protocol

The service transports pixels in JSON as base64 text plus an explicit shape.
It does not transport PNG or JPEG for the `image` and `mask` fields.

## Required representation

For each raw field `name`:

- `name` is a standard base64 string containing the bytes of a flattened
  `numpy.uint8` array.
- `name_shape` is a JSON array of positive integers, normally
  `[height, width, channels]`.
- The decoded byte count must equal
  `product(name_shape) * 1` because `uint8` has one byte per element.
- Reshape in row-major order. Do not silently infer dimensions or channel
  count from the base64 text.

The request fields are `image`/`image_shape` and, for text edit,
`mask`/`mask_shape`. The output fields are `image`/`image_shape`; the output
also echoes `text`. The service's `get_numpy_img` uses `base64.b64decode`,
`np.frombuffer(..., dtype=np.uint8)`, and `np.reshape`, so malformed base64,
negative/non-integral dimensions, or a byte-count mismatch should be rejected
before sending a request.

An optional `dtype` key is not part of the observed wire contract. Treat the
wire dtype as fixed `uint8`; if a local fixture includes `dtype`, accept only
`uint8` and flag other values rather than guessing.

## Minimal local fixtures

These are validation-only examples:

| Field | Base64 | Shape | Bytes |
|---|---|---:|---:|
| RGB pixel | `AAEC` | `[1, 1, 3]` | `00 01 02` |
| RGBA pixel | `AAAA/w==` | `[1, 1, 4]` | `00 00 00 ff` |

A fixture can be checked without a server:

```text
python scripts/validate_image_payload.py --input payload.json --decode
```

Use `--field mask` when validating a mask object, or `--all` to validate
both `image` and `mask` fields if present. The validator only reads the local
JSON and never writes decoded pixels or contacts a network.

## GIMP 2 versus other output

The legacy bridge sends raw pixel-region bytes and declares `source: "gimp2"`.
The service then uses the pipeline object's GIMP 2 output conversion and the
plug-in writes the decoded bytes into a new layer whose width and height come
from `image_shape`. A non-GIMP-2 source selects the flattened output method.
Do not change `source` merely to work around a shape error; fix the shape and
byte contract instead.

The GIMP 2 plug-ins read the same configured localhost port, call model load,
then call inference, and decode the response. Text-to-image adds a new layer;
edit adds a new layer; extend opens a new image sized from the output; outpaint
adds a new layer. These bridge effects are source behavior, not verified in
this environment.

## Shape and channel guardrails

- Keep height, width, and channel order consistent with the originating pixel
  region. The service does not normalize channel order.
- Masks must have a shape that the selected pipeline can index. The edit tool
  examines black RGBA pixels when deriving transparency, so a 4-channel mask
  is the least surprising input for that implementation.
- Outpaint indexes channel 3 to find transparent pixels; use an RGBA image
  (`channels == 4`) or expect an index error.
- Avoid enormous dimensions. The service allocates an array from the decoded
  payload before the provider call; validate resource bounds in a client.
- A base64 value that decodes to a valid image file is still invalid unless
  its file bytes happen to be the exact raw array bytes described by the
  paired shape.
