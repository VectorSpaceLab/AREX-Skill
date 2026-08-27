#!/usr/bin/env python3
"""Render safe, non-executing InternLM-XComposer benchmark plans.

This helper prints checklist-style plans only. It never imports model packages,
never downloads datasets, never calls judge APIs, and never launches benchmark
commands. Optional --check-paths performs simple os.path.exists probes on
user-supplied paths.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Any, Dict, Iterable, List


Workflow = Dict[str, Any]


def gpu_list(count: int) -> str:
    count = max(int(count or 1), 1)
    return ",".join(str(i) for i in range(count))


WORKFLOWS: Dict[str, Workflow] = {
    "vlmevalkit": {
        "title": "Current XComposer / VLMEvalKit route",
        "summary": "Prefer VLMEvalKit for current general visual QA and supported XComposer2/4KHD workflows.",
        "requires": ["VLMEvalKit installation", "model adapter/config", "benchmark data", "CUDA for model execution"],
        "external": ["dataset licenses", "leaderboard submission when the selected data requires it"],
        "data_layout": ["Use VLMEvalKit's dataset cache/layout for the selected benchmark."],
        "commands": [
            "# Pattern only: configure VLMEvalKit model adapter before execution",
            "torchrun --nproc-per-node={gpus} run.py --data <DATASET> --model <XCOMPOSER_MODEL_ADAPTER> --work-dir {output_root}",
        ],
        "outputs": ["VLMEvalKit result directory", "dataset-specific score or submission artifact"],
        "sibling_route": "Use model-inference for custom model loading questions; keep this helper for evaluation planning.",
        "checks": [],
    },
    "xcomposer2-mme": {
        "title": "Legacy XComposer MME",
        "summary": "Plan MME perception/cognition evaluation using official MME images and eval tool.",
        "requires": ["MME_Benchmark_release images", "official eval_tool", "CUDA", "model checkpoint"],
        "external": ["MME data/license", "official eval tool"],
        "data_layout": [
            "<data-root>/MME_Benchmark_release or equivalent image root",
            "<data-root>/eval_tool/Your_Results template files",
            "<output-root>/<model-name>/ task txt files for calculation",
        ],
        "commands": [
            "# Pattern only: run or reimplement the legacy MME inference loop",
            "CUDA_VISIBLE_DEVICES={gpu_list} python <mme_runner>.py --model-path {model_path} --data-root {data_root} --output-root {output_root}",
            "python <official_mme_eval_tool>/calculation.py --results_dir <model-results-dir>",
        ],
        "outputs": ["tab-separated per-task result txt files", "perception and cognition score log"],
        "sibling_route": "Use model-inference if the user needs the model loading/generation implementation.",
        "checks": ["MME_Benchmark_release", "eval_tool"],
    },
    "xcomposer2-mmbench": {
        "title": "Legacy XComposer MMBench / MMBench-CN",
        "summary": "Plan MMBench TSV inference and XLSX submission packaging.",
        "requires": ["official MMBench TSV", "CUDA", "pandas/openpyxl or xlsxwriter", "model checkpoint"],
        "external": ["OpenCompass/MMBench submission server for official score"],
        "data_layout": ["<data-root>/mmbench_dev_20230712.tsv or test TSV", "<output-root>/submit_*.xlsx"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <mmbench_runner>.py --model-path {model_path} --tsv <split.tsv> --output-xlsx {output_root}/submit.xlsx",
            "# Submit XLSX manually only after leaderboard/account approval.",
        ],
        "outputs": ["XLSX with prediction column", "server-side official score after upload"],
        "sibling_route": "Use data-conversion guidance for JSONL-to-XLSX packaging.",
        "checks": [],
    },
    "xcomposer2-seed": {
        "title": "Legacy XComposer SEED-Bench Image",
        "summary": "Plan SEED image multiple-choice evaluation and optional upload packaging.",
        "requires": ["SEED-Bench-image", "SEED-Bench.json", "CUDA", "model checkpoint"],
        "external": ["SEED data/license", "optional leaderboard submission"],
        "data_layout": ["<data-root>/SEED-Bench-image", "<data-root>/SEED-Bench.json", "<output-root>/answers_upload/*.jsonl"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <seed_runner>.py --model-path {model_path} --image-root {data_root}/SEED-Bench-image --annotation {data_root}/SEED-Bench.json --answers {output_root}/seed_answers.jsonl",
            "python <seed_converter>.py --annotation-file {data_root}/SEED-Bench.json --result-file {output_root}/seed_answers.jsonl --result-upload-file {output_root}/answers_upload/seed.jsonl",
        ],
        "outputs": ["local accuracy", "optional upload JSONL"],
        "sibling_route": "Use data-conversion.md for exact/tolerant option-letter handling.",
        "checks": ["SEED-Bench-image", "SEED-Bench.json"],
    },
    "xcomposer2-qbench": {
        "title": "Legacy XComposer QBench / Chinese-QBench",
        "summary": "Plan QBench dev/test inference, formatting, and submission distinction.",
        "requires": ["LLVisionQA JSON", "images_llvisionqa/llv_dev images", "CUDA", "model checkpoint"],
        "external": ["QBench data/license", "test-set submission server/instructions"],
        "data_layout": ["<data-root>/llvisionqa_dev.json", "<data-root>/质衡-问答-验证集.json", "<data-root>/images_llvisionqa or llv_dev"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <qbench_runner>.py --model-path {model_path} --questions <qbench-json> --image-root <qbench-images> --answers {output_root}/qbench_answers.jsonl",
            "python <qbench_formatter>.py --filepath {output_root}/qbench_answers.jsonl",
            "python <qbench_eval>.py --filepath {output_root}/qbench_answers.jsonl  # dev only",
        ],
        "outputs": ["dev score for local dev split", "formatted test artifact for external submission"],
        "sibling_route": "Use troubleshooting.md for non-ASCII Chinese filename issues.",
        "checks": [],
    },
    "xcomposer2-mmmu": {
        "title": "Legacy XComposer MMMU",
        "summary": "Plan MMMU prediction JSON creation and evaluation-only category/domain scoring.",
        "requires": ["MMMU validation data/images", "answer_dict_val.json", "CUDA for prediction"],
        "external": ["MMMU dataset/license"],
        "data_layout": ["<data-root>/MMMU images", "<data-root>/answer_dict_val.json", "<output-root>/mmmu_predictions.json"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <mmmu_prediction_runner>.py --model-path {model_path} --data-root {data_root} --output-path {output_root}/mmmu_predictions.json",
            "python main_eval_only.py --output_path {output_root}/mmmu_predictions.json --answer_path {data_root}/answer_dict_val.json",
        ],
        "outputs": ["prediction JSON", "printed Overall/domain/category accuracies"],
        "sibling_route": "Use model-inference for prediction implementation; evaluation-only parsing can be planned here.",
        "checks": ["answer_dict_val.json"],
    },
    "xcomposer2-mmvet": {
        "title": "Legacy XComposer MM-Vet",
        "summary": "Plan MM-Vet prediction JSON and GPT-based evaluator boundary.",
        "requires": ["mm-vet.json", "images directory", "CUDA for prediction"],
        "external": ["MM-Vet data/license", "GPT/OpenAI judge for final capability scores"],
        "data_layout": ["<data-root>/mm-vet.json", "<data-root>/images", "<output-root>/MMVet_<model>.json"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <mmvet_prediction_runner>.py --model-path {model_path} --data-root {data_root} --output {output_root}/mmvet_answers.json",
            "# Stop here unless GPT judge approval/key/budget are explicitly provided.",
        ],
        "outputs": ["raw answer JSON", "grade JSON/CSV only after external GPT judge"],
        "sibling_route": "Do not call GPT judges from this sub-skill.",
        "checks": ["mm-vet.json", "images"],
    },
    "xcomposer2-pope": {
        "title": "Legacy XComposer POPE",
        "summary": "Plan COCO POPE yes/no hallucination evaluation.",
        "requires": ["COCO POPE adversarial/popular/random JSON", "COCO image root", "CUDA for prediction"],
        "external": ["POPE/COCO data licenses"],
        "data_layout": ["<data-root>/json_files/coco_pope_adversarial.json", "<data-root>/json_files/coco_pope_popular.json", "<data-root>/json_files/coco_pope_random.json"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <pope_runner>.py --model-path {model_path} --data-root {data_root} --output {output_root}/pope_predictions.jsonl",
            "python <pope_metric>.py --predictions {output_root}/pope_predictions.jsonl",
        ],
        "outputs": ["TP/FP/TN/FN", "accuracy/precision/recall/F1/yes ratio"],
        "sibling_route": "Use model-inference for generation implementation if needed.",
        "checks": ["json_files"],
    },
    "xcomposer2-chartqa": {
        "title": "Legacy XComposer ChartQA",
        "summary": "Plan ChartQA human/augmented split evaluation with relaxed numeric accuracy.",
        "requires": ["ChartQA test JSONs", "test/png images", "CUDA for prediction"],
        "external": ["ChartQA dataset/license"],
        "data_layout": ["<data-root>/ChartQA Dataset/test/test_human.json", "<data-root>/ChartQA Dataset/test/test_augmented.json", "<data-root>/ChartQA Dataset/test/png"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <chartqa_runner>.py --model-path {model_path} --data-root {data_root} --output {output_root}/chartqa_predictions.json",
            "python <chartqa_metric>.py --predictions {output_root}/chartqa_predictions.json",
        ],
        "outputs": ["human accuracy", "augmented accuracy", "overall relaxed accuracy"],
        "sibling_route": "Use data-conversion.md for output-shape planning.",
        "checks": [],
    },
    "xcomposer2-ai2d": {
        "title": "Legacy XComposer AI2D",
        "summary": "Plan AI2D multiple-choice evaluation over processed images.",
        "requires": ["ai2d_test.jsonl", "processed AI2D images", "CUDA for prediction"],
        "external": ["AI2D data/license"],
        "data_layout": ["<data-root>/ai2d_test.jsonl", "<data-root>/ai2d images"],
        "commands": ["CUDA_VISIBLE_DEVICES={gpu_list} python <ai2d_runner>.py --model-path {model_path} --questions {data_root}/ai2d_test.jsonl --image-root <ai2d-images> --output {output_root}/ai2d_answers.jsonl"],
        "outputs": ["overall local accuracy"],
        "sibling_route": "Use model-inference for prediction implementation.",
        "checks": ["ai2d_test.jsonl"],
    },
    "xcomposer2-llava-wild": {
        "title": "Legacy XComposer LLaVA-Bench-In-The-Wild",
        "summary": "Plan raw answer generation and GPT judge boundary.",
        "requires": ["questions.jsonl", "images", "answers_gpt4.jsonl", "context.jsonl", "CUDA for prediction"],
        "external": ["dataset/license", "GPT/OpenAI judge for final review scores"],
        "data_layout": ["<data-root>/questions.jsonl", "<data-root>/images", "<data-root>/answers_gpt4.jsonl", "<data-root>/context.jsonl"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} python <llava_wild_runner>.py --model-path {model_path} --data-root {data_root} --answers-file {output_root}/llava_wild_answers.jsonl",
            "# Stop before GPT review unless judge approval/key/budget are provided.",
        ],
        "outputs": ["answer JSONL", "review JSONL and summary only after GPT judge"],
        "sibling_route": "Do not call GPT review from this sub-skill.",
        "checks": ["questions.jsonl", "answers_gpt4.jsonl", "context.jsonl"],
    },
    "omnilive-mlvu": {
        "title": "OmniLive MLVU",
        "summary": "Plan MLVU video benchmark chunking and aggregation for OmniLive.",
        "requires": ["MLVU video folders", "OmniLive base checkpoint", "CUDA", "Decord", "Torch/TorchVision"],
        "external": ["MLVU data/license"],
        "data_layout": ["<video-root>/1_plotQA", "<video-root>/2_needle", "<video-root>/3_ego", "<video-root>/4_count", "<video-root>/5_order", "<video-root>/6_anomaly_reco", "<video-root>/7_topic_reasoning"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} sh benchmarks/mlvu/mlvu.sh {data_root}",
            "# Writes outputs/mlvu/<idx>_of_<chunks>.json, then averages per task.",
        ],
        "outputs": ["per-task mean accuracy", "overall average"],
        "sibling_route": "Use sibling omnilive for model layout and actual video inference setup.",
        "checks": ["1_plotQA", "2_needle", "7_topic_reasoning"],
    },
    "omnilive-video-mme": {
        "title": "OmniLive Video-MME",
        "summary": "Plan Video-MME short/medium/long split benchmark for OmniLive.",
        "requires": ["Video-MME videos", "parquet annotation", "OmniLive base checkpoint", "CUDA", "Decord", "pandas", "pyarrow"],
        "external": ["Video-MME data/license"],
        "data_layout": ["<video-root>/<videoID>.mp4", "annotation parquet available to the benchmark implementation"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} sh benchmarks/video_mme/video_mme.sh {data_root}",
            "# Writes outputs/video_mme/<idx>_of_<chunks>.json, then averages short/medium/long.",
        ],
        "outputs": ["short/medium/long accuracy", "overall average"],
        "sibling_route": "Use sibling omnilive for checkpoint layout and memory/base model troubleshooting.",
        "checks": [],
    },
    "omnilive-streamingbench": {
        "title": "OmniLive StreamingBench",
        "summary": "Plan StreamingBench real-time video benchmark chunking and aggregation.",
        "requires": ["StreamingBench real video folders", "questions JSON", "OmniLive model path", "CUDA"],
        "external": ["StreamingBench data/license"],
        "data_layout": ["<video-root>/real/sample_*/video.mp4", "questions_real.json in the benchmark data implementation"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} sh benchmarks/streamingbench/eval.sh {data_root}",
            "# Verify working directory and GPU mapping before real execution.",
        ],
        "outputs": ["category metrics", "overall StreamingBench score"],
        "sibling_route": "Use sibling omnilive for live streaming/service tasks.",
        "checks": ["real"],
    },
    "omnilive-mvbench": {
        "title": "OmniLive MVBench",
        "summary": "Plan MVBench multi-dataset video benchmark for OmniLive.",
        "requires": ["many MVBench component datasets", "OmniLive base checkpoint", "CUDA", "Decord"],
        "external": ["MVBench component dataset licenses"],
        "data_layout": ["<video-root>/clevrer", "<video-root>/FunQA_test", "<video-root>/star", "<video-root>/ssv2_video", "<video-root>/tvqa", "and other MVBench component roots"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} sh benchmarks/mvbench/mvbench.sh {data_root}",
            "# Writes outputs/mvbench/<idx>_of_<chunks>.json, then averages 20 tasks.",
        ],
        "outputs": ["per-task mean accuracy", "overall average"],
        "sibling_route": "Use sibling omnilive for actual model execution details.",
        "checks": [],
    },
    "omnilive-audio-asr": {
        "title": "OmniLive ASR: WenetSpeech / LibriSpeech",
        "summary": "Plan distributed ASR evaluation and WER aggregation.",
        "requires": ["audio JSONL manifests", "real audio root", "audio checkpoint", "CUDA/NCCL", "ffmpeg", "Qwen2-Audio dependencies"],
        "external": ["WenetSpeech/LibriSpeech data licenses"],
        "data_layout": ["JSONL rows with audio, gt, source", "audio root replacing placeholder paths"],
        "commands": [
            "python -m torch.distributed.launch --use_env --nproc_per_node {gpus} --nnodes 1 evaluate_asr.py --checkpoint {model_path} --dataset <librispeech|wenet_test_meeting|wenet_test_net> --batch-size <batch> --num-workers <workers>",
        ],
        "outputs": ["timestamped result JSON", "WER by source"],
        "sibling_route": "Use sibling omnilive for audio model setup/inference troubleshooting.",
        "checks": [],
    },
    "sharegpt4v-eval": {
        "title": "ShareGPT4V evaluation family",
        "summary": "Plan ShareGPT4V playground-based evaluation across VQAv2, GQA, VizWiz, SQA, TextVQA, MME, MMBench, SEED, LLaVA-Bench, MM-Vet, and QBench.",
        "requires": ["share4v package", "playground archive", "checkpoint", "CUDA", "benchmark-specific data"],
        "external": ["dataset licenses", "EvalAI/OpenCompass/QBench/SEED servers as applicable", "GPT/OpenAI judge for LLaVA-Bench/MM-Vet"],
        "data_layout": ["<project>/playground/data/eval/<benchmark>", "<project>/checkpoints/{checkpoint} unless an explicit checkpoint dir is used"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} bash scripts/sharegpt4v/eval/<benchmark>.sh {checkpoint}",
            "# Pick one benchmark script; do not launch GPT review scripts unless judge approval exists.",
        ],
        "outputs": ["chunk JSONL files", "merge.jsonl", "benchmark-specific upload JSON/XLSX or local score"],
        "sibling_route": "Use model-inference for custom ShareGPT4V generation; keep project eval/converter planning here.",
        "checks": ["playground/data/eval"],
    },
    "sharegpt4v-captioner": {
        "title": "ShareGPT4V ShareCaptioner batch plan",
        "summary": "Plan batch caption generation over a JSON image list without running the model.",
        "requires": ["share4v package", "ShareCaptioner checkpoint", "images-file JSON list", "CUDA"],
        "external": ["model/data license terms"],
        "data_layout": ["images-file: JSON list of image paths", "save-path: captions JSON"],
        "commands": [
            "python tools/share-cap_batch_infer.py --model-name <captioner-checkpoint> --images-file <images.json> --save-path {output_root}/captions.json --batch-size <n> --num_gpus {gpus}",
            "# This is long model inference; do not run from this sub-skill.",
        ],
        "outputs": ["JSON list mapping image path to generated caption"],
        "sibling_route": "Actual caption generation should be treated as model inference with CUDA approval.",
        "checks": [],
    },
    "sharegpt4v-converters": {
        "title": "ShareGPT4V converters",
        "summary": "Plan JSONL-to-submission/result conversion for ShareGPT4V predictions.",
        "requires": ["merged prediction JSONL", "official annotation files", "pandas/openpyxl for XLSX workflows"],
        "external": ["submission server approval for official uploads"],
        "data_layout": ["playground/data/eval/<benchmark>/answers/.../merge.jsonl", "benchmark annotation file", "answers_upload or results output directory"],
        "commands": [
            "python scripts/convert_mmbench_for_submission.py --annotation-file <split.tsv> --result-dir <answers-dir> --upload-dir <upload-dir> --experiment merge",
            "python scripts/convert_seed_for_submission.py --annotation-file <SEED-Bench.json> --result-file <merge.jsonl> --result-upload-file <upload.jsonl>",
            "python scripts/convert_gqa_for_eval.py --src <merge.jsonl> --dst <official_predictions.json>",
        ],
        "outputs": ["XLSX", "upload JSON/JSONL", "official evaluator prediction JSON"],
        "sibling_route": "See data-conversion.md for exact schemas.",
        "checks": [],
    },
    "dualfocus-eval": {
        "title": "DualFocus evaluation family",
        "summary": "Plan DualFocus evaluation on MMBench, SEED, TextVQA, and GQA MCQ.",
        "requires": ["dualfocus package", "DualFocus checkpoint", "Vicuna base model", "CUDA", "benchmark data"],
        "external": ["dataset licenses", "MMBench server for official score"],
        "data_layout": ["playground/data/eval/mmbench", "playground/data/eval/seed_bench", "playground/data/eval/textvqa", "playground/data/eval/gqa"],
        "commands": [
            "CUDA_VISIBLE_DEVICES={gpu_list} bash scripts/eval/eval_mmbench.sh {checkpoint}",
            "CUDA_VISIBLE_DEVICES={gpu_list} bash scripts/eval/eval_seed.sh {checkpoint}",
            "CUDA_VISIBLE_DEVICES={gpu_list} bash scripts/eval/eval_textvqa.sh {checkpoint}",
            "CUDA_VISIBLE_DEVICES={gpu_list} bash scripts/eval/eval_gqa.sh {checkpoint}",
        ],
        "outputs": ["chunk JSONL files", "merge.jsonl", "local score or upload XLSX/JSONL"],
        "sibling_route": "DualFocus training was not released in evidence; do not route training here.",
        "checks": ["playground/data/eval"],
    },
    "dualfocus-converters": {
        "title": "DualFocus converters",
        "summary": "Plan DualFocus MMBench/GQA/SEED result packaging.",
        "requires": ["merged JSONL", "official annotation/eval files", "pandas/openpyxl for MMBench"],
        "external": ["MMBench server or optional SEED leaderboard"],
        "data_layout": ["playground/data/eval/<benchmark>/answers/<ckpt>/merge.jsonl", "answers_upload output directory"],
        "commands": [
            "python scripts/convert_mmbench_for_submission.py --annotation-file <split.tsv> --pred-file <merge.jsonl> --save-file <answers_upload/ckpt.xlsx>",
            "python scripts/convert_gqa_for_eval.py --src <merge.jsonl> --dst <official_predictions.json>",
            "python scripts/convert_seed_for_submission.py --annotation-file <SEED-Bench.json> --result-file <merge.jsonl> --result-upload-file <upload.jsonl>",
        ],
        "outputs": ["XLSX", "official prediction JSON", "upload JSONL"],
        "sibling_route": "See data-conversion.md for schema preflight checks.",
        "checks": [],
    },
}

ALIASES = {
    "mme": "xcomposer2-mme",
    "mmbench": "xcomposer2-mmbench",
    "mmbench-cn": "xcomposer2-mmbench",
    "seed": "xcomposer2-seed",
    "seed-bench": "xcomposer2-seed",
    "qbench": "xcomposer2-qbench",
    "mmmu": "xcomposer2-mmmu",
    "mm-vet": "xcomposer2-mmvet",
    "mmvet": "xcomposer2-mmvet",
    "pope": "xcomposer2-pope",
    "chartqa": "xcomposer2-chartqa",
    "ai2d": "xcomposer2-ai2d",
    "llava-wild": "xcomposer2-llava-wild",
    "mlvu": "omnilive-mlvu",
    "video-mme": "omnilive-video-mme",
    "streamingbench": "omnilive-streamingbench",
    "mvbench": "omnilive-mvbench",
    "asr": "omnilive-audio-asr",
    "audio-asr": "omnilive-audio-asr",
    "sharegpt4v": "sharegpt4v-eval",
    "sharegpt4v-evaluation": "sharegpt4v-eval",
    "sharecaptioner": "sharegpt4v-captioner",
    "captioner": "sharegpt4v-captioner",
    "sharegpt4v-convert": "sharegpt4v-converters",
    "dualfocus": "dualfocus-eval",
    "dualfocus-convert": "dualfocus-converters",
}


def normalize_workflow(value: str) -> str:
    key = (value or "").strip().lower().replace("_", "-")
    key = ALIASES.get(key, key)
    if key not in WORKFLOWS:
        valid = ", ".join(sorted(WORKFLOWS))
        raise SystemExit(f"Unknown workflow '{value}'. Use --list. Valid workflow ids: {valid}")
    return key


def fill(template: str, args: argparse.Namespace) -> str:
    values = {
        "gpus": str(args.gpus),
        "gpu_list": gpu_list(args.gpus),
        "model_path": args.model_path or "<model-path>",
        "data_root": args.data_root or "<data-root>",
        "output_root": args.output_root or "<output-root>",
        "checkpoint": args.checkpoint or "<checkpoint>",
    }
    return template.format(**values)


def bullet(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none recorded"


def path_checks(plan: Workflow, args: argparse.Namespace) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    base_paths = []
    if args.data_root:
        base_paths.append(("data_root", args.data_root))
    if args.model_path:
        base_paths.append(("model_path", args.model_path))
    if args.output_root:
        base_paths.append(("output_root", args.output_root))
    for label, path in base_paths:
        checks.append({"label": label, "path": path, "exists": os.path.exists(path)})
    if args.data_root:
        for rel in plan.get("checks", []):
            path = os.path.join(args.data_root, rel)
            checks.append({"label": f"data_root/{rel}", "path": path, "exists": os.path.exists(path)})
    return checks


def render_markdown(workflow_id: str, plan: Workflow, args: argparse.Namespace) -> str:
    commands = [fill(command, args) for command in plan.get("commands", [])]
    check_rows = path_checks(plan, args) if args.check_paths else []
    parts = [
        f"# Non-Executing Benchmark Plan: {plan['title']}",
        "",
        f"Workflow id: `{workflow_id}`",
        "",
        plan.get("summary", ""),
        "",
        "## Boundaries",
        "",
        "- This helper only renders a plan/checklist.",
        "- It does not download data, load models, submit to servers, call GPT/OpenAI judges, or launch CUDA inference.",
        "- Treat command blocks as patterns to review in a separate approved execution environment.",
        "",
        "## Required Resources",
        "",
        bullet(plan.get("requires", [])),
        "",
        "## External Gates",
        "",
        bullet(plan.get("external", [])),
        "",
        "## Expected Data Layout",
        "",
        bullet(plan.get("data_layout", [])),
        "",
        "## Command Patterns (Not Executed)",
        "",
        "```bash",
        *commands,
        "```",
        "",
        "## Expected Outputs",
        "",
        bullet(plan.get("outputs", [])),
        "",
        "## Routing Note",
        "",
        plan.get("sibling_route", "No sibling route recorded."),
    ]
    if check_rows:
        parts.extend(["", "## Optional Path Probe", ""])
        for row in check_rows:
            status = "ok" if row["exists"] else "missing"
            parts.append(f"- {row['label']}: {status} (`{row['path']}`)")
    return "\n".join(parts).rstrip() + "\n"


def render_json(workflow_id: str, plan: Workflow, args: argparse.Namespace) -> str:
    payload = {
        "workflow_id": workflow_id,
        "title": plan["title"],
        "summary": plan.get("summary", ""),
        "non_executing": True,
        "requires": plan.get("requires", []),
        "external_gates": plan.get("external", []),
        "data_layout": plan.get("data_layout", []),
        "command_patterns": [fill(command, args) for command in plan.get("commands", [])],
        "expected_outputs": plan.get("outputs", []),
        "routing_note": plan.get("sibling_route", ""),
    }
    if args.check_paths:
        payload["path_checks"] = path_checks(plan, args)
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def list_workflows() -> str:
    rows = []
    for key in sorted(WORKFLOWS):
        rows.append(f"{key:24s} {WORKFLOWS[key]['title']}")
    alias_lines = []
    for alias in sorted(ALIASES):
        alias_lines.append(f"{alias:24s} -> {ALIASES[alias]}")
    return (
        "Available workflow ids:\n"
        + "\n".join(rows)
        + "\n\nAliases:\n"
        + "\n".join(alias_lines)
        + "\n"
    )


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a safe non-executing benchmark/project checklist.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              render_benchmark_plan.py --list
              render_benchmark_plan.py --workflow xcomposer2-mme --model-path /models/ixc --data-root /data/mme --output-root /runs/mme --gpus 1
              render_benchmark_plan.py --workflow sharegpt4v-eval --checkpoint share4v-7b --gpus 8 --format json
              render_benchmark_plan.py --workflow omnilive-video-mme --data-root /data/video_mme --gpus 8 --check-paths
            """
        ),
    )
    parser.add_argument("--workflow", "-w", help="Workflow id or alias. Use --list to see options.")
    parser.add_argument("--list", action="store_true", help="List available workflow ids and aliases.")
    parser.add_argument("--model-path", default="", help="Model/checkpoint path placeholder to render into command patterns.")
    parser.add_argument("--checkpoint", default="", help="Project checkpoint name placeholder, e.g. share4v-7b or yhcao/DualFocus-LLaVA-1.5-7B.")
    parser.add_argument("--data-root", default="", help="Dataset root placeholder. With --check-paths this path is probed for existence only.")
    parser.add_argument("--output-root", default="", help="Output root placeholder. With --check-paths this path is probed for existence only.")
    parser.add_argument("--gpus", type=int, default=1, help="GPU count used to render sharding patterns. Default: 1.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    parser.add_argument("--check-paths", action="store_true", help="Safely probe user-supplied paths with os.path.exists; no files are read.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.list:
        sys.stdout.write(list_workflows())
        return 0
    if not args.workflow:
        raise SystemExit("--workflow is required unless --list is used")
    workflow_id = normalize_workflow(args.workflow)
    plan = WORKFLOWS[workflow_id]
    if args.format == "json":
        sys.stdout.write(render_json(workflow_id, plan, args))
    else:
        sys.stdout.write(render_markdown(workflow_id, plan, args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
