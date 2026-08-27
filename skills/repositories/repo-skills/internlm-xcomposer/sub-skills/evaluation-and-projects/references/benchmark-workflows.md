# Benchmark Workflows

This reference distills the repository's benchmark evidence into non-executing plans. Treat every command below as a command pattern to adapt in an approved execution environment; this skill does not provide the original checkout scripts and does not run models.

## Planning Gates

For every benchmark, decide these before execution is delegated elsewhere:

- **Data access:** benchmark archives, image/video/audio roots, official eval tools, and license terms are external. Do not assume they are present.
- **Model access:** large checkpoints normally require CUDA and accepted model licenses.
- **Judge/submission:** some workflows produce only predictions locally; official scores require GPT/OpenAI judges or an external leaderboard server.
- **Runtime:** legacy image workflows generally used single-GPU CUDA; ShareGPT4V/DualFocus and OmniLive benchmarks shard by `CUDA_VISIBLE_DEVICES`; OmniLive audio uses distributed NCCL; VLMEvalKit examples use `torchrun`.
- **Result ownership:** keep predictions, converted upload files, and score logs outside this skill tree.

## Current Top-Level VLMEvalKit Route

Use VLMEvalKit as the preferred route for current general visual QA and for XComposer2-4KHD when a benchmark is supported there. The top-level evaluation notes state that general visual QA evaluation is supported by VLMEvalKit; video and high-resolution benchmark notes were marked as pending in that top-level document.

Plan shape:

1. Install/configure VLMEvalKit in the user's benchmark environment.
2. Select or implement the XComposer model adapter expected by VLMEvalKit.
3. Provide model path, data identifiers, GPU count, and output directory.
4. Run only after benchmark data and license acceptance are confirmed.
5. Use VLMEvalKit outputs or official submission paths according to the dataset.

OmniLive MMBench-Video evidence used a VLMEvalKit-style route: adjust the `XComposer2d5` model path to the OmniLive base checkpoint and run a multi-GPU command pattern such as `torchrun --nproc-per-node=8 run.py --data MMBench-Video --model XComposer2d5 --nframe 64`. This needs VLMEvalKit, eight GPUs in the original example, video data, and no source-checkout dependency from this skill.

## Legacy XComposer 1.0 / 2.0 Image Benchmarks

### MME

- **Purpose:** perception and cognition subtasks including existence, count, position, color, OCR, commonsense, numerical calculation, translation, and code reasoning.
- **Data layout:** official `eval_tool` plus `MME_Benchmark_release` images. The old scripts expected an eval-tool `Your_Results` template and wrote a model-named results directory.
- **Command pattern:** single-GPU inference over MME prompt text files, then official `calculation.py --results_dir <model-results-dir>`.
- **Result shape:** tab-separated lines containing image, question, ground truth, and model response; official tool prints perception/cognition scores.
- **Requirements/blockers:** CUDA, full MME data, official eval tool, model checkpoint, source-era scripts or a reimplementation. No external GPT judge is needed for the MME calculation itself.

### MMBench / MMBench-CN / CCBench

- **Data layout:** MMBench TSV files under a benchmark data directory. XComposer2 evidence used `mmbench_test_20230712.tsv` and a CN test TSV; ShareGPT4V/DualFocus use dev TSVs in their `playground/data/eval/mmbench` layout.
- **Command pattern:** shard or single-GPU inference writes JSONL or directly writes an Excel submission file; converter inserts a `prediction` column into the official TSV-derived table.
- **Result/submission:** local output is usually `.xlsx` under an upload directory; official scoring requires OpenCompass/MMBench submission server. The benchmark's circular-eval design may involve external judge infrastructure outside local scripts.
- **Requirements/blockers:** CUDA, pandas/openpyxl or xlsxwriter, official TSV with expected columns, leaderboard account for final score. Do not treat local XLSX creation as an official score.

### SEED-Bench Image

- **Data layout:** `SEED-Bench-image` directory plus `SEED-Bench.json` annotation file.
- **Command pattern:** multiple-choice inference over images, compare predicted option letter to `answer`, and optionally write an upload JSONL.
- **Result/submission:** local accuracy by question type and total; optional official leaderboard submission.
- **Requirements/blockers:** dataset license/download, CUDA for inference, exact question ids and image paths.

