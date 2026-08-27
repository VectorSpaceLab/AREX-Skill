# Checkpoints and environment

## CUDA is a hard runtime requirement

The selected training and evaluation workflows are CUDA-bound. The source
creates `cuda:<gpu_device>` state, allocates CUDA tensors while shared modules
are imported, and moves models and batches to CUDA. The standalone MobileSAMv2
route has the same limitation, although its initial model-placement fallback
can misleadingly appear to support CPU before a later box tensor calls
`.cuda()`.

Run these checks in the user's own environment and with an explicit device
selection before opening a real dataset:

```bash
python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); torch.zeros(1, device='cuda')"
python -m pip check
```

A CPU-only parser check, shape validator, or import is useful diagnostic
information only. It cannot clear the runtime gate, and `-gpu False` does not
make the core loop CPU-safe. Do not claim a training/evaluation workflow is
verified when only CPU checks passed.

The repository's historical environment specification is a Python 3.10-era
baseline with PyTorch/torchvision, MONAI, imaging, and logging packages. It also
contains a contradictory `cpuonly` pin alongside a pip CUDA torch pin. Do not
install it blindly as one complete definition; prepare a compatible CUDA binary
PyTorch/torchvision pair and verify the selected packages with `pip check`.

## Adapter dependency matrix

| Adapter family | Additional dependency to preflight | What the metadata helper cannot prove |
|---|---|---|
| ISIC, REFUGE, WBC, STARE, Pendal | PyTorch/torchvision, Pillow, and the tabular/image packages actually used by the adapter | CSV decoding, image mode, mask values, and prompt generation |
| DDTI | OpenCV for connected components, plus its image/tabular dependencies | Component area and the availability of one or two valid foreground prompts |
| LIDC | NumPy, PyTorch, and pickle reading | The broken `MyLIDC` registry call and pickle schema/content |
| Brat, KITS, Atlas, SegRap | `nibabel` | NIfTI affine, orientation, spacing, and label values |
| LNQ | `SimpleITK` for NRRD | NRRD spacing/orientation and the marker/volume pairing |
| ToothFairy | NumPy | `.npy` dtype and whether sparse labels are spatially aligned |
| Decathlon/BTCV | MONAI plus compatible PyTorch and medical-image readers | `dataset_0.json` path resolution, MONAI transforms, cache memory, and post-spacing dimensions |

The source imports broad shared utilities, so a selected adapter can still be
blocked by a broken core PyTorch/torchvision/MONAI binary even if its own file
format is simple.

## Checkpoint roles and safe path preflight

Keep the following artifacts separate:

1. **Base model (`-sam_ckpt`).** A checkpoint-consuming `sam` or `mobile_sam`
   builder uses this for the selected encoder. Choose the exact variant for the
   requested encoder. An existing filename is not proof of compatibility. The
   runtime route must not rely on legacy model-builder download behavior.
2. **EfficientSAM weights.** The source constructs the selected EfficientSAM
   registry entry differently from original SAM. Confirm the installed builder's
   weight behavior; do not assume an original SAM checkpoint is interchangeable.
3. **Adapter/resume (`-weights`).** The source's training/evaluation wrapper
   expects a readable saved record with at least `epoch`, `best_tol`, and
   `state_dict`; training records also carry `optimizer` and `path_helper`.
   Load it only with the matching network, encoder, output count, and device.
   `-weights` is not a raw base SAM file.
4. **`-pretrain`.** The parser declares this as `bool`, but later code treats a
   truthy value as a path for `torch.load`. Do not pass a path through this flag
   without inspecting the parsed behavior or fixing the interface.

A path-only preflight should check `is_file` and readability, for example
`test -r "$SAM_CKPT"`, without deserializing an untrusted checkpoint. After the
path passes, a separate model-compatible load check may inspect keys in an
isolated user environment. Never download a missing artifact from a runtime
skill.

## Data and memory gates

Before a real run, confirm:

- `-dataset` is one of the exact registered names and `-data_path` is the root
  expected by that adapter;
- `-image_size` and `-out_size` are positive and match the declared sample
  contract;
- 3D uses `-thd True`, a positive `-chunk`, and for evaluation a positive
  `-evl_chunk`; the latter should divide the post-transform depth when possible
  because the source loop can omit a remainder;
- MONAI `-roi_size` fits the post-crop in-plane dimensions;
- a representative small case fits the selected GPU before increasing batch,
  crop depth, or random-crop count.

For a 2D out-of-memory error, lower `-b`, then `-image_size`. For MONAI 3D,
lower `-b`, `-chunk`, `-num_sample`, and evaluation `-evl_chunk`. Preserve the
3D flag and label rank; moving to CPU is not a valid memory workaround for this
source.
