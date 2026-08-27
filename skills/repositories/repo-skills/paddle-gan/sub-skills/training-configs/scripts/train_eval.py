#!/usr/bin/env python3
"""Bundled PaddleGAN training and evaluation runner.

This script mirrors the repo training CLI shape while adding a safe
config-inspection mode:

- `--show-config` / `--check-config` prints the resolved YAML and exits
- dotted overrides are applied as literal values only
- trainer construction is deferred until after inspection mode
"""

from __future__ import annotations

import argparse
import sys
from ast import literal_eval
from pathlib import Path

import yaml


def _bootstrap_project_root() -> None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "ppgan").is_dir():
            root = str(parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            return


_bootstrap_project_root()


class AttrDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            self[key] = value


def create_attr_dict(yaml_config):
    for key, value in yaml_config.items():
        if type(value) is dict:
            yaml_config[key] = value = AttrDict(value)
        if isinstance(value, str):
            try:
                value = literal_eval(value)
            except BaseException:
                pass
        if isinstance(value, AttrDict):
            create_attr_dict(yaml_config[key])
        else:
            yaml_config[key] = value


def parse_config(cfg_file):
    if not Path(cfg_file).exists():
        raise AssertionError(f"config file({cfg_file}) is not exist")
    with open(cfg_file, "r") as fopen:
        yaml_config = AttrDict(yaml.load(fopen, Loader=yaml.SafeLoader))
    create_attr_dict(yaml_config)
    return yaml_config


def cfg2dict(cfg):
    if isinstance(cfg, AttrDict):
        cfg = dict(cfg)
    for k in cfg.keys():
        if isinstance(cfg[k], AttrDict):
            cfg[k] = cfg2dict(cfg[k])
    return cfg


def _coerce_literal(text):
    if not isinstance(text, str):
        return text
    try:
        return literal_eval(text)
    except Exception:
        return text


def _apply_override(target, keys, value):
    if not keys:
        raise ValueError("override path cannot be empty")

    if isinstance(target, list):
        index = _coerce_literal(keys[0])
        if not isinstance(index, int):
            raise TypeError(f"list index must be an integer, got {keys[0]!r}")
        if index < 0 or index >= len(target):
            raise IndexError(f"list index {index} out of range for override path {'.'.join(keys)}")
        if len(keys) == 1:
            target[index] = _coerce_literal(value)
        else:
            _apply_override(target[index], keys[1:], value)
        return

    if not isinstance(target, dict):
        raise TypeError(f"override target must be a dict or list, got {type(target)!r}")

    key = keys[0]
    if key not in target:
        raise KeyError(
            f"override path {'.'.join(keys)!r} does not exist in the loaded config; "
            "edit the YAML or target an existing key"
        )

    if len(keys) == 1:
        target[key] = _coerce_literal(value)
    else:
        _apply_override(target[key], keys[1:], value)


def load_config(config_file, overrides=None):
    cfg = parse_config(config_file)
    if overrides:
        for opt in overrides:
            if not isinstance(opt, str):
                raise TypeError(f"override({opt!r}) should be a string")
            if "=" not in opt:
                raise ValueError(
                    f"override({opt!r}) should contain an '=' to separate key and value"
                )
            key, value = opt.split("=", 1)
            if not key:
                raise ValueError(f"override({opt!r}) has an empty key path")
            _apply_override(cfg, key.split("."), value)
    return cfg


def build_parser():
    parser = argparse.ArgumentParser(description="PaddleGAN training and evaluation runner")
    parser.add_argument("-c", "--config-file", metavar="FILE", help="config file path")
    parser.add_argument(
        "--no-cuda",
        action="store_true",
        default=False,
        help="compatibility flag; backend selection still follows the Paddle build",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="path to a checkpoint with optimizer and epoch state",
    )
    parser.add_argument(
        "--load",
        type=str,
        default=None,
        help="path to weights for fine-tuning or evaluation",
    )
    parser.add_argument(
        "--val-interval",
        type=int,
        default=1,
        help="compatibility flag; use validate.interval in the YAML instead",
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        default=False,
        help="skip training and run test() after initialization",
    )
    parser.add_argument(
        "-o",
        "--opt",
        nargs="+",
        help="set configuration options with dotted key=value pairs",
    )

    # compatibility-only parser fields kept from the source CLI
    parser.add_argument("--source_path", default="", metavar="FILE", help="compatibility placeholder")
    parser.add_argument("--reference_dir", default="", help="compatibility placeholder")
    parser.add_argument("--model_path", default=None, help="compatibility placeholder")

    parser.add_argument(
        "-p",
        "--profiler_options",
        type=str,
        default=None,
        help='profiler options in the form "key1=value1;key2=value2;key3=value3"',
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="fix random numbers by setting a seed",
    )
    parser.add_argument(
        "--amp",
        action="store_true",
        default=False,
        help="whether to enable AMP training",
    )
    parser.add_argument(
        "--amp_level",
        type=str,
        default="O1",
        choices=["O1", "O2"],
        help="AMP level; O2 represents pure fp16",
    )
    parser.add_argument(
        "--show-config",
        "--check-config",
        dest="show_config",
        action="store_true",
        help="print the resolved config and exit without building the trainer",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.config_file:
        parser.error("the -c/--config-file option is required")

    cfg = load_config(args.config_file, args.opt)

    if args.show_config:
        print(yaml.safe_dump(cfg2dict(cfg), sort_keys=False))
        return 0

    from ppgan.engine.trainer import Trainer
    from ppgan.utils.setup import setup

    setup(args, cfg)
    trainer = Trainer(cfg)

    if args.resume:
        trainer.resume(args.resume)
    elif args.load:
        trainer.load(args.load)

    try:
        if args.evaluate_only:
            trainer.test()
        else:
            trainer.train()
    except KeyboardInterrupt:
        if not args.evaluate_only:
            trainer.save(trainer.current_epoch)
    finally:
        trainer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
