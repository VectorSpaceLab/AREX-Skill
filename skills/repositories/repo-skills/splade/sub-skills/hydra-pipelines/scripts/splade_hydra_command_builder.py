#!/usr/bin/env python3
"""Print safe SPLADE Hydra command templates without executing them."""

import argparse
import shlex
import sys
from typing import Iterable, List, Optional, Sequence, Tuple

DEFAULT_TOY_CONFIG = "config_default.yaml"
DEFAULT_PRETRAINED_CONFIG = "config_splade++_cocondenser_ensembledistil.yaml"
DEFAULT_PRETRAINED_MODEL = "naver/splade-cocondenser-ensembledistil"


def quote(value: object) -> str:
    return shlex.quote(str(value))


def require_non_empty(parser: argparse.ArgumentParser, args: argparse.Namespace, names: Sequence[str]) -> None:
    missing = [name.replace("_", "-") for name in names if not getattr(args, name, None)]
    if missing:
        parser.error("missing required option(s): " + ", ".join("--" + name for name in missing))


def validate_config_source(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Tuple[str, str]:
    config_name = getattr(args, "config_name", None)
    config_fullpath = getattr(args, "config_fullpath", None)
    if config_name and config_fullpath:
        parser.error("use either --config-name or --config-fullpath, not both")
    if config_fullpath:
        return "SPLADE_CONFIG_FULLPATH", config_fullpath
    return "SPLADE_CONFIG_NAME", config_name or DEFAULT_TOY_CONFIG


def env_prefix(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    key, value = validate_config_source(parser, args)
    return f"{key}={quote(value)}"


def override(key: str, value: Optional[object], plus: bool = False) -> Optional[str]:
    if value is None:
        return None
    prefix = "+" if plus else ""
    return f"{prefix}{key}={quote(value)}"


def command(module: str, args: argparse.Namespace, parser: argparse.ArgumentParser, overrides: Iterable[Optional[str]]) -> str:
    parts: List[str] = [env_prefix(args, parser), "python", "-m", module]
    parts.extend(item for item in overrides if item)
    return " ".join(parts)


def print_block(title: str, commands: Sequence[str]) -> None:
    print(f"# {title}")
    for item in commands:
        print(item)
    print()


def add_config_args(parser: argparse.ArgumentParser, default_name: Optional[str] = None) -> None:
    parser.add_argument("--config-name", default=default_name, help="Bundled SPLADE config name, e.g. config_default.yaml")
    parser.add_argument("--config-fullpath", help="Full path to a saved SPLADE config.yaml from a checkpoint directory")


def add_output_args(parser: argparse.ArgumentParser, checkpoint: bool = True, index: bool = True, out: bool = True) -> None:
    if checkpoint:
        parser.add_argument("--checkpoint-dir", help="Value for config.checkpoint_dir")
    if index:
        parser.add_argument("--index-dir", help="Value for config.index_dir")
    if out:
        parser.add_argument("--out-dir", help="Value for config.out_dir")


def add_common_override_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--extra-override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional raw Hydra override; may be repeated",
    )


def common_output_overrides(args: argparse.Namespace) -> List[Optional[str]]:
    return [
        override("config.checkpoint_dir", getattr(args, "checkpoint_dir", None)),
        override("config.index_dir", getattr(args, "index_dir", None)),
        override("config.out_dir", getattr(args, "out_dir", None)),
    ]


def append_extra(args: argparse.Namespace, overrides: List[Optional[str]]) -> List[Optional[str]]:
    return overrides + list(getattr(args, "extra_override", []))


def handle_toy_all(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir", "index_dir", "out_dir"])
    overrides = append_extra(args, common_output_overrides(args))
    print_block("Toy all-in-one SPLADE workflow", [command("splade.all", args, parser, overrides)])


def handle_toy_split(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir", "index_dir", "out_dir"])
    train_overrides = append_extra(
        args,
        [
            override("config.checkpoint_dir", args.checkpoint_dir),
            override("config.index_dir", args.index_dir),
            override("config.out_dir", args.out_dir),
        ],
    )
    index_overrides = append_extra(
        args,
        [
            override("config.checkpoint_dir", args.checkpoint_dir),
            override("config.index_dir", args.index_dir),
        ],
    )
    retrieve_overrides = append_extra(args, common_output_overrides(args))
    evaluate_overrides = append_extra(args, [override("config.out_dir", args.out_dir)])
    print_block(
        "Toy split SPLADE workflow",
        [
            command("splade.train", args, parser, train_overrides),
            command("splade.index", args, parser, index_overrides),
            command("splade.retrieve", args, parser, retrieve_overrides),
            command("splade.evaluate", args, parser, evaluate_overrides),
        ],
    )


def handle_train(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir"])
    overrides = [override("config.checkpoint_dir", args.checkpoint_dir)]
    if args.index_dir:
        overrides.append(override("config.index_dir", args.index_dir))
    if args.out_dir:
        overrides.append(override("config.out_dir", args.out_dir))
    overrides.extend(args.extra_override)
    print_block("SPLADE train command", [command("splade.train", args, parser, overrides)])


def handle_index(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir", "index_dir"])
    overrides = append_extra(
        args,
        [override("config.checkpoint_dir", args.checkpoint_dir), override("config.index_dir", args.index_dir)],
    )
    print_block("SPLADE index command", [command("splade.index", args, parser, overrides)])


def handle_retrieve(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir", "index_dir", "out_dir"])
    overrides = append_extra(args, common_output_overrides(args))
    print_block("SPLADE retrieve/evaluate command", [command("splade.retrieve", args, parser, overrides)])


def handle_flops(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["checkpoint_dir", "index_dir", "out_dir"])
    overrides = append_extra(args, common_output_overrides(args))
    print_block("SPLADE FLOPS command", [command("splade.flops", args, parser, overrides)])


def handle_pretrained(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["model", "index_dir", "out_dir"])
    index_overrides = [
        override("init_dict.model_type_or_dir", args.model),
        override("init_dict.model_type_or_dir_q", args.query_model),
        override("config.pretrained_no_yamlconfig", "true"),
        override("config.index_dir", args.index_dir),
    ]
    retrieve_overrides = index_overrides + [override("config.out_dir", args.out_dir)]
    if args.retrieve_config:
        retrieve_overrides.append(f"retrieve_evaluate={quote(args.retrieve_config)}")
    if args.index_config:
        index_overrides.append(f"index={quote(args.index_config)}")
    index_overrides = append_extra(args, index_overrides)
    retrieve_overrides = append_extra(args, retrieve_overrides)
    print_block(
        "Pretrained Hugging Face index/retrieve workflow",
        [
            command("splade.index", args, parser, index_overrides),
            command("splade.retrieve", args, parser, retrieve_overrides),
        ],
    )


def handle_create_anserini(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    require_non_empty(parser, args, ["index_dir"])
    overrides: List[Optional[str]] = [override("config.index_dir", args.index_dir)]
    if args.checkpoint_dir:
        overrides.append(override("config.checkpoint_dir", args.checkpoint_dir))
    if args.out_dir:
        overrides.append(override("config.out_dir", args.out_dir))
    if args.model:
        overrides.extend(
            [
                override("init_dict.model_type_or_dir", args.model),
                override("init_dict.model_type_or_dir_q", args.query_model),
                override("config.pretrained_no_yamlconfig", "true"),
            ]
        )
    elif not args.config_fullpath and not args.checkpoint_dir:
        parser.error("provide --checkpoint-dir, --config-fullpath, or --model for create-anserini")
    overrides.extend(
        [
            override("quantization_factor_document", args.quantization_factor_document, plus=True),
            override("quantization_factor_query", args.quantization_factor_query, plus=True),
        ]
    )
    overrides = append_extra(args, overrides)
    print_block("SPLADE create_anserini export command", [command("splade.create_anserini", args, parser, overrides)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit safe SPLADE Hydra command templates. The generated commands are printed only; "
            "this helper never launches training, indexing, retrieval, downloads, or evaluation."
        )
    )
    subparsers = parser.add_subparsers(dest="workflow", required=True)

    toy_all = subparsers.add_parser("toy-all", help="Print one toy splade.all command")
    add_config_args(toy_all, DEFAULT_TOY_CONFIG)
    add_output_args(toy_all)
    add_common_override_args(toy_all)
    toy_all.set_defaults(handler=handle_toy_all)

    toy_split = subparsers.add_parser("toy-split", help="Print toy train/index/retrieve/evaluate commands")
    add_config_args(toy_split, DEFAULT_TOY_CONFIG)
    add_output_args(toy_split)
    add_common_override_args(toy_split)
    toy_split.set_defaults(handler=handle_toy_split)

    train = subparsers.add_parser("train", help="Print a classic splade.train command")
    add_config_args(train, DEFAULT_TOY_CONFIG)
    add_output_args(train)
    add_common_override_args(train)
    train.set_defaults(handler=handle_train)

    index = subparsers.add_parser("index", help="Print a classic splade.index command")
    add_config_args(index, DEFAULT_TOY_CONFIG)
    add_output_args(index, checkpoint=True, index=True, out=False)
    add_common_override_args(index)
    index.set_defaults(handler=handle_index)

    retrieve = subparsers.add_parser("retrieve", help="Print a classic splade.retrieve command")
    add_config_args(retrieve, DEFAULT_TOY_CONFIG)
    add_output_args(retrieve)
    add_common_override_args(retrieve)
    retrieve.set_defaults(handler=handle_retrieve)

    flops = subparsers.add_parser("flops", help="Print a classic splade.flops command")
    add_config_args(flops, DEFAULT_TOY_CONFIG)
    add_output_args(flops)
    add_common_override_args(flops)
    flops.set_defaults(handler=handle_flops)

    pretrained = subparsers.add_parser("pretrained", help="Print Hugging Face model index/retrieve commands")
    add_config_args(pretrained, DEFAULT_PRETRAINED_CONFIG)
    pretrained.add_argument("--model", default=DEFAULT_PRETRAINED_MODEL, help="HF model id or local SPLADE model directory")
    pretrained.add_argument("--query-model", help="Optional separate query encoder model id/directory")
    add_output_args(pretrained, checkpoint=False, index=True, out=True)
    pretrained.add_argument("--index-config", help="Optional Hydra index group override, e.g. toy or msmarco")
    pretrained.add_argument("--retrieve-config", help="Optional Hydra retrieve_evaluate group override, e.g. toy or msmarco")
    add_common_override_args(pretrained)
    pretrained.set_defaults(handler=handle_pretrained)

    create_anserini = subparsers.add_parser("create-anserini", help="Print a splade.create_anserini command")
    add_config_args(create_anserini, None)
    create_anserini.add_argument("--model", help="HF model id or local SPLADE model directory; enables pretrained_no_yamlconfig")
    create_anserini.add_argument("--query-model", help="Optional separate query encoder model id/directory")
    add_output_args(create_anserini)
    create_anserini.add_argument("--quantization-factor-document", type=int, default=100)
    create_anserini.add_argument("--quantization-factor-query", type=int, default=100)
    add_common_override_args(create_anserini)
    create_anserini.set_defaults(handler=handle_create_anserini)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.handler(args, parser)
    return 0


if __name__ == "__main__":
    sys.exit(main())
