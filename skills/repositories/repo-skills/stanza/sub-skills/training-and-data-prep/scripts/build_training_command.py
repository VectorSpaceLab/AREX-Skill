#!/usr/bin/env python3
"""Build Stanza training/evaluation command templates without executing them."""

from __future__ import annotations

import argparse
import shlex
from typing import Dict, List

DIRECT_MODULES: Dict[str, str] = {
    "tokenizer": "stanza.models.tokenizer",
    "mwt": "stanza.models.mwt_expander",
    "pos": "stanza.models.tagger",
    "lemma": "stanza.models.lemmatizer",
    "depparse": "stanza.models.parser",
    "ner": "stanza.models.ner_tagger",
    "classifier": "stanza.models.classifier",
    "sentiment": "stanza.models.classifier",
    "constituency": "stanza.models.constituency_parser",
    "charlm": "stanza.models.charlm",
    "langid": "stanza.models.lang_identifier",
    "coref": "stanza.models.wl_coref",
}

WRAPPER_MODULES: Dict[str, str] = {
    "tokenizer": "stanza.utils.training.run_tokenizer",
    "mwt": "stanza.utils.training.run_mwt",
    "pos": "stanza.utils.training.run_pos",
    "lemma": "stanza.utils.training.run_lemma",
    "depparse": "stanza.utils.training.run_depparse",
    "ner": "stanza.utils.training.run_ner",
    "sentiment": "stanza.utils.training.run_sentiment",
    "constituency": "stanza.utils.training.run_constituency",
    "charlm": "stanza.utils.training.run_charlm",
}

MODE_TO_WRAPPER_FLAG = {
    "train": "--train",
    "score-dev": "--score_dev",
    "score-test": "--score_test",
    "score-train": "--score_train",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a Stanza training/evaluation command template without running it.",
    )
    parser.add_argument(
        "task",
        choices=sorted(set(DIRECT_MODULES) | set(WRAPPER_MODULES)),
        help="Model family or wrapper task.",
    )
    parser.add_argument(
        "name",
        help="Treebank, dataset, corpus, or experiment name (for example en_ewt or en_ontonotes).",
    )
    parser.add_argument(
        "--mode",
        choices=["train", "predict", "score-dev", "score-test", "score-train"],
        default="train",
        help="Requested operation. Wrapper score modes map to --score_* flags.",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Use the lower-level model module instead of a stanza.utils.training wrapper when both exist.",
    )
    parser.add_argument("--lang", default=None, help="Language code for direct model commands.")
    parser.add_argument("--save-dir", default=None, help="Explicit model output directory to include.")
    parser.add_argument("--save-name", default=None, help="Explicit model filename to include.")
    parser.add_argument("--cpu", action="store_true", help="Add --cpu when the target module supports device flags.")
    parser.add_argument("--cuda", action="store_true", help="Add --cuda when the target module supports device flags.")
    parser.add_argument("--no-charlm", action="store_true", help="Add wrapper --no_charlm where supported.")
    parser.add_argument("--force", action="store_true", help="Add wrapper --force to retrain existing models.")
    parser.add_argument(
        "--extra",
        nargs=argparse.REMAINDER,
        help="Extra flags to append after a --extra_args delimiter for wrappers or directly for direct modules.",
    )
    return parser


def _append_common(args: argparse.Namespace, cmd: List[str], wrapper: bool) -> None:
    if args.save_dir:
        cmd += ["--save_dir", args.save_dir]
    if args.save_name:
        cmd += ["--save_name", args.save_name]
    if args.cpu:
        cmd.append("--cpu")
    if args.cuda:
        cmd.append("--cuda")
    if args.extra:
        if wrapper:
            cmd.append("--extra_args")
        cmd.extend(args.extra)


def build_command(args: argparse.Namespace) -> List[str]:
    use_wrapper = (not args.direct) and args.task in WRAPPER_MODULES and args.mode != "predict"
    if use_wrapper:
        module = WRAPPER_MODULES[args.task]
        cmd = ["python", "-m", module, args.name]
        cmd.append(MODE_TO_WRAPPER_FLAG[args.mode])
        if args.no_charlm:
            cmd.append("--no_charlm")
        if args.force:
            cmd.append("--force")
        _append_common(args, cmd, wrapper=True)
        return cmd

    module = DIRECT_MODULES[args.task]
    cmd = ["python", "-m", module]
    direct_mode = "predict" if args.mode.startswith("score") else args.mode
    cmd += ["--mode", direct_mode]
    if args.lang:
        cmd += ["--lang", args.lang]
    if args.task not in {"coref"}:
        cmd += ["--shorthand", args.name]
    else:
        cmd.append(args.name)
    if args.no_charlm:
        cmd.append("--no_charlm")
    _append_common(args, cmd, wrapper=False)
    return cmd


def main() -> int:
    args = build_parser().parse_args()
    if args.cpu and args.cuda:
        raise SystemExit("Choose at most one of --cpu and --cuda")
    if args.no_charlm and args.direct:
        # Several direct modules use --charlm/--no_charlm variants inconsistently.
        print("# Review --no_charlm support in the selected direct module before running.")
    cmd = build_command(args)
    print("# Dry-run command template. Review data paths and flags before running.")
    print(" ".join(shlex.quote(piece) for piece in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
