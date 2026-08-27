# Chest-X-ray troubleshooting

Use the smallest corrective action first. Preserve the original error and
changed setting in run metadata. Do not add a downloader, credential, or
fallback model to a production runtime as an ad hoc fix.

| Symptom | Likely cause | Bounded response |
|---|---|---|
| `FileNotFoundError` or validator rejects a path | Missing/non-regular file, unsupported suffix, or wrong working directory | Pass a readable JPG/PNG path; use the validator; route DICOM through image-data utilities |
| Image loads but model fails on shape/channels | Unsupported image encoding, alpha/multichannel assumptions, or corrupt file | Re-export as a valid 8-bit JPG/PNG; verify with the display/data utility; do not claim the original was analyzed |
| `Invalid organs specified` | Segmentation name is not one of the exact 14 labels | Use exact names from the API reference, including `Left/Right`, `Hilus Pulmonis`, `Facies Diaphragmatica`, `Weasand`, and `Spine` |
| Segmentation works but `area_cm2` looks implausible | JPG/PNG has no trusted physical pixel spacing; source applies fixed 0.2 mm/pixel | Report pixels/masks as image-derived; explicitly mark cm² approximate and route DICOM measurement work elsewhere |
| Segmentation returns no metric for a requested organ | Thresholded mask is empty or region props found no component | Preserve `processed_organs`; treat as empty mask/uncertain output, not proof of absence; inspect overlay |
| CUDA unavailable, invalid device, or out-of-memory | No GPU, insufficient VRAM, or another model remains resident | Run validator on CPU; select one smaller tool; release other models; use grounding 8-bit only if bitsandbytes is compatible; never imply quality equivalence |
| CPU path is very slow | DenseNet/PSPNet or transformer model is running without acceleration | Bound the run or stop; CPU smoke execution is not a clinical performance test |
| CheXagent fails with bfloat16 | Backend lacks bfloat16 kernels/support, or model/device mapping is incompatible | Check accelerator and installed stack; choose a supported dtype only after explicit verification; do not silently cast and claim equivalence |
| CheXagent constructor leaves a confusing Transformers error | Remote-code model expects the source's temporary 4.40.0 compatibility behavior | Isolate the constructor in a clean process, check the installed pinned stack, and record the failure; do not globally mutate a shared process |
| MAIRA-2 fails with `BitsAndBytesConfig` or quantized load | bitsandbytes, CUDA, Accelerate, or Transformers incompatibility; both flags set | Set neither flag for a full-precision test, or set exactly one flag after backend verification; preserve the selected mode |
| MAIRA-2 returns `completed_no_finding` | Decoder produced no grounded predictions or all predictions lacked boxes | Keep an empty prediction result and no overlay; do not manufacture a box or call it a failed load |
| Grounding overlay is misplaced | Model-space box used as original-image box, or coordinate order changed | Use `image_coordinates`; preserve `[x_min, y_min, x_max, y_max]`; compare against original width/height |
| Grounding visualization cannot be saved | Temporary directory missing or not writable | Supply an existing writable caller-managed temp directory; if no artifact is possible, retain boxes and metadata only |
| Report returns an error string | One of two model/tokenizer/processor sets is absent, image processing failed, or generation compatibility broke | Confirm both model artifacts and RGB image; check Transformers generation compatibility; do not present the error string as a report |
| Report generation rejects `beam_width` or config fields | Installed Transformers generation API differs from the source expectation | Record a compatibility block and align the environment under deployment policy; do not silently alter decoding settings |
| VQA/LLaVA answer is empty, generic, or hallucinatory | Prompt ambiguity, model limitations, or image preprocessing failure | Retain exact prompt and status; ask a focused question or corroborate with classification/grounding; never add confidence |
| LLaVA fails on CPU despite `device="cpu"` | `_process_input` uses `.cuda()` and half-precision tensors directly | Treat CPU as unsupported for this implementation; use CheXagent only after its own backend check or choose CPU utilities |
| LLaVA fails while loading quantization | bitsandbytes or model-builder version mismatch | Try one unquantized/quantized mode in an isolated environment, only when resources allow; otherwise route around optional LLaVA |
| RoentGen cannot find weights | Manual RoentGen artifacts are absent or `model_path` is wrong | Stop generation; have an operator provision and verify the model directory; do not download from a bundled script |
| RoentGen runs out of memory or is too slow | Float32 Diffusers pipeline and requested image/steps are expensive | Use a bounded test size/steps only in an approved experiment; keep output labeled synthetic; do not use as patient evidence |
| Generated PNG path is missing after success | Temporary directory cleanup, permission issue, or failed save | Verify the path immediately and use a persistent writable temp directory; preserve failed metadata if absent |
| Constructors import-fail before any run | Missing scikit-image, TorchXRayVision, Transformers, Diffusers, Pillow, or other declared dependency | Report the missing dependency and environment; do not patch the runtime or claim model support from static API knowledge |

## Specific diagnostic order

### CUDA versus CPU

First run the input validator, then check the requested device in the host
runtime. If no CUDA device is available, prefer no-model validation or a single
CPU classifier/segmentation attempt. For transformer tools, distinguish “the
constructor accepted `cpu`” from “all input and generation operations support
CPU.” LLaVA-Med is explicitly unverified on CPU because its input preparation
calls CUDA helpers.

### Cache or model availability

A missing cache is not a reason for a bundled script to fetch weights. Record
which named model artifact is absent, whether network/model-hub access is
permitted by the operator, and stop if it is not. Report generation requires
both section models. RoentGen requires manual weights and is optional.

### Non-DICOM segmentation

If segmentation accepts a PNG/JPG, it can still return a mask and overlay.
However, its `area_cm2` is computed from a fixed spacing assumption rather than
study metadata. Explain this before reporting any area. A failed DICOM
conversion is a data-preparation failure, not evidence that the model found no
organ.

## External-resource boundary

This skill's bundled validator performs only local filesystem and argument
checks. It does not access networks, model hubs, credentials, caches, DICOM
parsers, GPUs, or model inference. All weight provisioning, dependency pinning,
and approval for external model access remain operator responsibilities.
