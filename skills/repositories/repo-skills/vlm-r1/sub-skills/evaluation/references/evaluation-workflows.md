# Evaluation Workflows

This reference distills VLM-R1's REC and OVD evaluation behavior into reusable recipes. It is self-contained: future agents should adapt these notes and the bundled offline scorer instead of depending on the original checkout.

## Quick decision map

| User goal | Recommended path |
| --- | --- |
| Score a saved REC/OVD JSON or JSONL file | Use `../scripts/evaluate_bbox_predictions.py`; no model or image download is needed. |
| Compare REC GRPO/R1 to SFT/baseline | Use the REC distributed flow below; choose the R1 or baseline prompt/parser differences explicitly. |
| Evaluate an InternVL REC checkpoint | Use the InternVL differences below; do not reuse Qwen processor/image-grid code. |
| Evaluate OVD with a Qwen checkpoint | Use the OVD single-device flow below; tune `batch_size`, `sample_num`, and `device_map`. |
| Generate a checkpoint or saved outputs first | Route to `../../training-workflows/SKILL.md`. |
| Explain data/reward JSONL schema | Route to `../../data-and-rewards/SKILL.md`. |

## REC distributed evaluation flow

REC evaluation is a multi-GPU `torchrun` recipe over JSON annotation files. Each JSON row is expected to contain at least:

```json
{
  "image": "relative/image/path.jpg",
  "problem": "the referring-expression question",
  "solution": [x1, y1, x2, y2]
}
```

Use these parameters when adapting the recipe:

| Parameter | Meaning | Native-style defaults to revisit |
| --- | --- | --- |
| `model_dir` | Qwen/InternVL checkpoint directory to load. | R1 and SFT use different checkpoint families. |
| `data_root` | Directory containing `{dataset}.json` annotation files. | REC and InternVL variants may use different processed annotation sets. |
| `image_root` | Directory joined with each row's relative `image`. | COCO for RefCOCO variants; LISA for out-of-domain `lisa_test`. |
| `datasets` | Dataset names without `.json`. | `refcoco_val`, `refcocop_val`, `refcocog_val`, or `lisa_test`. |
| `output_dir`/pattern | Where per-dataset JSON summaries are saved. | Include dataset, run name, and step for comparisons. |
| `batch_size` | Per-rank generation batch size. | R1 used smaller batches than baseline in the distilled recipe. |
| `sample_limit` | Max shuffled rows per dataset. | 2000 for REC recipes. |
| `seed` | Shuffle seed before truncation. | 42. |
| `nproc_per_node` | Number of GPU worker processes. | Match visible GPUs; every process uses its `LOCAL_RANK`. |

Distributed flow:

1. Initialize NCCL distributed processing from `LOCAL_RANK`; set the CUDA device to the local rank.
2. Load the model on the local rank. For Qwen2.5-VL, use bfloat16, flash attention when available, and `device_map={"": local_rank}`.
3. Load the processor/tokenizer from the same checkpoint.
4. Read and shuffle each dataset with a fixed seed, then truncate to the sample limit.
5. Split rows by rank with integer division and let the last rank receive the remainder.
6. Build chat messages with one image URI and one text prompt per row.
7. Batch the messages, apply the chat template, process vision inputs, move tensors to the rank device, generate deterministically, trim prompt tokens from generated IDs, and decode text.
8. For Qwen REC, also record the processor input size from `image_grid_thw` as `(height, width)` using the grid value times 14, plus the original image size as `(height, width)`.
9. Gather `(global_index, output)` pairs from every rank with `all_gather_object`; rank 0 reconstructs the full ordered result list.
10. Extract bbox predictions, resize when required, compute IoU against `solution`, count `IoU > 0.5` as correct, then write a JSON summary.

### REC Qwen R1 recipe

Prompt form:

```text
{Question} First output the thinking process in <think> </think> tags and then output the final answer in <answer> </answer> tags. Output the final answer in JSON format.
```

Prediction parser:

