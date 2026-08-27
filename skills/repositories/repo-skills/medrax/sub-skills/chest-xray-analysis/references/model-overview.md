# Model and runtime overview

This reference separates what the source code constructs from what a Researcher
must provision. Model initialization is intentionally not performed by the
bundled validator or by this skill itself.

## Tool-to-model map

| Tool | Model/backend in the implementation | Weight behavior | Practical device note |
|---|---|---|---|
| `ChestXRayClassifierTool` | TorchXRayVision DenseNet, default `densenet121-res224-all` | TorchXRayVision weights are loaded by the constructor | `cuda` is the normal path; `cpu` is accepted but may be slow and memory-bound |
| `ChestXRaySegmentationTool` | TorchXRayVision ChestX-Det PSPNet | Baseline model is loaded by the constructor | `cuda` is preferred; CPU is a bounded fallback for small validation runs |
| `ChestXRayReportGeneratorTool` | Two Hugging Face `VisionEncoderDecoderModel` pipelines, findings and impression | Both model/tokenizer/processor sets must be available | Two models are moved to the requested device; expect high memory use |
| `XRayVQATool` | `StanfordAIMI/CheXagent-2-3b` via Transformers remote code | Tokenizer/model are loaded automatically | Defaults to CUDA and bfloat16; check accelerator bfloat16 support |
| `XRayPhraseGroundingTool` | `microsoft/maira-2` via Transformers remote code | Model and processor are loaded automatically | CUDA is the practical default; 4/8-bit paths require bitsandbytes compatibility |
| `LlavaMedTool` | `microsoft/llava-med-v1.5-mistral-7b` through the bundled LLaVA builder | Model assets are loaded by the builder | Large and optional; source input preparation uses CUDA helpers directly |
| `ChestXRayGeneratorTool` | Diffusers Stable Diffusion pipeline using RoentGen | Weights must already be manually supplied | Float32 pipeline; CUDA is strongly preferred for usable latency |

The repository README describes these as integrated tools and recommends
selective initialization. Follow that recommendation: constructing every model
can exhaust host or GPU memory before any input is processed.

## Device and dtype prerequisites

1. Check `torch.cuda.is_available()` and available memory before selecting
   `cuda`. A constructor accepting a string does not prove that a compatible
   GPU exists.
2. CPU is a reasonable first environment for the path validator and for small
   image utilities, but it does not establish that model inference is usable.
   Classifier and segmentation explicitly move their models to the requested
   device. Report generation also moves both models, but its two-model footprint
   is substantial.
3. CheXagent defaults to `torch.bfloat16`. A CUDA device without suitable
   bfloat16 support, or a CPU build with incomplete bfloat16 kernels, can fail
   during load or generation. Choose a supported dtype only after testing the
   installed model/runtime combination.
4. LLaVA-Med exposes `device`, yet `_process_input` calls `.cuda()` for token
   and image tensors and casts the image to half precision. Treat CPU mode as
   unverified and expect failures unless the implementation is adapted outside
   this operating contract.
5. RoentGen is moved to float32. This is conservative for compatibility but
   increases memory use; do not infer that a CPU run will be fast or practical.

## Quantization

- MAIRA-2 and LLaVA-Med expose independent `load_in_4bit` and
  `load_in_8bit` flags. Set at most one. Their support depends on a working
  bitsandbytes installation, a compatible Transformers/Accelerate stack, and
  a backend that supports the chosen quantization path.
- MAIRA-2's 4-bit configuration uses bfloat16 compute, NF4, and double
  quantization; 8-bit uses the library's 8-bit configuration. These reduce
  weight memory but can introduce load/device errors.
- The README's example uses 8-bit for grounding and LLaVA-Med when memory is
  constrained. This is a starting point, not a verification result.
- Classification, segmentation, and report generation do not expose a
  quantization flag in their constructors. Do not pretend that passing an
  unused keyword enables quantization.

## Cache and external resources

- `cache_dir` is caller-supplied state. The tool constructors may resolve model
  identifiers through a model hub or use already cached artifacts. This skill
  does not download weights, embed credentials, or prescribe a cache location.
- Report generation requires both named findings/impression model artifacts.
  A partial cache is insufficient.
- CheXagent and MAIRA-2 use `trust_remote_code=True`; pin and review the
  installed dependency/model revisions according to the deployment policy.
- LLaVA-Med depends on its model-builder implementation and compatible vision,
  tokenizer, and Transformers components.
- RoentGen is different: the source documents manual acquisition and a local
  model directory. If those weights are absent, route around generation rather
  than trying to download them from a bundled script.
- The benchmark dataset, cloud LLM credentials, Gradio lifecycle, and DICOM
  readers are outside this sub-skill's runtime contract.

## Compatibility hazards

- The project declares a pinned Git revision of Transformers while CheXagent
  temporarily changes the reported Transformers version during construction.
  A newer or older environment may therefore fail in model loading or
  generation even if imports succeed.
- `generation.py` relies on Diffusers pipeline call semantics; mismatched
  Diffusers/Transformers versions can reject arguments or fail while loading
  the scheduler/components.
- `report_generation.py` passes a `GenerationConfig` containing `beam_width`.
  If the installed generation stack rejects that field, treat it as a
  compatibility blocker and do not silently change generation behavior.
- `numpy<2`, Torch, TorchVision, TorchXRayVision, scikit-image, Pillow,
  Transformers, Accelerate, bitsandbytes, and Diffusers must be mutually
  compatible. Import success alone is not inference verification.

## What remains unverified by default

Without cached weights and a compatible accelerator, the following remain
unverified: numerical classification quality, segmentation mask quality,
report factuality, CheXagent/LLaVA answer quality, MAIRA-2 localization quality,
and RoentGen image fidelity. A successful constructor or a saved artifact only
proves that one path executed; it does not validate clinical correctness.
