#!/usr/bin/env python3
"""Print safe UniLM vision/document command templates without running them."""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence

PLACEHOLDERS = {
    "data": "<DATA_ROOT>",
    "output": "<OUTPUT_DIR>",
    "log": "<LOG_DIR>",
    "checkpoint": "<CHECKPOINT_OR_URL>",
    "spm": "<BEIT3_SENTENCEPIECE_MODEL>",
    "image": "<IMAGE_PATH>",
    "config": "<CONFIG_YAML>",
    "arrow": "<ARROW_ROOT>",
    "trocr_model": "<TROCR_FAIRSEQ_CHECKPOINT>",
}

BEIT3_TASKS = {
    "imagenet": {"input_size": 224, "model": "beit3_base_patch16_224", "lr": "7e-4", "epochs": 50, "batch_size": 128},
    "vqav2": {"input_size": 480, "model": "beit3_base_patch16_480", "lr": "3e-5", "epochs": 10, "batch_size": 16},
    "nlvr2": {"input_size": 224, "model": "beit3_base_patch16_224", "lr": "7e-4", "epochs": 20, "batch_size": 32},
    "coco_captioning": {"input_size": 480, "model": "beit3_base_patch16_480", "lr": "4e-5", "epochs": 10, "batch_size": 32},
    "nocaps": {"input_size": 480, "model": "beit3_base_patch16_480", "lr": "1e-5", "epochs": 10, "batch_size": 32},
    "coco_retrieval": {"input_size": 384, "model": "beit3_base_patch16_384", "lr": "2e-4", "epochs": 15, "batch_size": 192},
    "flickr30k": {"input_size": 384, "model": "beit3_base_patch16_384", "lr": "1e-4", "epochs": 20, "batch_size": 192},
}

VLMO_CONFIGS = (
    "task_finetune_vqa_base_image480",
    "task_finetune_vqa_base_plus_image480",
    "task_finetune_vqa_large_image480",
    "task_finetune_nlvr2_base_image384",
    "task_finetune_nlvr2_base_plus_image384",
    "task_finetune_nlvr2_large_image384",
    "task_finetune_irtr_coco_base_image384",
    "task_finetune_irtr_coco_base_plus_image384",
    "task_finetune_irtr_coco_large_image384",
    "task_finetune_irtr_f30k_base_image384",
    "task_finetune_irtr_f30k_base_plus_image384",
    "task_finetune_irtr_f30k_large_image384",
    "task_textmlm_base",
    "task_mlm_itm_itc_base",
)

DIT_CONFIGS = {
    "publaynet-maskrcnn-base": "publaynet_configs/maskrcnn/maskrcnn_dit_base.yaml",
    "publaynet-maskrcnn-large": "publaynet_configs/maskrcnn/maskrcnn_dit_large.yaml",
    "publaynet-cascade-base": "publaynet_configs/cascade/cascade_dit_base.yaml",
    "publaynet-cascade-large": "publaynet_configs/cascade/cascade_dit_large.yaml",
    "icdar19-maskrcnn-base": "icdar19_configs/maskrcnn/maskrcnn_dit_base.yaml",
    "icdar19-maskrcnn-large": "icdar19_configs/maskrcnn/maskrcnn_dit_large.yaml",
    "icdar19-cascade-base": "icdar19_configs/cascade/cascade_dit_base.yaml",
    "icdar19-cascade-large": "icdar19_configs/cascade/cascade_dit_large.yaml",
    "funsd-text-maskrcnn-base": "configs/mask_rcnn_dit_base.yaml",
}

LANGUAGES = ("zh", "ja", "es", "fr", "it", "de", "pt")


@dataclass
class Plan:
    title: str
    command: list[str]
    notes: list[str]


def quote(value: str) -> str:
    return shlex.quote(str(value))


def format_command(parts: Sequence[str], width: int = 96) -> str:
    lines: list[str] = []
    current = ""
    for part in parts:
        token = quote(part)
        if not current:
            current = token
            continue
        if len(current) + 1 + len(token) > width:
            lines.append(current + " \\")
            current = "  " + token
        else:
            current += " " + token
    if current:
        lines.append(current)
    return "\n".join(lines)


def placeholder(value: str | None, key: str) -> str:
    return value if value else PLACEHOLDERS[key]


def common_notes() -> list[str]:
    return [
        "This script only prints a template; it does not train, evaluate, import native packages, download assets, or read model/data files.",
        "Before running a printed command, confirm the source checkout, dependency stack, dataset, checkpoint/tokenizer, GPU count, and output directory.",
    ]