- Look inside the final `<answer>...</answer>` block.
- Accept a JSON-looking answer containing four integer coordinates, for example `{"bbox_2d": [10, 20, 30, 40]}`.
- If no bbox is found, use `[0, 0, 0, 0]` so the row scores as incorrect rather than crashing.

Qwen REC resize rule:

```text
x1' = x1 / input_width  * image_width
y1' = y1 / input_height * image_height
x2' = x2 / input_width  * image_width
y2' = y2 / input_height * image_height
```

Use this only when the prediction came from generated Qwen text in processor input coordinates. Do not apply it a second time to already-resized `extracted_answer` values.

### REC SFT/baseline recipe

Baseline/SFT evaluation uses the same distributed structure and IoU threshold, but differs in prompt and parser:

- Prompt: `{Question} Please provide the bounding box coordinate in JSON format.`
- Parser: take the first bracketed four-number list anywhere in the model output; floats and negative signs are accepted.
- The baseline recipe still computes Qwen input/image sizes and internally resizes parsed boxes before IoU.
- When producing saved outputs for later audit, include `input_size` and `image_size` if the stored `extracted_answer` is not already resized.

### REC InternVL recipe

InternVL evaluation keeps the distributed rank-splitting/gather/IoU pattern but does not use Qwen's processor or `image_grid_thw` resize path.

Key differences:

- Use the VLM-R1 InternVL module's model-class lookup and prompt/input preparation helpers.
- Load the model with bfloat16, `trust_remote_code=True`, and flash attention when available.
- Use an `AutoTokenizer`; set the pad token to EOS when necessary and apply the module's post-model initialization.
- Set `max_anyres_num` to the intended image tiling cap before generation.
- Build prompts via the module, load PIL images, prepare model inputs, cast `pixel_values` to bfloat16, and filter module-declared non-generation parameters before calling `generate`.
- Decode full outputs with the tokenizer; parse the `<answer>...</answer>` block for a bracketed integer bbox.
- Score the parsed bbox directly against `solution` with IoU > 0.5; no Qwen post-resize is part of the distilled InternVL evaluation recipe.

## OVD single-device evaluation flow

OVD evaluation is a one-device Qwen recipe, not distributed in the distilled source behavior.

Expected annotation row fields:

```json
{
  "image": "relative/image/path.jpg",
  "normal_caption": "class/category prompt text",
  "solution": [x1, y1, x2, y2],
  "normalized_solution": [x1, y1, x2, y2]
}
```

Important parameters:

| Parameter | Meaning | Native-style default |
| --- | --- | --- |
| `model_dir` | Qwen OVD checkpoint directory. | User-supplied. |
| `data_root` | Directory containing `{dataset}.json`. | User-supplied. |
| `image_root` | Root joined with row `image`. | User-supplied. |
| `datasets` | Evaluation dataset names. | RefCOCO variants are common defaults. |
| `question_template` | Must contain `{Question}`; receives `normal_caption`. | Think/answer plus JSON final answer instruction. |
| `batch_size` | Generation batch size. | 32, reduce on OOM. |
| `sample_num` | Max shuffled rows per dataset. | 500. |
| `seed` | Shuffle seed. | 42. |
| `device_map` | Generation device. | `cuda:0` in a single-device run. |

OVD flow:

1. Load Qwen2.5-VL with bfloat16, flash attention when available, and the requested `device_map`.
2. Build one image-plus-text chat message per row, where text is `question_template.format(Question=row["normal_caption"])`.
3. Batch messages, apply the chat template, process vision inputs, move tensors to the selected device, generate deterministically, trim prompt tokens, and decode.
4. Extract the first bbox from a fenced JSON block, typically an array of objects such as:

   ```json
   [{"bbox_2d": [10, 20, 30, 40], "label": "target"}]
   ```

5. Compare against `solution` unless the parser explicitly marks the prediction as normalized; in the distilled native behavior the parser always treats predictions as not normalized.
6. Count IoU > 0.5 as correct and write `accuracy` plus per-row `question`, `ground_truth`, `model_output`, `extracted_answer`, `correct`, and `iou`.

