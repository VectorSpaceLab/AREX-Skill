# Chest-X-ray workflows

These workflows keep tool choice explicit and bound model/resource use. They
assume an image has already been obtained; DICOM conversion and display belong
to the image-data utility workflow.

## 1. Preflight and declare the run

Use the safe helper before importing MedRAX model modules:

```bash
python scripts/validate_inputs.py --tool classifier --image-path IMAGE
python scripts/validate_inputs.py --tool segmentation --image-path IMAGE --organ "Left Lung"
python scripts/validate_inputs.py --tool grounding --image-path IMAGE --phrase "Pleural effusion"
python scripts/validate_inputs.py --tool vqa --image-path IMAGE --prompt "Describe the cardiac silhouette"
```

The helper checks file type, existence, required fields, organ spellings, and
bounded numeric values. It does not decode pixels, load weights, access a
network, or claim that inference will work.

Before construction, record:

- one selected tool and its exact constructor options;
- whether the image is a JPG/PNG conversion or native image file;
- device, dtype, quantization flags, and available memory;
- whether all required model artifacts are already available;
- a writable caller-managed temporary output directory;
- the stop condition (for example, no weight download or no CUDA fallback).

## 2. Bounded tool selection

| Question | Preferred tool | Stop or route when |
|---|---|---|
| Need a broad numeric screen? | Classifier | Do not interpret scores as diagnosis or calibration |
| Need anatomy masks? | Segmentation | Invalid organ names fail; non-DICOM area is approximate |
| Need a structured draft? | Report generator | Either model missing means no complete report |
| Need a visual answer over one/many images? | CheXagent VQA | Avoid if bfloat16/remote-code/CUDA is unavailable |
| Need a location for a phrase? | MAIRA-2 grounding | Empty predictions are a valid no-finding status; do not force a box |
| Need general biomedical QA? | LLaVA-Med | Prefer CheXagent for detailed CXR; CPU is unverified |
| Need synthetic training/demo data? | RoentGen | Require manually provisioned weights and label output synthetic |

If the user asks for more than one observation, run the smallest sequential set
rather than constructing all models. A common bounded set is classifier plus
one of segmentation or grounding. A report can be added only after memory and
model availability are checked.

## 3. Common invocation pattern

The classes are `BaseTool` objects. Use a caller-owned variable for each tool
and pass the schema fields, for example:

```python
classifier = ChestXRayClassifierTool(device=device)
scores, meta = classifier.invoke({"image_path": image_path})
if meta.get("analysis_status") != "completed":
    raise RuntimeError(meta)
```

For every tool:

1. Preserve the returned metadata before displaying or summarizing output.
2. Check `analysis_status` (`completed`, `completed_no_finding`, or `failed`).
3. Confirm any returned artifact path is writable and exists before handing it to
   another step.
4. Keep raw scores, boxes, masks, and text separate; do not turn a model draft
   into a clinical conclusion automatically.
5. Release the model before constructing the next large tool when memory is
   tight. Exact cleanup is environment-dependent and outside this skill.

## 4. Classification then localization

Use this bounded two-step workflow when the question asks both “what might be
present?” and “where?”

1. Run the classifier and sort or report scores without inventing a threshold.
2. Select only a phrase supported by the question or a high-priority review
   criterion; do not automatically ground all 18 labels.
3. Run MAIRA-2 with that phrase and keep `model_coordinates` and
   `image_coordinates` named separately.
4. If grounding returns `completed_no_finding`, report that no box was decoded;
   do not replace it with a full-image box.
5. If the overlay is saved, verify it visually through the display workflow;
   do not build a second display pipeline here.

This sequence is resource-bounded but does not establish classifier-grounding
agreement or diagnostic accuracy.

## 5. Segmentation with honest metrics

1. Validate `organs` against the exact 14-name map. If no list is needed, omit
   the field to request all organs.
2. Run the tool and capture `segmentation_image_path`, `metrics`, and metadata.
3. Explain that masks are center-crop/512-resize predictions aligned back to the
   source image. The source's 0.2 mm/pixel assumption makes `area_cm2`
   approximate for JPG/PNG and not physically accurate.
4. Treat a missing organ in `processed_organs` as an empty/failed mask outcome,
   not as proof of absence. Check status and error details.
5. Route DICOM pixel-spacing interpretation and image display elsewhere.

A synthetic negative test should use one invalid organ and a non-DICOM PNG:
the invalid name must produce a failed status with a clear `Invalid organs`
error, while the valid PNG may produce masks but must not be reported as an
accurate physical-area measurement.

## 6. Low-memory selected set

Use this order when resources are uncertain:

1. Run the standard-library validator only.
2. Start one CPU-capable utility or a single classifier/segmentation instance
   on CPU if a smoke check is required; expect slow execution and record that
   model quality was not tested.
3. If a CUDA device is available, choose exactly one CUDA model: classifier for
   18 labels, segmentation for anatomy, or MAIRA-2 with one quantization mode
   for localization.
4. Do not instantiate report generation (two models), CheXagent 2-3B,
   LLaVA-Med 7B, or RoentGen until memory and artifacts are confirmed.
5. Stop after the selected result and preserve unverified capabilities in the
   handoff.

This is a safe operating plan, not a claim that CPU inference or 4/8-bit
loading has been validated in the current environment.

## 7. Text and synthetic outputs

- For report generation, preserve the `FINDINGS` and `IMPRESSION` sections
  separately in downstream notes even though the tool returns one string.
- For CheXagent or LLaVA-Med, write the exact prompt alongside the answer and
  do not add a confidence value that the model did not return.
- For RoentGen, label every saved output as synthetic and retain generation
  parameters. Never use it as a patient image or as a ground-truth label.