def beit_classification(args: argparse.Namespace) -> Plan:
    data_path = placeholder(args.data_path, "data")
    output_dir = placeholder(args.output_dir, "output")
    checkpoint = placeholder(args.checkpoint, "checkpoint")
    command = [
        "OMP_NUM_THREADS=1",
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        "run_class_finetuning.py",
        "--model",
        args.model,
        "--data_path",
        data_path,
        "--finetune" if args.mode == "train" else "--resume",
        checkpoint,
        "--output_dir",
        output_dir,
        "--batch_size",
        str(args.batch_size),
        "--lr",
        args.lr,
        "--update_freq",
        str(args.update_freq),
        "--warmup_epochs",
        str(args.warmup_epochs),
        "--epochs",
        str(args.epochs),
        "--layer_decay",
        args.layer_decay,
        "--drop_path",
        args.drop_path,
        "--weight_decay",
        args.weight_decay,
    ]
    if args.input_size:
        command.extend(["--input_size", str(args.input_size)])
    if args.mode == "eval":
        command.append("--eval")
    if args.enable_deepspeed:
        command.append("--enable_deepspeed")
    notes = common_notes() + [
        "BEiT classification expects an ImageFolder-style data root with train/ and val/ class folders.",
        "Effective batch size is gpus * batch_size * update_freq; adjust batch_size and update_freq together for memory limits.",
        "Use BEiT/BEiT v2 segmentation workflows, not this template, for ADE20K semantic segmentation.",
    ]
    return Plan("BEiT image classification", command, notes)


def beit3_task(args: argparse.Namespace) -> Plan:
    defaults = BEIT3_TASKS[args.beit3_task]
    model = args.model or defaults["model"]
    input_size = args.input_size or defaults["input_size"]
    batch_size = args.batch_size or defaults["batch_size"]
    lr = args.lr or defaults["lr"]
    epochs = args.epochs or defaults["epochs"]
    data_path = placeholder(args.data_path, "data")
    output_dir = placeholder(args.output_dir, "output")
    log_dir = args.log_dir or f"{output_dir}/log"
    checkpoint = placeholder(args.checkpoint, "checkpoint")
    sentencepiece_model = placeholder(args.sentencepiece_model, "spm")
    command = [
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        "run_beit3_finetuning.py",
        "--model",
        model,
        "--input_size",
        str(input_size),
        "--task",
        args.beit3_task,
        "--batch_size",
        str(batch_size),
        "--layer_decay",
        args.layer_decay,
        "--lr",
        str(lr),
        "--epochs",
        str(epochs),
        "--warmup_epochs",
        str(args.warmup_epochs),
        "--drop_path",
        args.drop_path,
        "--sentencepiece_model",
        sentencepiece_model,
        "--finetune",
        checkpoint,
        "--data_path",
        data_path,
        "--output_dir",
        output_dir,
        "--log_dir",
        log_dir,
        "--weight_decay",
        args.weight_decay,
        "--seed",
        str(args.seed),
        "--save_ckpt_freq",
        str(args.save_ckpt_freq),
    ]
    if args.mode == "eval":
        command.append("--eval")
    if args.dist_eval:
        command.append("--dist_eval")
    if args.enable_deepspeed:
        command.append("--enable_deepspeed")
    if args.checkpoint_activations:
        command.append("--checkpoint_activations")
    if args.beit3_task == "imagenet" and args.mode == "train":
        command.extend(["--mixup", "0.8", "--cutmix", "1.0"])
    if args.beit3_task in {"vqav2", "coco_captioning", "nocaps"}:
        command.extend(["--num_max_bpe_tokens", str(args.num_max_bpe_tokens)])
    if args.beit3_task in {"coco_captioning", "nocaps"} and args.mode == "train":
        command.extend(["--captioning_mask_prob", args.captioning_mask_prob])
    notes = common_notes() + [
        "BEiT-3 requires a sentencepiece model path for every task, including image classification.",
        "Raw COCO, VQA, NLVR2, and retrieval image folders are not enough; generate the BEiT-3 task index files first.",
        "Use ITC checkpoints for retrieval tasks and indomain checkpoints for VQA/NLVR2 when reproducing the documented recipes.",
    ]
    return Plan(f"BEiT-3 {args.beit3_task}", command, notes)


