# Fields, formats, and custom registration

## Mapping order and descriptors

`DatasetWriter` receives a mapping from logical names to `Field` instances. It
constructs sample metadata from `fields.values()` in insertion order and
encodes each sample by zipping that order with the sample iterable:

```python
import numpy as np
from ffcv.fields import FloatField, NDArrayField

fields = {
    "features": NDArrayField(np.dtype("float32"), (6,)),
    "target": FloatField(),
}
# Every source row is (features, target), in precisely that order.
```

The descriptor stores names in a fixed 16-byte ASCII slot. This source version
truncates a longer encoded name when writing; use unique names of at most 16
ASCII bytes rather than relying on truncation. `Reader.field_names` exposes the
logical names. The structured `Reader.metadata` dtype uses anonymous field
names (`f0`, `f1`, ...), which are for low-level metadata inspection only.

The writer chooses a built-in type id by exact class. A subclass of a built-in
is therefore type id 255 and needs custom registration even if it reuses the
built-in metadata layout. The format's `ARG_TYPE` is a fixed 1024-byte payload
for field arguments.

## Fixed scalar fields

### `IntField`

- Input: one integer-like scalar per sample.
- Metadata: signed little-endian `int64`; default decoder: `IntDecoder`.
- Check: do not pass a string, array, or multi-value object; check the intended
  integer range before worker conversion.

### `FloatField`

- Input: one float-like scalar per sample.
- Metadata: little-endian `float64`; default decoder: `FloatDecoder`.
- Check: return exactly one scalar and make any precision conversion explicit.

## Fixed arrays and tensors

### `NDArrayField(dtype, shape)`

- Input: a NumPy array with the declared shape and compatible dtype.
- Storage: a pointer to a fixed allocation of
  `dtype.itemsize * product(shape)` bytes.
- Decoder: `NDArrayDecoder`, returning the declared shape and dtype.
- Check: inspect first, typical, and last/odd samples for exact shape, dtype,
  contiguity/byte size, and no ragged rows. A mismatch commonly appears as a
  copy/broadcast failure in `encode`.

The implementation writes `field.reshape(-1).view('<u1')`; this is not a ragged
array field. Use fixed padding or `BytesField` plus a length protocol for
variable-length rows.

### `TorchTensorField(torch_dtype, shape)`

- Input: a CPU torch tensor of the declared shape and dtype on which
  `.numpy()` succeeds.
- Storage/decoder: the same pointer-backed fixed-size representation as an
  `NDArrayField`, after conversion to the corresponding NumPy dtype.
- Check: move CUDA tensors to CPU, detach tensors that require grad, and
  normalize unsupported layouts before returning a sample. Verify shape and
  dtype on representative rows.

The writer is not a general tensor transfer mechanism. If an image tensor is
being stored as an image, convert it to HWC RGB `uint8` and use
`RGBImageField` instead.

## `RGBImageField`

The writer accepts a NumPy array or a PIL `Image`; a torch tensor is not
accepted by the implementation even though older prose may suggest otherwise.
Normalize to a CPU HWC `uint8` array before the source reaches the writer.

- Required representation: `(height, width, 3)`, RGB, `uint8`.
- `write_mode='raw'`: contiguous raw pixel bytes.
- `write_mode='jpg'`: JPEG compression with `jpeg_quality`.
- `write_mode='smart'`: computes a JPEG candidate and chooses JPEG only when
  `smart_threshold` is set and `image.nbytes > smart_threshold`; otherwise raw.
- `write_mode='proportion'`: chooses JPEG randomly with
  `compress_probability`, otherwise raw.
- `max_resolution`: resizes only when the longest side exceeds the requested
  maximum; it preserves HWC RGB form.
- Metadata: mode, width, height, and data pointer. The simple decoder requires
  constant resolution; crop/resize decoders handle variable resolutions later.

Reject grayscale `(H, W)`, RGBA `(H, W, 4)`, non-`uint8`, CHW, and malformed
arrays in a preflight adapter rather than waiting for a worker traceback.

## Variable bytes and JSON

### `BytesField`

- Input: a one-dimensional NumPy `uint8` array. For Python bytes use
  `np.frombuffer(payload, dtype=np.uint8)` explicitly.
