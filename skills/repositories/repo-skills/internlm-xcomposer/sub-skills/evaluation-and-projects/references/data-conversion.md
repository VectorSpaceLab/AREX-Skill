# Data Conversion And Result Packaging

Use this reference when the user needs a non-executing plan for converting benchmark data, merging model predictions, or packaging submissions. The conversion patterns below are distilled from repository scripts; do not assume the original scripts are present.

## Common Prediction JSONL Contract

ShareGPT4V and DualFocus evaluation scripts generally write one JSON object per line with at least:

```json
{"question_id": 123, "text": "answer text"}
```

Some adapters may use `prediction` instead of `text`. Before conversion, validate:

- every line parses as JSON;
- every required benchmark question id appears exactly once unless the official format allows blanks;
- answer text is normalized as required by the target benchmark;
- chunk files are merged in a deterministic order;
- the output directory exists and is outside this runtime skill tree.

## MMBench XLSX Upload

Two converter styles appear in the evidence:

- ShareGPT4V style: read official annotation TSV, read `<result-dir>/<experiment>.jsonl`, drop metadata columns, insert a `prediction` column, and write `<upload-dir>/<experiment>.xlsx`.
- DualFocus style: read official annotation TSV, read a merged prediction JSONL passed as `--pred-file`, insert `prediction`, and write a single XLSX `--save-file`.

Expected TSV columns include `index` plus metadata columns such as hint, category, source, image, comment, and l2-category. If the official TSV schema changes, update the drop-column list before conversion. Official score still requires MMBench/OpenCompass submission.

Checklist:

1. Confirm TSV split (`mmbench_dev_20230712`, `mmbench_dev_cn_20231003`, or another official split).
2. Merge chunk JSONL files into `merge.jsonl`.
3. Verify each `question_id` matches a TSV `index`.
4. Write XLSX with one `prediction` column.
5. Submit only after user approval and leaderboard/account readiness.

## SEED-Bench Upload And Local Accuracy

SEED conversion reads:

- annotation file `SEED-Bench.json`;
- merged result JSONL with `question_id` and answer text;
- output upload JSONL path.

The converter also computes local accuracy by question type and total accuracy by comparing exact option letters. A tolerance mode may accept a first-character match. Plans should state whether exact or tolerant matching is intended.

Checklist:

1. Confirm image-only versus video/full benchmark subset.
2. Ensure question ids preserve original type (integer or string).
3. Normalize predictions to option letters before local accuracy/submission.
4. Keep upload JSONL separate from raw model answers.

## GQA Official Prediction JSON

GQA conversion reads merged JSONL and writes a JSON array:

```json
[{"questionId": "...", "prediction": "lowercase answer"}]
```

The evidence strips a trailing period and lowercases the answer. After conversion, official GQA evaluation expects the file name/path used by its eval script, commonly `testdev_balanced_predictions.json` under the official data/eval directory.

Checklist:

- Confirm official GQA data and eval assets are available.
- Confirm MCQ versus short-answer variant; DualFocus evidence uses a GQA MCQ JSONL.
- Confirm any required official eval script patch for missing GQA v1.2 assets.

## MM-Vet Result JSON

MM-Vet conversion maps answer JSONL to a dictionary keyed by `v1_<question_id>`:

```json
{"v1_1": "model answer", "v1_2": "model answer"}
```

This JSON is the input to the official/GPT-based evaluator. Raw conversion is local, but scoring requires judge credentials/cost and must not be performed by this sub-skill.

## VizWiz Upload JSON

VizWiz conversion reads:

- annotation JSONL with `question_id` and image name;
- model result JSONL with `question_id` and `text`;
- output upload JSON.

It normalizes answers through an EvalAI-style answer processor and writes objects containing `image` and `answer`. Missing predictions are not tolerated in the evidence style; plan a preflight check for every annotation id.

## VQAv2 Upload JSON

VQAv2 conversion reads merged JSONL under `answers/<split>/<ckpt>/merge.jsonl` and an official split JSONL. It writes `answers_upload/<split>/<ckpt>.json` containing objects like:

```json
{"question_id": 123, "answer": "normalized answer"}
```

If a question id is missing, the evidence converter inserts an empty answer. Plans should still flag missing ids as a quality failure before submission unless the user explicitly accepts blanks.

## ScienceQA Conversion

ScienceQA conversion consumes `pid_splits.json` and `problems.json`. It builds prompts from question, context/hint, options, answer, lecture, and solution. Evidence supports prompt formats such as `QCM-LEA` and `QCM-LEPA`.

Two output families exist:

- ShareGPT4V conversation JSON: items have `id`, optional `image`, and `conversations` with human/GPT turns.
- JSONL instruction format: items have `id`, optional `image`, `instruction`, and `output`.

Image examples use paths relative to each problem id directory. Plans should specify whether captions are included in context and whether examples are test-mode (answer stub only) or train-mode (full answer).

## QBench Formatting

ShareGPT4V QBench evidence writes answer JSONL, runs a formatter, then a local dev evaluator. Plans should distinguish:

- English versus Chinese question JSONs;
- dev versus test split;
- image root naming (`images_llvisionqa` or equivalent extracted image tree);
- local dev scoring versus external test submission.

Chinese filenames can contain non-ASCII characters. Preserve exact names and avoid shell globbing assumptions.

## MME Answer Conversion

MME workflows often need to transform a generic model-answer JSONL into the official eval-tool directory shape: one text file per MME task, each line containing image name, question, ground truth, and prediction separated by tabs. The official `calculation.py` then reads the model results directory.

Plans should confirm:

- official `Your_Results` template files are present;
- image paths are resolved against the MME release root;
- model result directory name matches the argument passed to `calculation.py`.

## Legacy XComposer Notebook Outputs

Legacy notebook workflows do not have a single converter contract:

- **AI2D:** question JSONL plus image root, local multiple-choice accuracy.
- **ChartQA:** JSON test files plus image root, relaxed numeric accuracy for human and augmented splits.
- **POPE:** three JSON files for adversarial/popular/random; local F1/precision/recall/yes-ratio metrics.
- **MMMU:** prediction JSON dictionary and answer dictionary; evaluation-only script prints category/domain/overall accuracies.
- **MM-Vet/LLaVA-Wild:** raw prediction files plus GPT judge/evaluator outputs when authorized.
- **QBench:** answer artifact can be JSONL or `.json.pth` depending on workflow version; test split requires official submission formatting.

When converting old notebook output, first write down the source artifact shape, target evaluator shape, and judge/submission requirements. Do not guess an official upload format from a local score notebook.

## ShareCaptioner Output

The ShareCaptioner batch utility writes a JSON list of dictionaries:

```json
[{"/path/to/image1.jpg": "caption text"}, {"/path/to/image2.jpg": "caption text"}]
```

A downstream data-preparation plan may need to transform this into image-text pair JSON, conversation JSON, or another dataset schema. Treat generated captions as model output with data/license implications, not as verified ground truth.

## Preflight Validation Checklist

Before any converter is executed by an execution-capable workflow:

1. Count expected annotations and prediction rows.
2. Check ids and split names match exactly.
3. Confirm output format and file extension expected by the benchmark server/evaluator.
4. Confirm local metric versus official submission boundary.
5. Confirm no converter will overwrite valuable raw predictions without backup.
6. Confirm GPT/OpenAI judge calls and external submissions remain disabled unless separately approved.
