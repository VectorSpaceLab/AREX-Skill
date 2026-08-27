# MedRAX troubleshooting

Use this page for cross-cutting failures, then open the nearest sub-skill
reference for tool-specific recovery. Do not turn an error into a clinical
claim or silently retry an expensive model download.

## Install and import

- **`medrax.tools` fails during import with a Transformers/Diffusers symbol
  error:** the pinned Transformers revision and the newest Diffusers/Torch
  stack are incompatible. Recreate an isolated environment from the package
  metadata, use a compatible Diffusers/Transformers pair, and run the safe
  import checker before constructing tools. Do not patch the source at runtime.
- **`torchvision` or Torch import fails:** check that Torch and TorchVision are
  a matched pair and that the wheel's CUDA runtime is compatible with the
  driver. A CPU-only wheel may import but cannot validate CUDA tools.
- **Optional dependency import errors:** select a utility-only profile first;
  install only the dependency required by the chosen tool, then rerun its
  schema/import check. Do not initialize all tools to discover which package is
  missing.
- **Gradio construction fails after package installation:** inspect the
  installed Gradio API and use the interface compatibility notes. Test demo
  construction without `launch()` and avoid changing unrelated ML packages.

## Model, device, and provider

- **CUDA unavailable or `no kernel image` appears:** query Torch's CUDA build,
  driver, device capability, and visible device count. Use a compatible CUDA
  wheel or a supported device; do not label CPU output as CUDA verification.
- **Out-of-memory during construction:** stop, clear stale processes, select
  fewer tools, use a smaller/quantized supported model, or move to a larger
  device. Quantization flags do not guarantee that every model supports the
  selected dtype.
- **Hugging Face download/authentication/network failure:** confirm the model
  identifier, cache directory permissions, network policy, and any required
  access authorization. The caller must explicitly authorize network/model
  downloads; cached weights are not part of this skill.
- **OpenAI-compatible chat call fails:** check that `OPENAI_API_KEY` is present
  in the process environment and that `OPENAI_BASE_URL` ends at the provider's
  compatible API root. Never print or commit a key. For a local endpoint,
  verify reachability and model name separately; a valid key does not prove a
  model is served.

## Input and configuration

- **File not found or unsupported suffix:** run the nearest bundled validator;
  pass an existing JPG/PNG to model tools and an existing DICOM file to
  `DicomProcessorTool`. Do not pass a display-only path that was deleted.
- **DICOM conversion fails:** inspect transfer syntax handlers, pixel data,
  window center/width, rescale slope/intercept, and dynamic range. Preserve the
  original DICOM; use the PNG only as a display/model derivative. Treat
  patient/study metadata as sensitive.
- **Invalid segmentation organ:** use the exact friendly names documented by
  `chest-xray-analysis`; reject the request instead of silently substituting a
  nearby organ.
- **Empty grounding result:** distinguish `completed_no_finding` from a model
  or input failure. Preserve the model-coordinate and original-image boxes
  separately when boxes exist.
- **Temporary output missing:** choose a writable caller-owned `temp_dir`,
  create it before construction, and preserve returned paths until the caller
  has consumed them. Avoid using the skill directory for runtime artifacts.

## UI, logs, and privacy

- **DICOM displays but analysis sees the wrong file:** the interface maintains
  an original path and a display path. Keep the DICOM original for tool input
  where appropriate and use the converted image only for display.
- **Chat continues the wrong conversation:** use a stable `thread_id` for one
  conversation and a new identifier for isolation. `MemorySaver` is process
  local, not durable storage.
- **Tool calls are missing from logs:** confirm `log_tools=True`, a writable
  `log_dir`, and that the graph reached its execute node. Logs can contain
  sensitive image paths and arguments; restrict access.
- **UI is exposed unexpectedly:** do not use `share=True` or bind publicly
  without a reviewed deployment boundary. A safe configuration checker can
  reject public bind/share combinations before launch.
- **Unexpected tool result or traceback:** record the selected tool, validated
  inputs, device, model availability, and `analysis_status`; route the error
  to the tool-specific reference instead of broadening the tool set.

## Benchmark-specific boundary

The benchmark runner needs data files, image sources, an OpenAI-compatible API,
network access in URL mode, and spend/credential authorization. Use its offline
manifest validator first. A missing image is a preflight/data error, a skipped
no-image case is not a correct answer, and a successful API response is not
clinical validation.