For multi-object OVD reward-style outputs, use the offline scorer's OVD mode. It can parse fenced JSON arrays of `{bbox_2d, label}` objects and report greedy IoU-threshold matches, precision, recall, and row correctness.

## Bounding-box and IoU conventions

All recipes use `[x1, y1, x2, y2]` boxes. The IoU helper follows the native inclusive-intersection convention:

```text
inter_x2 = min(box1.x2 - 1, box2.x2 - 1)
inter_y2 = min(box1.y2 - 1, box2.y2 - 1)
if inter_x1 < inter_x2 and inter_y1 < inter_y2:
    inter = (inter_x2 - inter_x1 + 1) * (inter_y2 - inter_y1 + 1)
else:
    inter = 0
union = area(box1) + area(box2) - inter
IoU = inter / union
```

A prediction is correct when `IoU > 0.5` rather than `>= 0.5`.

## Output JSON schemas

### Native-style REC output

```json
{
  "accuracy": 73.25,
  "results": [
    {
      "image": "relative/image.jpg",
      "question": "question text",
      "ground_truth": [1, 2, 3, 4],
      "model_output": "raw generated text",
      "input_size": [height, width],
      "image_size": [height, width],
      "extracted_answer": [1.0, 2.0, 3.0, 4.0],
      "correct": 1
    }
  ]
}
```

Baseline and InternVL outputs may omit `input_size`/`image_size` depending on how the adapted run stores already-resized answers.

### Native-style OVD output

```json
{
  "accuracy": 68.0,
  "results": [
    {
      "question": "prompt text",
      "ground_truth": [1, 2, 3, 4],
      "model_output": "raw generated text with fenced JSON",
      "extracted_answer": [1, 2, 3, 4],
      "correct": 1,
      "iou": 0.78
    }
  ]
}
```

### Offline scorer output

`../scripts/evaluate_bbox_predictions.py` writes:

```json
{
  "schema_version": "vlm-r1-bbox-score-v1",
  "task": "rec",
  "iou_threshold": 0.5,
  "summary": {
    "rows": 2,
    "scored": 2,
    "correct": 1,
    "accuracy": 0.5,
    "accuracy_percent": 50.0,
    "mean_iou": 0.5,
    "parse_errors": 0,
    "missing_ground_truth": 0
  },
  "results": [
    {
      "index": 0,
      "prediction_key": "model_output",
      "ground_truth_key": "ground_truth",
      "pred_bbox": [1.0, 2.0, 3.0, 4.0],
      "gt_bbox": [1.0, 2.0, 3.0, 4.0],
      "iou": 1.0,
      "correct": true,
      "scored": true,
      "resized": false,
      "warnings": []
    }
  ]
}
```

OVD mode returns `pred_boxes`, `gt_boxes`, `matches`, `precision`, `recall`, and `mean_iou` per row.

## Offline scoring examples

Score native-style REC output where `extracted_answer` is already resized:

```bash
python ../scripts/evaluate_bbox_predictions.py \
  --task rec \
  --input saved_rec_results.json \
  --output scored_rec.json
```

Score raw Qwen REC generations that need resize from processor input coordinates to image coordinates:

```bash
python ../scripts/evaluate_bbox_predictions.py \
  --task rec \
  --input raw_rec_outputs.jsonl \
  --prediction-key model_output \
  --ground-truth-key solution \
  --resize-mode on \
  --input-size-key input_size \
  --image-size-key image_size \
  --output scored_rec.json
```

Score OVD rows with fenced JSON predictions and continue through malformed rows:

```bash
python ../scripts/evaluate_bbox_predictions.py \
  --task ovd \
  --input saved_ovd_outputs.jsonl \
  --prediction-key model_output \
  --ground-truth-key ground_truth \
  --output scored_ovd.json
```

Use `--require-label` for reward-style OVD arrays when predicted and ground-truth object labels must match before a bbox can be counted as a match.
