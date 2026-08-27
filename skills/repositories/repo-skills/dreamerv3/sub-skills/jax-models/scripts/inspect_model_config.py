#!/usr/bin/env python3
"""Inspect DreamerV3 model/JAX config without constructing the Agent.

The script uses the installed dreamerv3 package by default to locate
configs.yaml. Pass --repo-root only when intentionally inspecting a checkout or
source tree. It parses config catalogs, saved YAML configs, Dreamer-style dotted
and regex overrides, and prints model/JAX summaries plus consistency warnings.
"""

from __future__ import annotations

import argparse
import ast
import copy
import importlib
import json
import pathlib
import re
import sys
from typing import Any, Iterable


REGEX_MARKERS = set("*+?[](){}^$\\|")

# Class-level defaults distilled from dreamerv3.rssm and embodied.jax.heads.
# Config files often omit fields that are supplied by these Ninjax module
# defaults; include them in the summary so omitted-but-active settings are not
# displayed as None.
MODULE_DEFAULTS = {
    "rssm": {
        "deter": 4096,
        "hidden": 2048,
        "stoch": 32,
        "classes": 32,
        "norm": "rms",
        "act": "gelu",
        "unroll": False,
        "unimix": 0.01,
        "outscale": 1.0,
        "imglayers": 2,
        "obslayers": 1,
        "dynlayers": 1,
        "absolute": False,
        "blocks": 8,
        "free_nats": 1.0,
    },
    "encoder": {
        "units": 1024,
        "norm": "rms",
        "act": "gelu",
        "depth": 64,
        "mults": [2, 3, 4, 4],
        "layers": 3,
        "kernel": 5,
        "symlog": True,
        "outer": False,
        "strided": False,
    },
    "decoder": {
        "units": 1024,
        "norm": "rms",
        "act": "gelu",
        "outscale": 1.0,
        "depth": 64,
        "mults": [2, 3, 4, 4],
        "layers": 3,
        "kernel": 5,
        "symlog": True,
        "bspace": 8,
        "outer": False,
        "strided": False,
    },
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        config, meta = resolve_config(args)
    except Exception as exc:  # Keep CLI failures readable.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    summary = build_summary(config, meta)
    warnings = build_warnings(config, meta)

    if args.json:
        print(json.dumps({"summary": summary, "warnings": warnings}, indent=2, sort_keys=True))
    else:
        print_text_summary(summary, warnings)

    if args.warnings_as_errors and warnings:
        return 1
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect DreamerV3 model/JAX configuration without importing JAX "
            "or constructing dreamerv3.agent.Agent."
        )
    )
    parser.add_argument(
        "configs",
        nargs="*",
        help=(
            "Built-in config names to merge in order, for example: "
            "defaults debug size1m. Defaults to 'defaults' when no YAML "
            "config file is supplied."
        ),
    )
    parser.add_argument(
        "--config-file",
        type=pathlib.Path,
        help=(
            "YAML config file. If it contains a top-level 'defaults' entry it "
            "is treated as a DreamerV3 config catalog; otherwise it is treated "
            "as an already-resolved config."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        help=(
            "Optional repository/source root containing dreamerv3/configs.yaml. "
            "By default the installed dreamerv3 package is used."
        ),
    )
    parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Apply an additional dotted or regex override after named configs. "
            "Examples: --set jax.platform=cpu --set agent.dyn.rssm.deter=512"
        ),
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="List available built-in config names from the selected catalog and exit.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit with status 1 when consistency warnings are produced.",
    )
    return parser.parse_args(argv)