### QBench / Chinese-QBench

- **Data layout:** English `llvisionqa_<split>.json` and Chinese `质衡-问答-<split>.json` files plus extracted `images_llvisionqa`/`llv_dev` images.
- **Command pattern:** run dev or test inference, normalize option answers, and save answer files such as JSONL or `.json.pth` depending on workflow version.
- **Result/submission:** dev evaluation can be local in ShareGPT4V evidence; test results require QBench submission instructions/server.
- **Requirements/blockers:** QBench data, correct split and Chinese filenames, CUDA, output format expected by the QBench tools.

### MMMU

- **Data layout:** image files plus validation JSON/answer JSON. The old notebook emitted a dictionary mapping data ids to parsed predictions; `main_eval_only.py` consumes `--output_path` and `--answer_path`.
- **Command pattern:** produce prediction JSON with multiple-choice letters or open answers, then run the evaluation-only parser to group results by category/domain and print overall/domain accuracy.
- **Result shape:** printed dictionary with `Overall`, domain subtotals, category counts, and accuracies.
- **Requirements/blockers:** MMMU data and images, CUDA for prediction generation, answer dictionary. Evaluation-only parsing is local once predictions exist.

### MM-Vet

- **Data layout:** `mm-vet.json` plus `images` directory.
- **Command pattern:** prediction notebook writes a JSON result mapping question ids to answers; a separate evaluator notebook grades with GPT-4.
- **Result/submission:** raw prediction JSON is local. Official-style capability CSV/grade JSON requires GPT/OpenAI calls and an API key.
- **Requirements/blockers:** MM-Vet data, CUDA for prediction, OpenAI/GPT judge access for scoring. This sub-skill can plan the handoff but must not call the judge.

### POPE

- **Data layout:** COCO POPE adversarial/popular/random JSON files under a JSON data directory; images are referenced by those annotations.
- **Command pattern:** run inference, convert yes/no responses, and compute TP/FP/TN/FN, accuracy, precision, recall, F1, and yes ratio.
- **Result shape:** local metrics for adversarial, popular, random, and average F1.
- **Requirements/blockers:** POPE files, image root, CUDA for prediction. No GPT judge is required.

### ChartQA

- **Data layout:** ChartQA test JSONs for human and augmented splits plus `test/png` images.
- **Command pattern:** generate answers, then evaluate relaxed accuracy: numeric predictions within about 5% tolerance can count as correct; non-numeric answers are exact normalized matches.
- **Result shape:** human, augmented, and overall accuracy.
- **Requirements/blockers:** ChartQA dataset license/download, CUDA for prediction, exact image names.

### AI2D

- **Data layout:** processed images plus an `ai2d_test.jsonl` question file.
- **Command pattern:** generate multiple-choice answers and compute accuracy locally.
- **Result shape:** overall accuracy.
- **Requirements/blockers:** processed image pack, CUDA for prediction, source-era notebook or reimplementation.

### LLaVA-Bench-In-The-Wild

- **Data layout:** questions, images, GPT-4 reference answers, and context files.
- **Command pattern:** generate answer JSONL, then compare model answer against GPT-4 reference with GPT-4 judging prompts and summarize reviews.
- **Result/submission:** answer JSONL is local; judged score JSONL and summaries require OpenAI/GPT calls.
- **Requirements/blockers:** data pack, CUDA for prediction, OpenAI/GPT judge key and cost budget for scoring. This sub-skill must not call the judge.

### MathVista and HallusionBench

- **Data layout:** task-specific JSON/images from the official datasets.
- **Command pattern:** source-era notebooks generated answers and used local parsing plus, for some MathVista extraction cases, GPT/OpenAI extraction.
- **Result shape:** task-specific accuracy; HallusionBench evidence evaluated the image part.
- **Requirements/blockers:** dataset access, CUDA, and possible GPT/OpenAI extraction or judge calls. Keep those calls outside this sub-skill.

## OmniLive Benchmarks

OmniLive benchmark scripts are benchmark-planning evidence only. Actual OmniLive inference, model layout, and service tasks belong to sibling `omnilive`.

