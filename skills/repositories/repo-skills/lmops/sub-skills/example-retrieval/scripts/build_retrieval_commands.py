#!/usr/bin/env python3
"""Print safe command templates for LMOps retrieval-family workflows.

This script only prints or checks command concepts. It does not import repository
code, download data, launch training, or start inference.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PLACEHOLDER = {
    "checkout": "<checkout-root>",
    "output": "<output-root>",
    "cache": "<cache-root>",
    "data": "<data-root>",
    "task": "<task-name>",
    "model": "<model-name-or-path>",
    "retriever": "<retriever-checkpoint>",
    "engine": "<openai-engine>",
}


TASKS_BY_PROJECT: Dict[str, Dict[str, List[str]]] = {
    "uprise": {
        "train_clusters": ["train_example_1", "train_example_2"],
        "test_clusters": ["test_example_1", "test_example_2"],
    },
    "se2": {
        "train_clusters": ["copa"],
        "test_clusters": ["copa"],
    },
    "llm-retriever": {
        "tasks": ["all"],
    },
}


def q(value: object) -> str:
    return shlex.quote(str(value))


def env_line(**pairs: object) -> str:
    return " ".join(f"{k}={q(v)}" for k, v in pairs.items())


def header(title: str) -> str:
    return f"# {title}"


def bullet(lines: Sequence[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def maybe_exists(path: str) -> Optional[bool]:
    if not path or path.startswith("<"):
        return None
    return Path(path).expanduser().exists()


def check_paths(label: str, paths: Sequence[Tuple[str, str]]) -> List[str]:
    findings: List[str] = []
    for name, path in paths:
        exists = maybe_exists(path)
        if exists is None:
            findings.append(f"{label}: {name} -> skipped placeholder {path}")
        elif exists:
            findings.append(f"{label}: {name} -> exists")
        else:
            findings.append(f"{label}: {name} -> missing ({path})")
    return findings


def wrap_cmd(cmd: str) -> str:
    return cmd.strip()


def uprise_plan(args: argparse.Namespace) -> List[str]:
    out: List[str] = []
    out.append(header("UPRISE command plan"))
    out.append("Stage order: command generation -> prompt-pool encoding -> retrieval/inference -> optional ablations.")
    out.append("")
    out.append("Command generator template:")
    generator = [
        "python get_cmds.py",
        f"  --output_dir {q(args.output_dir)}",
        f"  --cache_dir {q(args.cache_dir)}",
        f"  --gpus {args.gpus}",
        f"  --train_clusters {q(args.train_clusters)}",
        f"  --test_clusters {q(args.test_clusters)}",
        f"  --scr_model {q(args.scr_model)}",
        f"  --inf_model {q(args.inf_model)}",
        f"  --retriever_prompt_setup {q(args.retriever_prompt_setup)}",
        f"  --ds_size {args.ds_size}",
        f"  --retriever_top_k {args.retriever_top_k}",
        f"  --retriever_bsz {args.retriever_bsz}",
        f"  --retriever_epoch {args.retriever_epoch}",
        f"  --num_prompts {args.num_prompts}",
        f"  --inference_bsz {args.inference_bsz}",
    ]
    if args.multi_task:
        generator.append("  --multi_task")
    if args.retrieve_random:
        generator.append("  --retrieve_random")
    if args.retrieve_bm25:
        generator.append("  --retrieve_bm25")
    if args.retrieve_sbert:
        generator.append("  --retrieve_sbert")
    out.append("\n".join(generator))
    out.append("")
    out.append("Training/inference artifacts expected from the generated scripts:")
    out.append(bullet([
        "train.sh writes sampled-prompt scoring, prompt-pool encoding, and retriever training commands.",
        "inference.sh writes prompt-pool encoding for test-time retrieval plus zero-shot and retrieved-prompt inference.",
        "ablation flags add random, BM25, and SBERT prompt retrieval branches.",
    ]))
    out.append("")
    out.append("Prompt-pool encoding concept:")
    out.append(wrap_cmd(
        "python DPR/generate_dense_embeddings.py model_file=<retriever-checkpoint> ctx_src=dpr_uprise shard_id=0 num_shards=1 "
        "out_file=<experiment-output>/dpr_enc_index ctx_sources.dpr_uprise.prompt_pool_path=<prompt-pool> "
        "ctx_sources.dpr_uprise.prompt_setup_type=qa encoder.cache_dir=<cache-root> hydra.run.dir=<experiment-output>"
    ))
    out.append("")
    out.append("HF and OpenAI inference concepts:")
    out.append(wrap_cmd(f"TASK={q(args.llm_task)} LLM={q(args.inf_model)} bash inference_hf.sh"))
    out.append(wrap_cmd(f"{args.openai_token_var}=<set> ENGINE={q(args.llm_engine)} bash inference_openai.sh"))
    out.append(bullet([
        "The OpenAI path reuses the HF prediction file instead of starting from scratch.",
        "Use the task plan validator before adding a new task or metric class.",
    ]))
    out.append("")
    out.append("Path checks:")
    out.extend(check_paths("UPRISE", [
        ("project root", args.project_root),
        ("output dir", args.output_dir),
        ("cache dir", args.cache_dir),
    ]))
    return out


def se2_plan(args: argparse.Namespace) -> List[str]:
    out: List[str] = []
    out.append(header("SE2 command plan"))
    out.append("Stage order: scoring -> training -> inference, with optional random/BM25/SBERT baselines.")
    out.append("")
    out.append("Command generator template:")
    generator = [
        "python get_cmds.py",
        f"  --output_dir {q(args.output_dir)}",
        f"  --cache_dir {q(args.cache_dir)}",
        f"  --gpus {args.gpus}",
        f"  --score_cmd_name {q(args.score_cmd_name)}",
        f"  --train_cmd_name {q(args.train_cmd_name)}",
        f"  --infer_cmd_name {q(args.infer_cmd_name)}",
        f"  --model_folder {q(args.model_folder)}",
        f"  --train_clusters {q(args.train_clusters)}",
        f"  --test_clusters {q(args.test_clusters)}",
        f"  --scr_model {q(args.scr_model)}",
        f"  --inf_model {q(args.inf_model)}",
        f"  --retriever_prompt_setup {q(args.retriever_prompt_setup)}",
        f"  --infer_prompt_setup {q(args.infer_prompt_setup)}",
        f"  --ds_size {args.ds_size}",
        f"  --retriever_top_k {args.retriever_top_k}",
        f"  --retriever_bsz {args.retriever_bsz}",
        f"  --retriever_epoch {args.retriever_epoch}",
        f"  --beam_size {args.beam_size}",
        f"  --shot_num {args.shot_num}",
        f"  --inference_bsz {args.inference_bsz}",
    ]
    if args.multi_task:
        generator.append("  --multi_task")
    if args.retrieve_random:
        generator.append("  --retrieve_random")
    if args.retrieve_bm25:
        generator.append("  --retrieve_bm25")
    if args.retrieve_sbert:
        generator.append("  --retrieve_sbert")
    out.append("\n".join(generator))
    out.append("")
    out.append("Public shortcuts and caveats:")
    out.append(bullet([
        "You can skip scoring if a compatible scored-data bundle is already staged.",
        "You can skip training if a compatible retriever checkpoint is already staged in the expected model folder.",
        "The public walkthrough notes an eight V100-32GB class setup for a full run.",
        "The scoring stage is multi-step and writes step-1, step-2, and step-3 files before merging them.",
    ]))
    out.append("")
    out.append("Expected stage outputs:")
    out.append(bullet([
        "score.sh builds the prompt pool, samples candidates, scores them, and merges step-wise JSON files.",
        "train.sh trains the SE2 retriever from the merged scored data.",
        "infer.sh encodes the prompt pool, retrieves beam-scored prompts, and runs the downstream LLM inference.",
    ]))
    out.append("")
    out.append("Path checks:")
    out.extend(check_paths("SE2", [
        ("project root", args.project_root),
        ("output dir", args.output_dir),
        ("cache dir", args.cache_dir),
    ]))
    return out


def llm_retriever_plan(args: argparse.Namespace) -> List[str]:
    out: List[str] = []
    out.append(header("LLM Retriever plan"))
    out.append("Stage order: data download -> task formatting -> evaluation or KD/reward training -> iterative search.")
    out.append("")
    out.append("Command concepts:")
    out.append(wrap_cmd("bash scripts/download_data.sh"))
    out.append(wrap_cmd(
        "python misc/format_all_tasks.py --output-dir <data-root> --template-idx 0 --max-train-examples 30000"
    ))
    out.append(wrap_cmd(
        f"OUTPUT_DIR={q(args.output_dir)} DATA_DIR={q(args.data_dir)} bash scripts/eval_retriever.sh {q(args.retriever_model)} {q(args.llm_model)}"
    ))
    out.append(wrap_cmd(
        f"OUTPUT_DIR={q(args.output_dir)} DATA_DIR={q(args.data_dir)} bash scripts/train_kd_biencoder.sh {q(args.retriever_model)}"
    ))
    out.append(wrap_cmd(
        f"DATA_DIR={q(args.data_dir)} bash scripts/gen_llm_score.sh {q(args.llm_model)} <split>"
    ))
    out.append(wrap_cmd(
        f"OUTPUT_DIR={q(args.output_dir)} DATA_DIR={q(args.data_dir)} bash scripts/train_reward.sh"
    ))
    out.append(wrap_cmd(
        f"OUTPUT_DIR={q(args.output_dir)} DATA_DIR={q(args.data_dir)} bash scripts/search_topk.sh {q(args.retriever_model)}"
    ))
    out.append(wrap_cmd(
        f"OUTPUT_DIR={q(args.output_dir)} DATA_DIR={q(args.data_dir)} bash scripts/gen_reward_scores.sh <reward-model> <split>"
    ))
    out.append("")
    out.append("Important configuration fields:")
    out.append(bullet([
        "`model_name_or_path`, `data_dir`, and `train_file` select the model and prepared JSONL bundle.",
        "`do_search`, `do_kd_gen_score`, `do_kd_biencoder`, and `do_llm_eval` switch the execution mode.",
        "`search_topk`, `search_batch_size`, and `kd_gen_score_batch_size` control retrieval and scoring memory use.",
        "`llm_model_name_or_path`, `llm_k_shot`, `llm_max_input_length`, and `llm_max_decode_length` control LLM evaluation.",
        "`topk_as_positive` and `bottomk_as_negative` control how reward scores become positives and negatives.",
    ]))
    out.append("")
    out.append("Data files to verify first:")
    out.append(bullet([
        "`passages.jsonl.gz` contains `id`, `contents`, and `task_name`.",
        "`train.jsonl.gz` and `test.jsonl.gz` contain `query_id`, `query`, `answers`, `options`, and `task_name`.",
        "Derived retrieval outputs add `doc_ids` and `doc_scores`.",
    ]))
    out.append("")
    out.append("Path checks:")
    out.extend(check_paths("LLM Retriever", [
        ("project root", args.project_root),
        ("data dir", args.data_dir),
        ("output dir", args.output_dir),
    ]))
    return out


def selected_plan(args: argparse.Namespace) -> List[str]:
    if args.project == "uprise":
        return uprise_plan(args)
    if args.project == "se2":
        return se2_plan(args)
    if args.project == "llm-retriever":
        return llm_retriever_plan(args)
    raise ValueError(args.project)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print safe retrieval command templates")
    parser.add_argument("--project", choices=["uprise", "se2", "llm-retriever"], required=True)
    parser.add_argument("--project-root", default=PLACEHOLDER["checkout"], help="Repository checkout root or placeholder")
    parser.add_argument("--output-dir", default=PLACEHOLDER["output"], help="Planned output root")
    parser.add_argument("--cache-dir", default=PLACEHOLDER["cache"], help="Planned cache root")
    parser.add_argument("--data-dir", default=PLACEHOLDER["data"], help="Planned data root for LLM Retriever")
    parser.add_argument("--stage", default="all", choices=["all", "train", "eval", "score", "inference", "download", "format", "reward", "kd", "search", "analysis"], help="Filter the printed plan")
    parser.add_argument("--check-paths", action="store_true", help="Check any concrete filesystem paths that were passed")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of formatted text")

    parser.add_argument("--train-clusters", "--train_clusters", dest="train_clusters", default="train_example_1+train_example_2")
    parser.add_argument("--test-clusters", "--test_clusters", dest="test_clusters", default="test_example_1+test_example_2")
    parser.add_argument("--score-cmd-name", "--score_cmd_name", dest="score_cmd_name", default="score.sh")
    parser.add_argument("--train-cmd-name", "--train_cmd_name", dest="train_cmd_name", default="train.sh")
    parser.add_argument("--infer-cmd-name", "--infer_cmd_name", dest="infer_cmd_name", default="infer.sh")
    parser.add_argument("--model-folder", "--model_folder", dest="model_folder", default="model_ckpt")
    parser.add_argument("--retriever-prompt-setup", "--retriever_prompt_setup", dest="retriever_prompt_setup", default="qa")
    parser.add_argument("--infer-prompt-setup", "--infer_prompt_setup", dest="infer_prompt_setup", default="qa")
    parser.add_argument("--ds-size", "--ds_size", dest="ds_size", type=int, default=10000)
    parser.add_argument("--scr-model", "--scr_model", "--score-model", dest="scr_model", default="EleutherAI/gpt-neo-2.7B")
    parser.add_argument("--inf-model", "--inf_model", "--infer-model", dest="inf_model", default="EleutherAI/gpt-neo-2.7B")
    parser.add_argument("--llm-model", dest="llm_model", default="huggyllama/llama-7b")
    parser.add_argument("--retriever-model", dest="retriever_model", default="intfloat/llm-retriever-base")
    parser.add_argument("--num-prompts", "--num_prompts", dest="num_prompts", type=int, default=3)
    parser.add_argument("--beam-size", "--beam_size", dest="beam_size", type=int, default=3)
    parser.add_argument("--shot-num", "--shot_num", dest="shot_num", type=int, default=3)
    parser.add_argument("--retriever-top-k", "--retriever_top_k", dest="retriever_top_k", type=int, default=20)
    parser.add_argument("--retriever-bsz", "--retriever_bsz", dest="retriever_bsz", type=int, default=16)
    parser.add_argument("--retriever-epoch", "--retriever_epoch", dest="retriever_epoch", type=int, default=3)
    parser.add_argument("--inference-bsz", "--inference_bsz", dest="inference_bsz", type=int, default=1)
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--retrieve-random", "--retrieve_random", dest="retrieve_random", action="store_true")
    parser.add_argument("--retrieve-bm25", "--retrieve_bm25", dest="retrieve_bm25", action="store_true")
    parser.add_argument("--retrieve-sbert", "--retrieve_sbert", dest="retrieve_sbert", action="store_true")
    parser.add_argument("--multi-task", "--multi_task", dest="multi_task", action="store_true")
    parser.add_argument("--llm-task", dest="llm_task", default=PLACEHOLDER["task"])
    parser.add_argument("--llm-engine", dest="llm_engine", default=PLACEHOLDER["engine"])
    parser.add_argument("--openai-token-var", dest="openai_token_var", default="OPENAI_TOKEN")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.project == "uprise" and args.stage in {"download", "format", "reward", "kd", "search", "analysis"}:
        # still print the UPRISE planner; stage filtering is handled by the output sections below.
        pass

    if args.json:
        print(json.dumps({
            "project": args.project,
            "stage": args.stage,
            "plan": selected_plan(args),
        }, indent=2, ensure_ascii=False))
        return 0

    plan_lines = [f"Requested stage filter: {args.stage}"] + selected_plan(args)
    print("\n".join(plan_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
