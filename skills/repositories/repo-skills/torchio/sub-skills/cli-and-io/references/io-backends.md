# TorchIO I/O Backends

TorchIO image constructors and the CLI share the same core image-loading behavior. The CLI wraps files as `tio.ScalarImage(PATH)`, while Python users can also provide tensors, arrays, file-like objects, nibabel images, SimpleITK images, fsspec open files, and optional Zarr stores.

## Source Types and Behavior

| Source form | Behavior | Practical guidance |
|---|---|---|
| Local `str` or `Path` | Stored as a path and lazily backed when possible. | Best for normal NIfTI workflows and CLI commands. |
| `file://` or fsspec local URI | Materialized through fsspec when passed as a string URI. | Useful when a pipeline already emits URI strings. |
| Remote non-Zarr URI, such as `https://.../image.nii.gz` or `s3://.../image.nii.gz` | Fetched with fsspec into a temporary local file before reading. | Expect full download and credentials/network requirements. |
| Remote `.nii.zarr` URI, such as `az://.../brain.nii.zarr` | Stored as a remote Zarr URI and opened lazily by the Zarr backend. | Preferred for large remote volumes because metadata and slices can stream without full download. |
| File-like object or bytes | Materialized to a temporary file; suffix hint may be required. | In Python, pass `suffix='.nii.gz'` for file-like inputs without a filename. |
| Tensor or NumPy array | Eager in-memory image. | Construct as `tio.ScalarImage(tensor)` or `tio.LabelMap(tensor)`, not `source=tensor`. |
| NIfTI-Zarr path ending `.nii.zarr` | Uses the Zarr backend and `niizarr`. | Requires the `zarr` extra. |

## Lazy Backend Selection

Built-in lazy backends include:

- `NibabelBackend` for local NIfTI paths and nibabel images.
- `ZarrBackend` for local or remote `.nii.zarr` sources.
- `TensorBackend` for tensor-backed images.

For local NIfTI and NIfTI-Zarr paths, metadata such as shape and affine can be inspected without immediately materializing the full image tensor. Slicing through `image.dataobj` can also avoid full materialization for supported lazy backends.

## Format Dispatch

TorchIO detects these major cases:

- `.nii` and `.nii.gz`: read through NiBabel for NIfTI-specific behavior.
- `.nii.zarr`: read through `niizarr`/Zarr when the optional dependency is installed.
- Other image extensions: read through SimpleITK when supported by SimpleITK.

Saving follows the output suffix. `image.save('output.nii.zarr')` writes a NIfTI-Zarr store through `niizarr`; other paths are written through SimpleITK. The `torchio convert` CLI command mirrors this behavior and special-cases `.nii.zarr` output.

## NIfTI-Zarr Workflows

Install the relevant optional dependencies before `.nii.zarr` conversion or loading:

```bash
pip install 'torchio[zarr]'
```

Convert locally from the CLI:

```bash
torchio convert input.nii.gz output.nii.zarr
```

Convert from Python:

```python
import torchio as tio

image = tio.ScalarImage('input.nii.gz')
image.save('output.nii.zarr')
loaded = tio.ScalarImage('output.nii.zarr')
print(loaded.shape)
```

The output is a directory-like `.nii.zarr` store containing chunked image data and NIfTI metadata. If chunk-size customization is required, use `niizarr` directly in user code; the TorchIO convenience path uses its default conversion settings.

## Remote and Cloud Loading

Remote `.nii.zarr` URIs are detected for protocols such as `az://`, `abfs://`, `s3://`, `gs://`, and `https://` when the clean URI ends with `.nii.zarr`. Query strings and fragments are ignored for detection. These sources are not fetched eagerly; the Zarr backend receives the URI and any `reader_kwargs`.

Install provider extras as needed:

```bash
pip install 'torchio[zarr,s3]'
pip install 'torchio[zarr,azure]'
pip install 'torchio[zarr,gcs]'
```

Credential handling is delegated to the provider fsspec backend:

- S3: `s3fs` reads normal AWS config or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.
- Azure: `adlfs` can use account/key, SAS token, connection string, or default credentials.
- GCS: `gcsfs` can use Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS`.
- HTTPS: fsspec HTTP support is part of the base dependency set, but private endpoints may still need headers or signed URLs.

In Python, cloud-store options can be passed through `reader_kwargs`:

```python
import torchio as tio

image = tio.ScalarImage(
    'az://container/dataset/brain.nii.zarr',
    reader_kwargs={'account_name': 'myaccount'},
)
print(image.shape)
```

Avoid embedding secrets in scripts or generated commands. Prefer environment variables, credential files, managed identities, or user-provided runtime configuration.

## CLI and Remote Inputs

The CLI accepts paths/URIs wherever `tio.ScalarImage(PATH)` would accept them, but use caution:

- `torchio info https://.../image.nii.gz` may download the whole file to a temporary path.
- `torchio info s3://.../image.nii.zarr` can stream metadata if the `zarr` and provider extras are installed and credentials work.
- `torchio convert remote.nii.zarr local.nii.gz` may materialize data when saving to a dense local format.
- Prefer small metadata checks (`info`) before transform or conversion commands on remote inputs.

## Optional Extras Summary

| Workflow | Extra packages | Failure symptom |
|---|---|---|
| Plot PNG/PDF outputs | `torchio[plot]` | ImportError mentioning matplotlib or plot extra. |
| GIF export | `torchio[plot]` for Pillow-backed image writing | Missing Pillow or image writer errors. |
| MP4 export | `torchio[video]` plus system `ffmpeg` | ImportError for `ffmpeg` Python package or runtime failure finding `ffmpeg`. |
| NIfTI-Zarr local read/write | `torchio[zarr]` | ImportError mentioning `nifti-zarr` or `zarr`. |
| S3 NIfTI-Zarr | `torchio[zarr,s3]` | Missing `s3fs`, auth errors, or bucket access failures. |
| Azure NIfTI-Zarr | `torchio[zarr,azure]` | Missing `adlfs`, auth errors, or account/container access failures. |
| GCS NIfTI-Zarr | `torchio[zarr,gcs]` | Missing `gcsfs`, auth errors, or application credential failures. |