def layoutlmv3_funsd_cord(args: argparse.Namespace) -> Plan:
    output_dir = placeholder(args.output_dir, "output")
    command = [
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        "--master_port",
        str(args.master_port),
        "examples/run_funsd_cord.py",
        "--dataset_name",
        args.dataset_name,
    ]
    if args.mode == "train":
        command.extend(["--do_train", "--do_eval"])
    else:
        command.append("--do_eval")
    command.extend([
        "--model_name_or_path",
        args.model_name_or_path,
        "--output_dir",
        output_dir,
        "--segment_level_layout",
        "1",
        "--visual_embed",
        "1",
        "--input_size",
        str(args.input_size),
        "--max_steps",
        str(args.max_steps),
        "--save_steps",
        "-1",
        "--evaluation_strategy",
        "steps",
        "--eval_steps",
        str(args.eval_steps),
        "--learning_rate",
        args.learning_rate,
        "--per_device_train_batch_size",
        str(args.batch_size),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--dataloader_num_workers",
        str(args.workers),
    ])
    notes = common_notes() + [
        "FUNSD/CORD examples require words or tokens, labels, bounding boxes, and document images through the dataset loader.",
        "The visual/layout flags are included intentionally: segment_level_layout=1, visual_embed=1, input_size=224 by default.",
        "Use layoutlmv3-xfund for XFUND language JSON files instead of this FUNSD/CORD template.",
    ]
    return Plan(f"LayoutLMv3 {args.dataset_name}", command, notes)


def layoutlmv3_xfund(args: argparse.Namespace) -> Plan:
    data_dir = placeholder(args.data_dir, "data")
    output_dir = placeholder(args.output_dir, "output")
    command = [
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        "--master_port",
        str(args.master_port),
        "examples/run_xfund.py",
        "--data_dir",
        data_dir,
        "--language",
        args.language,
    ]
    if args.mode == "train":
        command.extend(["--do_train", "--do_eval"])
    else:
        command.append("--do_eval")
    command.extend([
        "--model_name_or_path",
        args.model_name_or_path,
        "--output_dir",
        output_dir,
        "--segment_level_layout",
        "1",
        "--visual_embed",
        "1",
        "--input_size",
        str(args.input_size),
        "--max_steps",
        str(args.max_steps),
        "--save_steps",
        "-1",
        "--evaluation_strategy",
        "steps",
        "--eval_steps",
        str(args.eval_steps),
        "--learning_rate",
        args.learning_rate,
        "--per_device_train_batch_size",
        str(args.batch_size),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--dataloader_num_workers",
        str(args.workers),
    ])
    notes = common_notes() + [
        "XFUND data should include language JSON files such as <lang>.train.json and <lang>.val.json plus matching images/.",
        "Use a language-compatible model, such as microsoft/layoutlmv3-base-chinese for Chinese XFUND examples.",
        "For LayoutXLM SER/RE scripts, use the workflow reference instead of this LayoutLMv3 command shape.",
    ]
    return Plan(f"LayoutLMv3 XFUND {args.language}", command, notes)


def dit_detection(args: argparse.Namespace) -> Plan:
    config = args.config or DIT_CONFIGS[args.detector]
    checkpoint = placeholder(args.checkpoint, "checkpoint")
    output_dir = placeholder(args.output_dir, "output")
    if args.mode == "inference":
        command = [
            "python",
            "inference.py",
            "--image_path",
            placeholder(args.image_path, "image"),
            "--output_file_name",
            args.output_file_name,
            "--config",
            config,
            "--opts",
            "MODEL.WEIGHTS",
            checkpoint,
        ]
        title = "DiT detection inference"
    else:
        command = [
            "python",
            "train_net.py",
            "--config-file",
            config,
        ]
        if args.mode == "eval":
            command.append("--eval-only")
        command.extend([
            "--num-gpus",
            str(args.gpus),
            "MODEL.WEIGHTS",
            checkpoint,
            "OUTPUT_DIR",
            output_dir,
        ])
        title = f"DiT detection {args.mode}"
    notes = common_notes() + [
        "The selected detector controls the default config path; override --config only after matching it to the checkpoint.",
        "Detectron2 must match the exact Torch/CUDA/Python stack; do not fix extension errors with broad upgrades.",
        "PubLayNet, ICDAR, and FUNSD text detection require prepared COCO-style data before training or evaluation.",
    ]
    return Plan(title, command, notes)