def resolve_config(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    source = None
    raw = None

    if args.config_file:
        source = args.config_file.expanduser().resolve()
        raw = load_yaml(source)
    else:
        source = locate_builtin_configs(args.repo_root)
        raw = load_yaml(source)

    if not isinstance(raw, dict):
        raise ValueError(f"YAML root must be a mapping: {source}")

    has_catalog_shape = "defaults" in raw and isinstance(raw.get("defaults"), dict)
    names = list(args.configs)

    if args.list_configs:
        if not has_catalog_shape:
            raise ValueError("--list-configs requires a DreamerV3 config catalog with 'defaults'")
        for name in raw.keys():
            print(name)
        raise SystemExit(0)

    if has_catalog_shape and (names or not args.config_file):
        if not names:
            names = ["defaults"]
        config = {}
        applied_patterns: list[str] = []
        for name in names:
            if name not in raw:
                available = ", ".join(raw.keys())
                raise KeyError(f"unknown config '{name}'. Available: {available}")
            patch = copy.deepcopy(raw[name])
            merge_config(config, patch, applied_patterns=applied_patterns)
    else:
        if names:
            raise ValueError(
                "positional config names require a catalog YAML with top-level 'defaults'; "
                "omit names when --config-file points to a resolved saved config"
            )
        config = copy.deepcopy(raw)
        applied_patterns = []

    for item in args.sets:
        key, value = parse_set(item)
        merge_config(config, {key: value}, applied_patterns=applied_patterns)

    meta = {
        "source": str(source),
        "configs": names or ["<resolved-yaml>"],
        "sets": list(args.sets),
        "applied_patterns": applied_patterns,
        "catalog": has_catalog_shape,
    }
    return config, meta


def locate_builtin_configs(repo_root: pathlib.Path | None) -> pathlib.Path:
    if repo_root:
        path = repo_root.expanduser().resolve() / "dreamerv3" / "configs.yaml"
        if not path.exists():
            raise FileNotFoundError(f"--repo-root does not contain dreamerv3/configs.yaml: {path}")
        return path

    try:
        pkg = importlib.import_module("dreamerv3")
    except Exception as exc:
        cwd_catalog = pathlib.Path.cwd() / "dreamerv3" / "configs.yaml"
        if cwd_catalog.exists():
            return cwd_catalog.resolve()
        raise RuntimeError(
            "Could not import installed package 'dreamerv3'. Install the package "
            "or pass --repo-root pointing at a DreamerV3 source tree."
        ) from exc

    pkg_file = getattr(pkg, "__file__", None)
    if not pkg_file:
        raise RuntimeError("imported dreamerv3 package has no __file__; pass --repo-root")
    path = pathlib.Path(pkg_file).resolve().parent / "configs.yaml"
    if not path.exists():
        raise FileNotFoundError(f"installed dreamerv3 package has no configs.yaml beside __file__: {path}")
    return path


def load_yaml(path: pathlib.Path) -> Any:
    text = path.read_text()
    try:
        from ruamel.yaml import YAML  # type: ignore

        return YAML(typ="safe").load(text)
    except ImportError:
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text)
        except ImportError as exc:
            raise RuntimeError("Install ruamel.yaml or PyYAML to parse DreamerV3 YAML configs") from exc


def parse_set(item: str) -> tuple[str, Any]:
    if "=" not in item:
        raise ValueError(f"--set item must be KEY=VALUE, got: {item!r}")
    key, raw = item.split("=", 1)
    key = key.strip()
    raw = raw.strip()
    if not key:
        raise ValueError(f"empty --set key in {item!r}")
    lowered = raw.lower()
    if lowered == "true":
        value = True
    elif lowered == "false":
        value = False
    elif lowered in {"none", "null"}:
        value = None
    else:
        try:
            value = ast.literal_eval(raw)
        except Exception:
            value = raw
    return key, value


def merge_config(base: dict[str, Any], patch: dict[str, Any], *, applied_patterns: list[str]) -> None:
    for key, value in patch.items():
        if not isinstance(key, str):
            base[key] = copy.deepcopy(value)
            continue
        if is_regex_key(key):
            count = apply_pattern(base, key, value, applied_patterns=applied_patterns)
            if count == 0:
                applied_patterns.append(f"NO_MATCH {key}")
        elif "." in key:
            set_dotted(base, key.split("."), copy.deepcopy(value), applied_patterns=applied_patterns)
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_config(base[key], value, applied_patterns=applied_patterns)
        else:
            base[key] = copy.deepcopy(value)


def is_regex_key(key: str) -> bool:
    return any(ch in key for ch in REGEX_MARKERS)


def iter_nodes(obj: Any, prefix: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield prefix, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                yield from iter_nodes(value, (*prefix, key))


def apply_pattern(base: dict[str, Any], pattern: str, value: Any, *, applied_patterns: list[str]) -> int:
    regex = re.compile(pattern)
    matches = []
    for path, current in list(iter_nodes(base)):
        if not path:
            continue
        dotted = ".".join(path)
        if regex.fullmatch(dotted):
            matches.append((path, current))

    for path, current in matches:
        if isinstance(value, dict) and isinstance(current, dict):
            merge_config(current, copy.deepcopy(value), applied_patterns=applied_patterns)
        else:
            set_path(base, path, copy.deepcopy(value))
    if matches:
        applied_patterns.append(f"{pattern} -> {len(matches)} match(es)")
    return len(matches)


def set_dotted(base: dict[str, Any], parts: list[str], value: Any, *, applied_patterns: list[str]) -> None:
    if len(parts) == 1:
        if isinstance(value, dict) and isinstance(base.get(parts[0]), dict):
            merge_config(base[parts[0]], value, applied_patterns=applied_patterns)
        else:
            base[parts[0]] = value
        return
    target = base
    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]
    leaf = parts[-1]
    if isinstance(value, dict) and isinstance(target.get(leaf), dict):
        merge_config(target[leaf], value, applied_patterns=applied_patterns)
    else:
        target[leaf] = value