- Metadata: pointer and byte count plus a variable-size allocation.
- Decoder: `BytesDecoder`.
- Read behavior: the decoder allocates a batch to the maximum `size` among its
  samples. The output shape alone does not reveal each original length. Keep a
  parallel `IntField` length, or define a safe sentinel/protocol and test empty,
  short, long, and batch-boundary payloads.

Passing Python `bytes` directly violates this implementation's writer contract:
`BytesField.encode` uses `.size` and assigns the array into the allocation.

### `JSONField`

- Input: a JSON-compatible Python object.
- Encoding: `json.dumps`, UTF-8, a NUL terminator, then the `BytesField`
  pointer/size representation.
- Decoder: the byte decoder; JSON conversion is not automatic.
- Unpacking: `JSONField.unpack` accepts a NumPy array or torch tensor, handles a
  single sample or batch, trims at the first NUL, decodes UTF-8, and calls
  `json.loads`.

The terminator is essential because a variable-byte batch is zero-padded to its
largest item. Never call `json.loads` on that padded array without first
trimming at NUL. Test empty/short/long documents and non-ASCII strings. In this
source version, `JSONField.from_binary` is inherited from `BytesField`, so a
reader handler reconstructed from the JSON type descriptor can be a
`BytesField`; use `JSONField.unpack` regardless.

## Custom `Field` contract

A custom field must provide a coherent implementation of the abstract `Field`
interface:

1. `metadata_type`: the NumPy dtype for each sample's metadata record.
2. `encode(destination, field, malloc)`: write metadata and call `malloc(size)`
   for every data-region allocation.
3. `get_decoder_class()`: return the `Operation` class used by the default
   decoding path.
4. `to_binary()`: return the fixed `ARG_TYPE` argument payload.
5. `from_binary(binary)`: reconstruct the field state from that payload.

The `binary` payload is fixed at 1024 bytes, so do not depend on process-local
objects or parameters that cannot fit in it. If a custom decoder or metadata
layout depends on custom parameters, override both serialization directions and
assert the decoded descriptor. An inherited `NDArrayField.from_binary` can be
sufficient only for a custom field whose reader behavior is intentionally the
base ND-array behavior; it returns an `NDArrayField`, not necessarily the custom
class.

This fixed-width ASCII example stores a padded `uint8` array and reconstructs
the custom class from the inherited shape descriptor:

```python
import numpy as np
from ffcv.fields.ndarray import NDArrayDecoder, NDArrayField

class StringDecoder(NDArrayDecoder):
    pass

class AsciiField(NDArrayField):
    def __init__(self, max_len):
        self.max_len = int(max_len)
        if self.max_len <= 0:
            raise ValueError("max_len must be positive")
        super().__init__(np.dtype("uint8"), (self.max_len,))

    @staticmethod
    def from_binary(binary):
        base = NDArrayField.from_binary(binary)
        if base.dtype != np.dtype("uint8") or base.shape[0] <= 0:
            raise ValueError("invalid AsciiField descriptor")
        return AsciiField(base.shape[0])

    def encode(self, destination, field, malloc):
        if not isinstance(field, str):
            raise TypeError("AsciiField expects str")
        raw = field.encode("ascii")
        if len(raw) > self.max_len:
            raise ValueError("string exceeds max_len")
        padded = np.zeros(self.max_len, dtype=np.uint8)
        padded[:len(raw)] = np.frombuffer(raw, dtype=np.uint8)
        return super().encode(destination, padded, malloc)
```

Write and read it with the **class**, not an instance, in the registration:

```python
from ffcv import Loader
from ffcv.writer import DatasetWriter

writer = DatasetWriter("captions.beton", {"caption": AsciiField(128)},
                       num_workers=1)
writer.from_indexed_dataset(caption_dataset)

loader = Loader(
    "captions.beton",
    batch_size=16,
    pipelines={"caption": [StringDecoder()]},
    custom_fields={"caption": AsciiField},
)
```

Omitting registration for a type-255 field causes `Reader`/`Loader` to raise a
`ValueError` instead of guessing. The custom class and decoder must be
importable in reader processes. The repository test's simpler `StringField`
subclass inherits the base binary descriptor and supplies an explicit
`StringDecoder`; use the stronger round-trip pattern above when custom state
must survive reading.
