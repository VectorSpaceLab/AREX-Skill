---
name: chest-xray-analysis
description: "Operate MedRAX chest-X-ray classification, segmentation, report,
  visual-QA, phrase-grounding, and optional image-generation tools with explicit
  resource and output checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chest X-ray analysis

Use this skill when a Researcher needs to operate one of MedRAX's chest-X-ray
model tools on an already available JPG or PNG image. Treat all model outputs as
assistive observations, not a diagnosis or a measurement suitable for clinical
decision-making without qualified review.

## Scope and routing

- Use **classification** for a bounded screen across the 18 TorchXRayVision
  pathology labels.
- Use **segmentation** for anatomical masks, an overlay, and approximate image
  metrics; route DICOM conversion or display concerns to `image-data-utilities`.
- Use **report generation** for a deterministic two-section findings/impression
  draft.
- Use **CheXagent VQA** for multi-image visual questions and broad CXR reasoning.
- Use **MAIRA-2 grounding** for a phrase and its localized bounding boxes.
- Use **LLaVA-Med** only for optional, broad medical visual QA; it is not the
  preferred detailed CXR interpreter.
- Use **RoentGen generation** only for synthetic-image experiments when its
  manually supplied weights are already available.
- Route tool selection, graph execution, and agent state to
  `agent-orchestration`; route benchmark claims to `benchmark-evaluation`.

Do not accept DICOM as a direct input to these tools: the tool schemas describe
JPG/PNG paths. Use the image-data utility workflow before analysis when a DICOM
study must be converted, and preserve the fact that conversion can change
metadata and pixel semantics.

## Fast decision matrix

| Need | Select | Main cost or caveat |
|---|---|---|
| 18-label abnormality likelihoods | `ChestXRayClassifierTool` | DenseNet weights; values are probabilities, not calibrated diagnoses |
| Organ boundaries/overlay | `ChestXRaySegmentationTool` | PSPNet; area is not accurate for non-DICOM input |
| Findings plus impression prose | `ChestXRayReportGeneratorTool` | Two encoder-decoder models; substantial model storage |
| Ask one or more image questions | `XRayVQATool` | CheXagent 2-3B, remote code, usually CUDA and bfloat16 |
| Locate a phrase | `XRayPhraseGroundingTool` | MAIRA-2; CUDA and optional bitsandbytes are practical constraints |
| General medical image QA | `LlavaMedTool` | Large optional model; implementation uses CUDA tensors directly |
| Create a synthetic CXR | `ChestXRayGeneratorTool` | RoentGen weights must be supplied manually; no clinical use |

For a low-memory run, start with CPU-side path/schema validation, then choose
**one** CUDA tool: classifier for labels, segmentation for anatomy, grounding
with 8-bit loading for localization, or CheXagent only when QA is essential.
Keep report generation, LLaVA-Med, and RoentGen disabled until their weights,
CUDA memory, and compatible dependencies are proven. This selection verifies
resource discipline, not model quality; unrun models remain unverified.

## Operating procedure

1. **Preflight without loading models.** Run the bundled validator from
   `scripts/validate_inputs.py`. Confirm regular files, `.jpg`, `.jpeg`, or
   `.png` suffixes, required text fields, positive token/image parameters, and
   exact segmentation organ names.
2. **Declare resources.** Record the requested device, dtype, quantization,
   caller-managed cache/temp locations, whether weights are already present,
   and whether the run may use external model access. Never silently download
   a large model or require credentials.
3. **Construct only the selected tool.** Constructor options and model
   prerequisites are in `references/api-reference.md` and
   `references/model-overview.md`. Avoid initializing every tool at once.
4. **Invoke with the tool schema.** MedRAX tools are LangChain `BaseTool`
   objects; pass the documented field names. They return a value plus metadata
   (except an error may be encoded in the value). Check `analysis_status` and
   preserve returned paths before interpreting content.
5. **Check output semantics.** Classifier scores are per-label likelihood
   values. Segmentation metrics are mask-derived image metrics. Grounding
   boxes use normalized coordinates unless converted to original-image pixels.
   Generated prose and images require human review.
6. **Recover narrowly.** For an error, use the matching row in
   `references/troubleshooting.md`; do not switch devices, quantization, or
   model sources blindly. Re-run only after recording the changed setting.

## Output checklist

- Record input image identity, requested tool, constructor settings, device,
  dtype/quantization, model availability, and `analysis_status`.
- Classification returns `(scores, metadata)` where scores map the 18 labels to
  numeric values in the source's 0–1 convention.
- Segmentation returns `(output, metadata)`: `segmentation_image_path`, a
  per-organ `metrics` dictionary, original/model sizes, requested and processed
  organs, and the fixed pixel-spacing assumption. An empty organ result is not
  proof of absence.
- Reports contain `CHEST X-RAY REPORT`, `FINDINGS`, and `IMPRESSION`, plus
  metadata listing both generated sections.
- VQA returns `{"response": text}` and metadata containing image paths, prompt,
  token limit, and status. It does not expose a calibrated confidence score.
- Grounding returns predictions with model and original-image boxes and may
  return `visualization_path`; `completed_no_finding` is distinct from failure.
- LLaVA-Med returns answer text and question/image/status metadata.
- RoentGen returns a generated `image_path` and prompt, sampling, device, and
  size metadata. Generated images are synthetic artifacts, not evidence.

## High-risk interpretation rules

- Do not threshold classifier scores as diagnoses unless a separately validated
  threshold is supplied; the tool supplies no threshold or calibration.
- Do not report segmentation `area_cm2` as physically accurate for JPG/PNG.
  The implementation uses a fixed 0.2 mm/pixel assumption; request DICOM-aware
  processing for measurement work and route conversion/display separately.
- Grounding coordinates are `[x_min, y_min, x_max, y_max]` in normalized
  model/image conventions as documented in the API reference. Use the returned
  `image_coordinates` for the original image and do not mix the two spaces.
- A missing/empty prediction, a failed model load, and a model's negative
  finding are different observations. Preserve status and error metadata.
- Reports, VQA answers, LLaVA answers, and generated images can hallucinate;
  corroborate with the image and an appropriate validated workflow.

## References

- [API reference](references/api-reference.md): exact fields, constructors,
  outputs, labels, coordinates, and artifacts.
- [Model overview](references/model-overview.md): weights, devices, dtypes,
  quantization, caches, and external-resource boundaries.
- [Workflows](references/workflows.md): bounded selection and low-memory runs.
- [Troubleshooting](references/troubleshooting.md): predictable failures and
  recovery actions.
- [Safe input validator](scripts/validate_inputs.py): local path/schema checks
  only; it never imports model libraries, downloads weights, or runs inference.