def trocr_inference(args: argparse.Namespace) -> Plan:
    command = [
        "python",
        "pic_inference.py",
        "--model_path",
        placeholder(args.model_path, "trocr_model"),
        "--image_path",
        placeholder(args.image_path, "image"),
        "--beam",
        str(args.beam),
    ]
    notes = common_notes() + [
        "The inspected native pic_inference.py hardcodes paths; expose these CLI flags in a local adaptation before running this shape.",
        "TrOCR native inference needs fairseq, local user-dir modules, a compatible checkpoint, and a PIL-readable image.",
        "For full-page documents, detect and crop text regions before OCR; TrOCR is not a layout detector.",
    ]
    return Plan("TrOCR single-image inference", command, notes)


def vlmo_run(args: argparse.Namespace) -> Plan:
    config_name = args.vlmo_config
    data_root = placeholder(args.data_root, "arrow")
    log_dir = placeholder(args.log_dir, "output")
    load_path = placeholder(args.load_path, "checkpoint")
    command = [
        "python",
        "run.py",
        "with",
        f"data_root={data_root}",
        f"num_gpus={args.gpus}",
        f"num_nodes={args.nodes}",
        config_name,
        f"per_gpu_batchsize={args.per_gpu_batchsize}",
        f"load_path={load_path}",
        f"log_dir={log_dir}",
    ]
    if args.mode == "eval":
        command.append("test_only=True")
    if args.retrieval_metrics:
        command.append("get_recall_metric=True")
    if args.whole_word_masking:
        command.append("whole_word_masking=True")
    if args.schedule:
        command.append(args.schedule)
    notes = common_notes() + [
        "VLMo uses Sacred syntax: arguments after 'with' are key=value config overrides or named config fragments.",
        "data_root must contain pyarrow files generated from the expected raw dataset layout; raw image folders alone are insufficient.",
        "Append get_recall_metric=True for COCO/Flickr retrieval evaluation.",
    ]
    return Plan(f"VLMo {config_name}", command, notes)


def render(plan: Plan, args: argparse.Namespace) -> str:
    sections = [
        f"# {plan.title}",
        "",
        "Command template:",
        format_command(plan.command),
        "",
        "Notes:",
    ]
    sections.extend(f"- {note}" for note in plan.notes)
    if args.show_cwd_note:
        sections.extend([
            "- Run native commands from the corresponding subproject directory, not from this skill directory.",
        ])
    return "\n".join(sections)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def add_common_path_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-path", help="Dataset root to insert into the template; omitted values use placeholders.")
    parser.add_argument("--checkpoint", help="Checkpoint path or URL to insert into the template; omitted values use placeholders.")
    parser.add_argument("--output-dir", help="Output directory to insert into the template; omitted values use placeholders.")


