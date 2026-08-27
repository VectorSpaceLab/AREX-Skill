# Cross-cutting troubleshooting

## Install/import failures

**`Could not find required package: opencv4` or `libturbojpeg`:** install the
development headers/libraries, ensure `pkg-config` resolves the names, and
retry the package build in the same environment. Do not paper over the error by
installing only the Python `cv2` module; the C++ extension still needs linkable
libraries.

**`import ffcv._libffcv` fails with a shared-library or symbol error:** inspect
the extension's dynamic dependencies and check that OpenCV, TurboJPEG, pthreads,
and the C++ runtime come from one compatible environment. Rebuild after fixing
library search paths. A successful editable-wheel build is not enough.

**`pip check` or import sees the wrong package:** run metadata and import checks
from the target environment and outside the source checkout. Keep the source
commit, distribution version, and module version in the report; this snapshot
has a 1.0.1/1.0.2 split.

## Data/schema failures

**Wrong values in fields:** confirm that each sample is a tuple/list whose
positions match the insertion order of `fields`. Mapping samples must be
adapted explicitly; the writer does not look up values by field name.

**RGB `TypeError`/`ValueError`:** normalize images to CPU HWC RGB `uint8` arrays.
Reject grayscale, RGBA, CHW, floating-point, and malformed arrays before worker
processes start. Use `max_resolution` only as a storage resize policy.

**Large sample raises `MemoryError`:** page size is a power of two from 2 MiB
up to but not including 4 GiB, and a single allocation must fit in a page.
Reduce encoded sample size or increase `page_size`; start with one worker while
debugging.

**JSON is not valid after loading:** `JSONField` uses UTF-8 plus a NUL
terminator and `BytesDecoder` returns a batch padded to its largest element.
Use `JSONField.unpack`; do not send padded bytes directly to `json.loads`.

**Custom field cannot be read:** type-255 custom fields require a field-name to
class mapping in `custom_fields`/`custom_handlers`. Register the class, not an
instance, and make the class/decoder importable in reader processes.

## Pipeline/API failures

**Variable image sizes fail with `SimpleRGBImageDecoder`:** choose
`RandomResizedCropRGBImageDecoder` or `CenterCropRGBImageDecoder`, or make the
stored images constant resolution.

**NumPy/Numba operation fails after `ToTensor`:** reorder the pipeline. Decoder
first, native NumPy operations next, `ToTensor`, device transfer, image layout,
then torch modules/GPU operations.

**Shape/device/dtype mismatch:** write down the state after every operation.
A shape-changing operation must declare a matching allocation; a CUDA buffer
cannot be requested while the state is JIT/NumPy CPU. Test a one-row tail when
`drop_last=False` so stale full-batch rows are not mistaken for data.

**CPU torch module is unexpectedly slow:** FFCV warns because a torch module on
CPU loses the native JIT path. Use an FFCV native transform or move the module
and its inputs to the intended GPU when that is safe.

## Cache/device/resource failures

**RAM exhaustion with random order:** if the dataset is larger than RAM, try
`os_cache=False` plus `OrderOption.QUASI_RANDOM` in non-distributed mode, or use
sequential/random order for distributed jobs. Record the changed sampling
semantics.

**`QUASI_RANDOM` raises in distributed mode:** this is an unsupported API
boundary, not a transient error. Use `SEQUENTIAL` or `RANDOM` with a shared
seed.

**CUDA OOM or stream failure during a CPU task:** shared hosts can have a full
default device, and this checkout initializes CUDA streams whenever CUDA is
visible. Reserve a GPU for CUDA work or hide CUDA for a CPU-only process. Do not
turn a CPU pass into a GPU capability claim.

**Benchmark process grows or runs too long:** use `python -m ffcv.benchmarks
--help`, select one suite with `--pattern`, set low `--runs`/`--warm-up`, and
stop on unsafe allocation. The default wildcard expands a Cartesian product;
benchmark-scale execution is not a smoke test.