def set_path(base: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    target = base
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def get(config: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = config
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_summary(config: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    rssm = with_module_defaults("rssm", get(config, "agent.dyn.rssm", {}))
    enc = with_module_defaults("encoder", get(config, "agent.enc.simple", {}))
    dec = with_module_defaults("decoder", get(config, "agent.dec.simple", {}))
    policy = copy.deepcopy(get(config, "agent.policy", {})) or {}
    rewhead = copy.deepcopy(get(config, "agent.rewhead", {})) or {}
    conhead = copy.deepcopy(get(config, "agent.conhead", {})) or {}
    value = copy.deepcopy(get(config, "agent.value", {})) or {}
    jax_cfg = copy.deepcopy(get(config, "jax", {})) or {}
    loss_scales = copy.deepcopy(get(config, "agent.loss_scales", {})) or {}

    deter = as_int(rssm.get("deter"))
    stoch = as_int(rssm.get("stoch"))
    classes = as_int(rssm.get("classes"))
    feature_dim = deter + stoch * classes if deter and stoch and classes else None

    enc_depths = scaled_depths(enc.get("depth"), enc.get("mults"))
    dec_depths = scaled_depths(dec.get("depth"), dec.get("mults"))

    return {
        "source": meta["source"],
        "configs": meta["configs"],
        "sets": meta["sets"],
        "jax": {
            "platform": jax_cfg.get("platform"),
            "compute_dtype": stringify(jax_cfg.get("compute_dtype")),
            "debug": jax_cfg.get("debug"),
            "jit": jax_cfg.get("jit"),
            "prealloc": jax_cfg.get("prealloc"),
            "mock_devices": jax_cfg.get("mock_devices"),
            "expect_devices": jax_cfg.get("expect_devices"),
            "policy_devices": jax_cfg.get("policy_devices"),
            "train_devices": jax_cfg.get("train_devices"),
            "policy_mesh": jax_cfg.get("policy_mesh", "-1,1,1"),
            "train_mesh": jax_cfg.get("train_mesh", "-1,1,1"),
            "enable_policy": jax_cfg.get("enable_policy"),
        },
        "batching": {
            "batch_size": config.get("batch_size"),
            "batch_length": config.get("batch_length"),
            "report_length": config.get("report_length"),
            "replay_context": config.get("replay_context"),
        },
        "rssm": {
            "typ": get(config, "agent.dyn.typ"),
            "deter": rssm.get("deter"),
            "hidden": rssm.get("hidden"),
            "stoch": rssm.get("stoch"),
            "classes": rssm.get("classes"),
            "feature_dim": feature_dim,
            "blocks": rssm.get("blocks"),
            "free_nats": rssm.get("free_nats"),
            "unimix": rssm.get("unimix"),
            "imglayers": rssm.get("imglayers"),
            "obslayers": rssm.get("obslayers"),
            "dynlayers": rssm.get("dynlayers"),
        },
        "encoder": {
            "typ": get(config, "agent.enc.typ"),
            "layers": enc.get("layers"),
            "units": enc.get("units"),
            "depth": enc.get("depth"),
            "mults": enc.get("mults"),
            "depths": enc_depths,
            "kernel": enc.get("kernel"),
            "symlog": enc.get("symlog"),
            "outer": enc.get("outer"),
            "strided": enc.get("strided"),
        },
        "decoder": {
            "typ": get(config, "agent.dec.typ"),
            "layers": dec.get("layers"),
            "units": dec.get("units"),
            "depth": dec.get("depth"),
            "mults": dec.get("mults"),
            "depths": dec_depths,
            "kernel": dec.get("kernel"),
            "symlog": dec.get("symlog"),
            "bspace": dec.get("bspace"),
            "outer": dec.get("outer"),
            "strided": dec.get("strided"),
        },
        "heads": {
            "reward": head_summary(rewhead),
            "continuation": head_summary(conhead),
            "policy": head_summary(policy),
            "value": head_summary(value),
            "policy_dist_disc": get(config, "agent.policy_dist_disc"),
            "policy_dist_cont": get(config, "agent.policy_dist_cont"),
        },
        "loss_scales": loss_scales,
        "rollout": {
            "imag_last": get(config, "agent.imag_last"),
            "imag_length": get(config, "agent.imag_length"),
            "horizon": get(config, "agent.horizon"),
            "contdisc": get(config, "agent.contdisc"),
            "repval_loss": get(config, "agent.repval_loss"),
            "reward_grad": get(config, "agent.reward_grad"),
            "repval_grad": get(config, "agent.repval_grad"),
        },
        "normalizers": {
            "retnorm": copy.deepcopy(get(config, "agent.retnorm", {})),
            "valnorm": copy.deepcopy(get(config, "agent.valnorm", {})),
            "advnorm": copy.deepcopy(get(config, "agent.advnorm", {})),
        },
        "patterns": meta.get("applied_patterns", []),
    }


def with_module_defaults(name: str, value: Any) -> dict[str, Any]:
    base = copy.deepcopy(MODULE_DEFAULTS[name])
    if isinstance(value, dict):
        base.update(copy.deepcopy(value))
    return base


def scaled_depths(depth: Any, mults: Any) -> list[int] | None:
    try:
        d = int(depth)
        return [d * int(m) for m in list(mults)]
    except Exception:
        return None


def stringify(value: Any) -> Any:
    if hasattr(value, "__name__"):
        return value.__name__
    return value


def head_summary(head: dict[str, Any]) -> dict[str, Any]:
    keys = ["layers", "units", "act", "norm", "output", "bins", "minstd", "maxstd", "unimix", "outscale"]
    return {k: stringify(head.get(k)) for k in keys if k in head}


def build_warnings(config: dict[str, Any], meta: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    platform = str(get(config, "jax.platform", "") or "").lower()
    compute_dtype = str(get(config, "jax.compute_dtype", "") or "").lower()
    debug = bool(get(config, "jax.debug", False))
    jit = bool(get(config, "jax.jit", True))
    prealloc = bool(get(config, "jax.prealloc", False))
    mock_devices = as_int(get(config, "jax.mock_devices", 0))
    expect_devices = as_int(get(config, "jax.expect_devices", 0))
    train_devices = get(config, "jax.train_devices", []) or []
    policy_devices = get(config, "jax.policy_devices", []) or []
    use_shardmap = bool(get(config, "jax.use_shardmap", False))

    deter = as_int(get(config, "agent.dyn.rssm.deter", 0))
    blocks = as_int(get(config, "agent.dyn.rssm.blocks", 0))
    bspace = as_int(get(config, "agent.dec.simple.bspace", 0))
    stoch = as_int(get(config, "agent.dyn.rssm.stoch", 0))
    classes = as_int(get(config, "agent.dyn.rssm.classes", 0))
    hidden = as_int(get(config, "agent.dyn.rssm.hidden", 0))
    batch_size = as_int(config.get("batch_size", 0))
    batch_length = as_int(config.get("batch_length", 0))
    imag_length = as_int(get(config, "agent.imag_length", 0))

    names = [str(x).lower() for x in meta.get("configs", [])]
    set_keys = " ".join(meta.get("sets", []))
    patterns = " ".join(meta.get("applied_patterns", []))

    if platform in {"cuda", "gpu", "tpu"} and debug:
        warnings.append("debug=True on an accelerator can be slow and may hide model assertions; use platform=cpu for narrow debugging.")
    if platform in {"cuda", "gpu"} and not prealloc:
        warnings.append("GPU preallocation is disabled; good for debugging contention, but production throughput/memory behavior may differ.")
    if platform == "cpu" and prealloc:
        warnings.append("prealloc=True is mainly a GPU setting; CPU debug usually uses prealloc=False.")
    if mock_devices and platform not in {"cpu", ""}:
        warnings.append("mock_devices forces host platform device count; use it with platform=cpu in a fresh process.")
    if expect_devices and mock_devices and expect_devices != mock_devices:
        warnings.append("expect_devices differs from mock_devices; the wrapper may alert and wait forever if actual count does not match.")
    if train_devices and mock_devices and max(map(int, train_devices)) >= mock_devices:
        warnings.append("train_devices references an index outside mock_devices host count.")
    if policy_devices and mock_devices and max(map(int, policy_devices)) >= mock_devices:
        warnings.append("policy_devices references an index outside mock_devices host count.")
    if use_shardmap and train_devices and batch_size and batch_size % len(train_devices) != 0:
        warnings.append("use_shardmap=True but batch_size is not divisible by number of train devices.")
    if not jit and batch_size * max(batch_length, 1) > 256:
        warnings.append("jit=False with a non-tiny batch/sequence can be extremely slow; shrink with debug/size1m.")
    if compute_dtype in {"float16", "jnp.float16"}:
        warnings.append("float16 enables optimizer gradient scaling; watch opt/grad_scale and opt/grad_overflow.")
    if compute_dtype in {"bfloat16", "jnp.bfloat16"} and debug:
        warnings.append("bfloat16 debug can obscure small numeric differences; use compute_dtype=float32 for narrow numerical investigations.")

    if deter and blocks and deter % blocks != 0:
        warnings.append("agent.dyn.rssm.deter must be divisible by agent.dyn.rssm.blocks.")
    if deter and bspace and deter % bspace != 0:
        warnings.append("agent.dyn.rssm.deter must be divisible by agent.dec.simple.bspace when bspace is non-zero.")
    if stoch <= 0 or classes <= 0:
        warnings.append("RSSM stoch/classes should be positive.")
    if hidden <= 0:
        warnings.append("RSSM hidden size should be positive.")
    if imag_length <= 0:
        warnings.append("agent.imag_length should be positive for actor/value imagination losses.")

    loss_scales = get(config, "agent.loss_scales", {}) or {}
    required_scale_keys = {"rec", "rew", "con", "dyn", "rep", "policy", "value"}
    missing = sorted(required_scale_keys - set(loss_scales.keys()))
    if missing:
        warnings.append(f"loss_scales is missing common keys: {', '.join(missing)}")
    if get(config, "agent.repval_loss", False) and "repval" not in loss_scales:
        warnings.append("repval_loss=True but loss_scales.repval is missing.")

    size_or_debug = any(name.startswith("size") or name == "debug" for name in names)
    manual_shape = any(token in set_keys for token in ["rssm", "deter", "hidden", "stoch", "classes", "units", "depth", "bins"])
    regex_shape = any(token in patterns for token in ["units", "depth", "bins", "rssm"])
    if size_or_debug or manual_shape or regex_shape:
        warnings.append("model-size/head regex overrides change parameter shapes; old checkpoints are usually incompatible without regex subset loading.")

    return warnings


def print_text_summary(summary: dict[str, Any], warnings: list[str]) -> None:
    print("DreamerV3 model/JAX config summary")
    print("=" * 38)
    print(f"Config source: {summary['source']}")
    print(f"Config names:  {', '.join(map(str, summary['configs']))}")
    if summary["sets"]:
        print(f"Extra --set:   {', '.join(summary['sets'])}")

    section("JAX")
    print_kv(summary["jax"])

    section("Batching")
    print_kv(summary["batching"])

    section("RSSM")
    print_kv(summary["rssm"])

    section("Encoder")
    print_kv(summary["encoder"])

    section("Decoder")
    print_kv(summary["decoder"])

    section("Heads and action distributions")
    heads = summary["heads"]
    for name in ["reward", "continuation", "policy", "value"]:
        print(f"{name:>22}: {compact(heads[name])}")
    print(f"{'policy_dist_disc':>22}: {heads.get('policy_dist_disc')}")
    print(f"{'policy_dist_cont':>22}: {heads.get('policy_dist_cont')}")

    section("Loss scales")
    print_kv(summary["loss_scales"])

    section("Rollout/loss behavior")
    print_kv(summary["rollout"])

    section("Normalizers")
    for key, value in summary["normalizers"].items():
        print(f"{key:>22}: {compact(value)}")

    if summary.get("patterns"):
        section("Applied regex patterns")
        for item in summary["patterns"]:
            print(f"- {item}")

    section("Warnings")
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    else:
        print("No consistency warnings.")


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_kv(mapping: dict[str, Any]) -> None:
    if not mapping:
        print("  <empty>")
        return
    width = max(len(str(k)) for k in mapping.keys())
    for key, value in mapping.items():
        print(f"{str(key):>{width}}: {compact(value)}")


def compact(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {compact(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(compact(v) for v in value) + "]"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