def add_layout_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("train", "eval"), default="train")
    parser.add_argument("--gpus", type=positive_int, default=8)
    parser.add_argument("--master-port", type=positive_int, default=4398)
    parser.add_argument("--model-name-or-path", default="microsoft/layoutlmv3-base")
    parser.add_argument("--output-dir")
    parser.add_argument("--input-size", type=positive_int, default=224)
    parser.add_argument("--max-steps", type=positive_int, default=1000)
    parser.add_argument("--eval-steps", type=positive_int, default=100)
    parser.add_argument("--learning-rate", default="1e-5")
    parser.add_argument("--batch-size", type=positive_int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=positive_int, default=1)
    parser.add_argument("--workers", type=int, default=8)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build safe command templates for UniLM vision/document AI workflows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--show-cwd-note", action="store_true", help="Add a reminder about running from the native subproject directory.")
    subparsers = parser.add_subparsers(dest="task", required=True)

    beit = subparsers.add_parser("beit-classification", help="BEiT/BEiT v2 image classification fine-tuning or evaluation.")
    beit.set_defaults(builder=beit_classification)
    add_common_path_args(beit)
    beit.add_argument("--mode", choices=("train", "eval"), default="train")
    beit.add_argument("--gpus", type=positive_int, default=8)
    beit.add_argument("--model", default="beit_large_patch16_224")
    beit.add_argument("--input-size", type=positive_int)
    beit.add_argument("--batch-size", type=positive_int, default=32)
    beit.add_argument("--lr", default="2e-5")
    beit.add_argument("--update-freq", type=positive_int, default=2)
    beit.add_argument("--warmup-epochs", type=positive_int, default=5)
    beit.add_argument("--epochs", type=positive_int, default=30)
    beit.add_argument("--layer-decay", default="0.9")
    beit.add_argument("--drop-path", default="0.4")
    beit.add_argument("--weight-decay", default="1e-8")
    beit.add_argument("--enable-deepspeed", action=argparse.BooleanOptionalAction, default=True)

    beit3 = subparsers.add_parser("beit3-task", help="BEiT-3 image or vision-language task.")
    beit3.set_defaults(builder=beit3_task)
    add_common_path_args(beit3)
    beit3.add_argument("--beit3-task", choices=tuple(BEIT3_TASKS), required=True)
    beit3.add_argument("--mode", choices=("train", "eval"), default="train")
    beit3.add_argument("--gpus", type=positive_int, default=8)
    beit3.add_argument("--model")
    beit3.add_argument("--input-size", type=positive_int)
    beit3.add_argument("--batch-size", type=positive_int)
    beit3.add_argument("--lr")
    beit3.add_argument("--epochs", type=positive_int)
    beit3.add_argument("--warmup-epochs", type=positive_int, default=5)
    beit3.add_argument("--layer-decay", default="0.65")
    beit3.add_argument("--drop-path", default="0.2")
    beit3.add_argument("--weight-decay", default="0.05")
    beit3.add_argument("--sentencepiece-model")
    beit3.add_argument("--log-dir")
    beit3.add_argument("--seed", type=int, default=42)
    beit3.add_argument("--save-ckpt-freq", type=positive_int, default=5)
    beit3.add_argument("--dist-eval", action=argparse.BooleanOptionalAction, default=True)
    beit3.add_argument("--enable-deepspeed", action=argparse.BooleanOptionalAction, default=True)
    beit3.add_argument("--checkpoint-activations", action="store_true")
    beit3.add_argument("--num-max-bpe-tokens", type=positive_int, default=32)
    beit3.add_argument("--captioning-mask-prob", default="0.7")

    funsd = subparsers.add_parser("layoutlmv3-funsd-cord", help="LayoutLMv3 FUNSD or CORD token classification.")
    funsd.set_defaults(builder=layoutlmv3_funsd_cord)
    add_layout_common(funsd)
    funsd.add_argument("--dataset-name", choices=("funsd", "cord"), default="funsd")

    xfund = subparsers.add_parser("layoutlmv3-xfund", help="LayoutLMv3 XFUND token classification.")
    xfund.set_defaults(builder=layoutlmv3_xfund)
    add_layout_common(xfund)
    xfund.add_argument("--data-dir")
    xfund.add_argument("--language", choices=LANGUAGES, default="zh")
    xfund.set_defaults(model_name_or_path="microsoft/layoutlmv3-base-chinese", eval_steps=20, learning_rate="7e-5")

    dit = subparsers.add_parser("dit-detection", help="DiT document layout/text/table detection.")
    dit.set_defaults(builder=dit_detection)
    dit.add_argument("--mode", choices=("inference", "eval", "train"), default="eval")
    dit.add_argument("--detector", choices=tuple(DIT_CONFIGS), default="publaynet-maskrcnn-base")
    dit.add_argument("--config", help="Override the default config path for the selected detector.")
    dit.add_argument("--checkpoint")
    dit.add_argument("--image-path")
    dit.add_argument("--output-file-name", default="output.jpg")
    dit.add_argument("--output-dir")
    dit.add_argument("--gpus", type=positive_int, default=8)

    trocr = subparsers.add_parser("trocr-inference", help="TrOCR single-image OCR inference command shape.")
    trocr.set_defaults(builder=trocr_inference)
    trocr.add_argument("--model-path")
    trocr.add_argument("--image-path")
    trocr.add_argument("--beam", type=positive_int, default=5)

    vlmo = subparsers.add_parser("vlmo-run", help="VLMo Sacred-style run.py command.")
    vlmo.set_defaults(builder=vlmo_run)
    vlmo.add_argument("--mode", choices=("train", "eval"), default="train")
    vlmo.add_argument("--vlmo-config", choices=VLMO_CONFIGS, default="task_finetune_vqa_base_image480")
    vlmo.add_argument("--data-root")
    vlmo.add_argument("--load-path")
    vlmo.add_argument("--log-dir")
    vlmo.add_argument("--gpus", type=positive_int, default=8)
    vlmo.add_argument("--nodes", type=positive_int, default=1)
    vlmo.add_argument("--per-gpu-batchsize", type=positive_int, default=16)
    vlmo.add_argument("--retrieval-metrics", action="store_true")
    vlmo.add_argument("--whole-word-masking", action="store_true")
    vlmo.add_argument("--schedule", choices=("step100k", "step200k", "step300k"))

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plan = args.builder(args)
    print(render(plan, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