### ASR: WenetSpeech and LibriSpeech

- **Data layout:** JSONL manifests with `audio`, `gt`, `source`, and optional `task`; each collection has an audio root placeholder that must be replaced with the real audio root.
- **Command pattern:** distributed launch of `evaluate_asr.py` with `--checkpoint <audio-checkpoint> --dataset <librispeech|wenet_test_meeting|wenet_test_net> --batch-size <n> --num-workers <n>`.
- **Result shape:** rank 0 writes timestamped result JSON and prints WER by `source`.
- **Requirements/blockers:** CUDA/NCCL, Qwen2-Audio processor/model dependencies, ffmpeg audio decoding, editdistance, sacrebleu tokenizer, Chinese text normalization dependencies, full audio dataset licenses.

### MLVU

- **Data layout:** video root contains subdirectories `1_plotQA`, `2_needle`, `3_ego`, `4_count`, `5_order`, `6_anomaly_reco`, and `7_topic_reasoning`, each containing videos named by the benchmark JSON.
- **Command pattern:** `CUDA_VISIBLE_DEVICES=<list> sh .../mlvu.sh <video-root>` in source-era form; internally chunks by GPU, writes `outputs/mlvu/<idx>_of_<chunks>.json`, then averages per task.
- **Result shape:** printed per-task mean accuracy plus overall average.
- **Requirements/blockers:** CUDA GPUs, Decord, PIL, Torch/TorchVision, model base checkpoint, benchmark videos.

### Video-MME

- **Data layout:** video root contains `<videoID>.mp4` files. A parquet annotation file provides duration split (`short`, `medium`, `long`), question, options, and answer.
- **Command pattern:** sharded inference writes `outputs/video_mme/<idx>_of_<chunks>.json`; evaluator averages by duration split and overall.
- **Result shape:** per-duration means plus overall average.
- **Requirements/blockers:** CUDA, Decord, pandas/pyarrow, model base checkpoint, Video-MME videos.

### StreamingBench

- **Data layout:** video root contains `real/sample_<id>/video.mp4` directories; data file is a StreamingBench questions JSON for the selected task.
- **Command pattern:** sharded evaluation writes `outputs/streamingbench/real_output_IXC2d5_OL_<idx>.json`, then a count/aggregation utility reads the output directory.
- **Result shape:** benchmark-category metrics and overall score.
- **Requirements/blockers:** CUDA, OmniLive model path, StreamingBench data, exact working directory assumptions. Check GPU mapping carefully when a nonzero `CUDA_VISIBLE_DEVICES` list is used.

### MVBench

- **Data layout:** a single video root expands placeholders for many component datasets: Charades, Something-Something V2, Moments in Time, FunQA, CLEVRER, Perception, STA, SceneQA, NTU RGB+D, VLNQA, TVQA frames, and others.
- **Command pattern:** sharded inference over 20 tasks writes `outputs/mvbench/<idx>_of_<chunks>.json`, then averages by task and overall.
- **Result shape:** per-task means and overall average.
- **Requirements/blockers:** CUDA, Decord, many separately licensed video datasets, some frame-folder tasks, model base checkpoint.

## Quick Workflow Selection

| User asks for | Use | Key blockers to mention |
| --- | --- | --- |
| Current XComposer visual QA benchmark | VLMEvalKit route | VLMEvalKit model adapter, dataset license, CUDA/GPU budget |
| Reproducing old XComposer2 paper benchmark table | Legacy image workflow plan | Source-era notebooks/scripts or reimplementation, benchmark data, CUDA, GPT judges for MM-Vet/LLaVA-Wild/MathVista extraction |
| OmniLive video/audio benchmark | OmniLive benchmark plan here, sibling `omnilive` for actual inference setup | Model base/audio checkpoint, Decord/Swift/ffmpeg, CUDA/NCCL, large video/audio data |
| MMBench or VQAv2 official score | Converter/submission plan | Correct upload file, server account, no local official score unless official evaluator exists |
| Dataset/result conversion | `data-conversion.md` | JSONL schema, question id alignment, TSV columns, output directory |
