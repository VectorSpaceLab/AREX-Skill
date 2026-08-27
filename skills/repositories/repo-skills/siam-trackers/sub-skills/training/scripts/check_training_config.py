#!/usr/bin/env python3
"""Read-only NanoTrack training configuration preflight.

This script does not import NanoTrack, load checkpoints, mutate data, or start
training. It accepts a YAML file in the conservative subset used by NanoTrack,
or a JSON mapping, merges it over bundled defaults, and checks static launch
gates. Exit 0 means no static errors; it is not proof that training will run.
"""

import argparse
import ast
import json
import math
import os
import re
import sys
from pathlib import Path


class ConfigError(ValueError):
    pass


DEFAULTS = {
    "META_ARC": "",
    "CUDA": True,
    "TRAIN": {
        "NEG_NUM": 16,
        "POS_NUM": 16,
        "TOTAL_NUM": 64,
        "EXEMPLAR_SIZE": 127,
        "SEARCH_SIZE": 255,
        "BASE_SIZE": 8,
        "OUTPUT_SIZE": 25,
        "RESUME": "",
        "PRETRAINED": "",
        "LOG_DIR": "./logs",
        "SNAPSHOT_DIR": "./snapshot",
        "EPOCH": 20,
        "START_EPOCH": 0,
        "NUM_CONVS": 4,
        "BATCH_SIZE": 32,
        "NUM_WORKERS": 8,
        "MOMENTUM": 0.9,
        "WEIGHT_DECAY": 0.0001,
        "CLS_WEIGHT": 1.0,
        "LOC_WEIGHT": 1.0,
        "PRINT_FREQ": 20,
        "LOG_GRADS": False,
        "GRAD_CLIP": 10.0,
        "BASE_LR": 0.005,
        "LR": {"TYPE": "log", "KWARGS": {}},
        "LR_WARMUP": {
            "WARMUP": True,
            "TYPE": "step",
            "EPOCH": 5,
            "KWARGS": {},
        },
    },
    "MASK": {"MASK": False},
    "DATASET": {
        "TEMPLATE": {
            "SHIFT": 4,
            "SCALE": 0.05,
            "BLUR": 0.0,
            "FLIP": 0.0,
            "COLOR": 1.0,
        },
        "SEARCH": {
            "SHIFT": 64,
            "SCALE": 0.18,
            "BLUR": 0.0,
            "FLIP": 0.0,
            "COLOR": 1.0,
        },
        "NEG": 0.2,
        "GRAY": 0.0,
        "NAMES": ["VID", "YOUTUBEBB", "DET", "COCO", "GOT", "LASOT"],
        "VID": {"ROOT": "", "ANNO": "", "FRAME_RANGE": 100, "NUM_USE": 100000},
        "YOUTUBEBB": {"ROOT": "", "ANNO": "", "FRAME_RANGE": 3, "NUM_USE": 100000},
        "DET": {"ROOT": "", "ANNO": "", "FRAME_RANGE": 1, "NUM_USE": 100000},
        "COCO": {"ROOT": "", "ANNO": "", "FRAME_RANGE": 1, "NUM_USE": 100000},
        "GOT": {
            "ROOT": "data/GOT-10k/crop511",
            "ANNO": "data/GOT-10k/train.json",
            "FRAME_RANGE": 100,
            "NUM_USE": 100000,
        },
        "LASOT": {"ROOT": "", "ANNO": "", "FRAME_RANGE": 100, "NUM_USE": 100000},
        "VIDEOS_PER_EPOCH": 600000,
    },
    "BACKBONE": {
        "TYPE": "res50",
        "KWARGS": {},
        "PRETRAINED": "",
        "TRAIN_LAYERS": [],
        "LAYERS_LR": 0.1,
        "TRAIN_EPOCH": 10,
    },
    "ADJUST": {"ADJUST": True, "KWARGS": {}, "TYPE": "AdjustAllLayer"},
    "BAN": {"BAN": False, "TYPE": "MultiBAN", "KWARGS": {}},
    "POINT": {"STRIDE": 8},
    "TRACK": {
        "TYPE": "NanoTracker",
        "PENALTY_K": 0.16,
        "WINDOW_INFLUENCE": 0.46,
        "LR": 0.34,
        "EXEMPLAR_SIZE": 127,
        "INSTANCE_SIZE": 255,
        "BASE_SIZE": 8,
        "OUTPUT_SIZE": 16,
        "CONTEXT_AMOUNT": 0.5,
    },
}

TOP_LEVEL_KEYS = set(DEFAULTS)
SECTION_KEYS = {
    "TRAIN": set(DEFAULTS["TRAIN"]),
    "BACKBONE": set(DEFAULTS["BACKBONE"]),
    "ADJUST": set(DEFAULTS["ADJUST"]),
    "BAN": set(DEFAULTS["BAN"]),
    "POINT": set(DEFAULTS["POINT"]),
}
LR_TYPES = {"log", "step", "multi-step", "linear", "cos"}
KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def strip_yaml_comment(line):
    """Strip # comments while preserving hashes inside quoted strings."""
    quote = None
    escaped = False
    out = []
    for char in line:
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            out.append(char)
            escaped = True
            continue
        if quote:
            out.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            out.append(char)
        elif char == "#":
            break
        else:
            out.append(char)
    if quote:
        raise ConfigError("unterminated quoted string")
    return "".join(out).rstrip()


def parse_scalar(text, line_no=None):
    text = text.strip()
    where = " on line {}".format(line_no) if line_no else ""
    if not text:
        raise ConfigError("empty scalar{}".format(where))
    if text.startswith(("&", "*", "!", "|", ">")):
        raise ConfigError("unsupported YAML feature{}: {!r}".format(where, text))
    lowered = text.lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    if lowered in ("null", "~"):
        return None
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        pass
    # Plain YAML scalars in these configs are identifiers/paths.
    if text.startswith(("[", "{", "(", "'", '"')):
        raise ConfigError("invalid inline scalar{}: {!r}".format(where, text))
    return text


def tokenize_simple_yaml(text):
    tokens = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ConfigError("tabs are not allowed for indentation on line {}".format(line_no))
        cleaned = strip_yaml_comment(raw)
        if not cleaned.strip() or cleaned.strip() in ("---", "..."):
            continue
        if cleaned.lstrip().startswith("%"):
            raise ConfigError("YAML directives are not supported on line {}".format(line_no))
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        tokens.append((indent, cleaned.strip(), line_no))
    return tokens


def split_mapping_entry(content, line_no):
    if ":" not in content:
        raise ConfigError("expected KEY: VALUE on line {}".format(line_no))
    key, value = content.split(":", 1)
    key = key.strip()
    if not key or not KEY_RE.match(key):
        raise ConfigError("unsupported mapping key on line {}: {!r}".format(line_no, key))
    return key, value.strip()


def parse_yaml_block(tokens, index, indent):
    if index >= len(tokens):
        raise ConfigError("expected an indented value at end of file")
    if tokens[index][0] != indent:
        raise ConfigError(
            "unexpected indentation on line {} (expected {}, got {})".format(
                tokens[index][2], indent, tokens[index][0]
            )
        )
    is_list = tokens[index][1] == "-" or tokens[index][1].startswith("- ")
    container = [] if is_list else {}

    while index < len(tokens):
        current_indent, content, line_no = tokens[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ConfigError("unexpected indentation on line {}".format(line_no))
        current_is_list = content == "-" or content.startswith("- ")
        if current_is_list != is_list:
            break

        if is_list:
            payload = content[1:].strip()
            if payload:
                container.append(parse_scalar(payload, line_no))
                index += 1
            else:
                index += 1
                if index >= len(tokens) or tokens[index][0] <= indent:
                    raise ConfigError("empty list item on line {}".format(line_no))
                child_indent = tokens[index][0]
                child, index = parse_yaml_block(tokens, index, child_indent)
                container.append(child)
            continue

        key, payload = split_mapping_entry(content, line_no)
        if key in container:
            raise ConfigError("duplicate key {!r} on line {}".format(key, line_no))
        index += 1
        if payload:
            container[key] = parse_scalar(payload, line_no)
            continue
        if index >= len(tokens) or tokens[index][0] < indent:
            container[key] = {}
            continue
        # NanoTrack YAML uses both ordinary indented children and the valid
        # "indentless sequence" form where list dashes align with the key.
        next_indent, next_content, _ = tokens[index]
        if next_indent == indent and (next_content == "-" or next_content.startswith("- ")):
            child, index = parse_yaml_block(tokens, index, indent)
            container[key] = child
        elif next_indent > indent:
            child, index = parse_yaml_block(tokens, index, next_indent)
            container[key] = child
        else:
            container[key] = {}
    return container, index


def simple_yaml_load(text):
    """Load the conservative mapping/list/scalar subset used by bundled configs."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        tokens = tokenize_simple_yaml(text)
        if not tokens:
            raise ConfigError("configuration is empty")
        if tokens[0][0] != 0:
            raise ConfigError("top-level YAML must start at indentation 0")
        parsed, index = parse_yaml_block(tokens, 0, 0)
        if index != len(tokens):
            _, _, line_no = tokens[index]
            raise ConfigError("could not parse YAML near line {}".format(line_no))
    if not isinstance(parsed, dict):
        raise ConfigError("top-level configuration must be a mapping")
    return parsed


def deep_copy(value):
    if isinstance(value, dict):
        return {key: deep_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return [deep_copy(item) for item in value]
    return value


def deep_merge(base, override):
    if not isinstance(override, dict):
        return deep_copy(override)
    result = deep_copy(base) if isinstance(base, dict) else {}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deep_copy(value)
    return result


def set_dotted(mapping, assignment):
    if "=" not in assignment:
        raise ConfigError("--set expects DOTTED.KEY=VALUE: {!r}".format(assignment))
    dotted, raw_value = assignment.split("=", 1)
    keys = [part.strip() for part in dotted.split(".")]
    if not keys or any(not key or not KEY_RE.match(key) for key in keys):
        raise ConfigError("invalid dotted key: {!r}".format(dotted))
    cursor = mapping
    for key in keys[:-1]:
        existing = cursor.get(key)
        if existing is None:
            existing = {}
            cursor[key] = existing
        if not isinstance(existing, dict):
            raise ConfigError("cannot set child of non-mapping key: {!r}".format(key))
        cursor = existing
    cursor[keys[-1]] = parse_scalar(raw_value)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def path_get(mapping, dotted, default=None):
    current = mapping
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def require_mapping(config, key, errors):
    value = config.get(key)
    if not isinstance(value, dict):
        errors.append("{} must be a mapping".format(key))
        return {}
    return value


def require_bool(mapping, key, label, errors):
    value = mapping.get(key)
    if not isinstance(value, bool):
        errors.append("{} must be true or false".format(label))
        return None
    return value


def require_number(mapping, key, label, errors, minimum=None, strict_min=False):
    value = mapping.get(key)
    if not is_number(value):
        errors.append("{} must be a finite number".format(label))
        return None
    if minimum is not None:
        bad = value <= minimum if strict_min else value < minimum
        if bad:
            op = ">" if strict_min else ">="
            errors.append("{} must be {} {}".format(label, op, minimum))
    return value


def require_int(mapping, key, label, errors, minimum=None, strict_min=False):
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append("{} must be an integer".format(label))
        return None
    if minimum is not None:
        bad = value <= minimum if strict_min else value < minimum
        if bad:
            op = ">" if strict_min else ">="
            errors.append("{} must be {} {}".format(label, op, minimum))
    return value


def resolve_project_path(project_root, raw):
    candidate = Path(os.path.expanduser(raw))
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve(strict=False)


def warn_unknown_keys(raw, warnings):
    for key in raw:
        if key not in TOP_LEVEL_KEYS:
            warnings.append("unknown top-level key {!r}; the runtime may reject it".format(key))
    for section, known in SECTION_KEYS.items():
        raw_section = raw.get(section)
        if isinstance(raw_section, dict):
            for key in raw_section:
                if key not in known:
                    warnings.append(
                        "unknown key {}.{}; check spelling and runtime support".format(section, key)
                    )


def validate(config, raw, args):
    errors = []
    warnings = []
    notes = []
    warn_unknown_keys(raw, warnings)

    train = require_mapping(config, "TRAIN", errors)
    dataset = require_mapping(config, "DATASET", errors)
    backbone = require_mapping(config, "BACKBONE", errors)
    adjust = require_mapping(config, "ADJUST", errors)
    ban = require_mapping(config, "BAN", errors)
    point = require_mapping(config, "POINT", errors)

    cuda_flag = config.get("CUDA")
    if not isinstance(cuda_flag, bool):
        errors.append("CUDA must be true or false")
    elif not cuda_flag:
        errors.append("CUDA=false cannot enable CPU training; stock training calls .cuda() unconditionally")

    ban_enabled = require_bool(ban, "BAN", "BAN.BAN", errors)
    if ban_enabled is False:
        errors.append("BAN.BAN must be true: the stock loader/model training path requires BANDataset and ban_head")
    if ban_enabled:
        if not isinstance(ban.get("TYPE"), str) or not ban.get("TYPE").strip():
            errors.append("BAN.TYPE must be a non-empty string")
        if not isinstance(ban.get("KWARGS"), dict):
            errors.append("BAN.KWARGS must be a mapping")

    adjust_enabled = require_bool(adjust, "ADJUST", "ADJUST.ADJUST", errors)
    if adjust_enabled:
        if not isinstance(adjust.get("TYPE"), str) or not adjust.get("TYPE").strip():
            errors.append("ADJUST.TYPE must be a non-empty string when enabled")
        if not isinstance(adjust.get("KWARGS"), dict):
            errors.append("ADJUST.KWARGS must be a mapping")

    if not isinstance(backbone.get("TYPE"), str) or not backbone.get("TYPE").strip():
        errors.append("BACKBONE.TYPE must be a non-empty string")
    if not isinstance(backbone.get("KWARGS"), dict):
        errors.append("BACKBONE.KWARGS must be a mapping")
    layers = backbone.get("TRAIN_LAYERS")
    if not isinstance(layers, (list, tuple)) or any(not isinstance(x, str) or not x for x in layers):
        errors.append("BACKBONE.TRAIN_LAYERS must be a list of non-empty layer names")
        layers = []

    epoch = require_int(train, "EPOCH", "TRAIN.EPOCH", errors, 0, strict_min=True)
    start_epoch = require_int(train, "START_EPOCH", "TRAIN.START_EPOCH", errors, 0)
    batch = require_int(train, "BATCH_SIZE", "TRAIN.BATCH_SIZE", errors, 0, strict_min=True)
    workers = require_int(train, "NUM_WORKERS", "TRAIN.NUM_WORKERS", errors, 0)
    exemplar = require_int(train, "EXEMPLAR_SIZE", "TRAIN.EXEMPLAR_SIZE", errors, 0, strict_min=True)
    search = require_int(train, "SEARCH_SIZE", "TRAIN.SEARCH_SIZE", errors, 0, strict_min=True)
    output = require_int(train, "OUTPUT_SIZE", "TRAIN.OUTPUT_SIZE", errors, 0, strict_min=True)
    base_size = require_int(train, "BASE_SIZE", "TRAIN.BASE_SIZE", errors, 0)
    stride = require_int(point, "STRIDE", "POINT.STRIDE", errors, 0, strict_min=True)
    train_epoch = require_int(backbone, "TRAIN_EPOCH", "BACKBONE.TRAIN_EPOCH", errors, 0)

    if epoch is not None and start_epoch is not None and start_epoch >= epoch:
        errors.append("TRAIN.START_EPOCH must be less than TRAIN.EPOCH")
    if epoch is not None and train_epoch is not None and train_epoch > epoch:
        warnings.append("BACKBONE.TRAIN_EPOCH is after training ends; backbone will remain frozen")
    if epoch is not None and train_epoch is not None and train_epoch < epoch and not layers:
        warnings.append("BACKBONE.TRAIN_LAYERS is empty; transition epoch will unfreeze no named layers")
    if exemplar is not None and exemplar % 2 == 0:
        warnings.append("TRAIN.EXEMPLAR_SIZE is even; maintained crop geometry uses an odd side")
    if search is not None and search % 2 == 0:
        warnings.append("TRAIN.SEARCH_SIZE is even; maintained crop geometry uses an odd side")
    if search is not None and exemplar is not None and search <= exemplar:
        errors.append("TRAIN.SEARCH_SIZE must be greater than TRAIN.EXEMPLAR_SIZE")
    if None not in (search, exemplar, output, base_size, stride):
        numerator = search - exemplar
        if numerator % stride == 0:
            heuristic = numerator // stride + 1 + base_size
            if heuristic != output:
                warnings.append(
                    "training geometry heuristic gives OUTPUT_SIZE={} but config uses {}; "
                    "this is intentional only for a matched architecture such as V3".format(
                        heuristic, output
                    )
                )
        else:
            warnings.append(
                "SEARCH_SIZE - EXEMPLAR_SIZE is not divisible by POINT.STRIDE; prove model output geometry"
            )

    pos = require_int(train, "POS_NUM", "TRAIN.POS_NUM", errors, 0)
    neg_num = require_int(train, "NEG_NUM", "TRAIN.NEG_NUM", errors, 0)
    total = require_int(train, "TOTAL_NUM", "TRAIN.TOTAL_NUM", errors, 0, strict_min=True)
    if pos is not None and total is not None and pos > total:
        errors.append("TRAIN.POS_NUM cannot exceed TRAIN.TOTAL_NUM")
    if neg_num == 0:
        warnings.append("TRAIN.NEG_NUM=0 gives explicit negative pairs no selected negative labels")

    for key in ("BASE_LR", "GRAD_CLIP"):
        require_number(train, key, "TRAIN." + key, errors, 0, strict_min=True)
    require_number(train, "WEIGHT_DECAY", "TRAIN.WEIGHT_DECAY", errors, 0)
    momentum = require_number(train, "MOMENTUM", "TRAIN.MOMENTUM", errors, 0)
    if momentum is not None and momentum >= 1.0:
        warnings.append("TRAIN.MOMENTUM is >= 1.0; verify this is intentional")
    cls_weight = require_number(train, "CLS_WEIGHT", "TRAIN.CLS_WEIGHT", errors, 0)
    loc_weight = require_number(train, "LOC_WEIGHT", "TRAIN.LOC_WEIGHT", errors, 0)
    if cls_weight == 0 and loc_weight == 0:
        errors.append("TRAIN.CLS_WEIGHT and TRAIN.LOC_WEIGHT cannot both be zero")
    require_int(train, "PRINT_FREQ", "TRAIN.PRINT_FREQ", errors, 0, strict_min=True)
    require_bool(train, "LOG_GRADS", "TRAIN.LOG_GRADS", errors)

    lr = train.get("LR")
    if not isinstance(lr, dict):
        errors.append("TRAIN.LR must be a mapping")
    else:
        lr_type = lr.get("TYPE")
        if lr_type not in LR_TYPES:
            errors.append("TRAIN.LR.TYPE must be one of {}".format(sorted(LR_TYPES)))
        if not isinstance(lr.get("KWARGS"), dict):
            errors.append("TRAIN.LR.KWARGS must be a mapping")
        else:
            validate_lr_kwargs(lr_type, lr["KWARGS"], "TRAIN.LR.KWARGS", errors, warnings)

    warm = train.get("LR_WARMUP")
    if not isinstance(warm, dict):
        errors.append("TRAIN.LR_WARMUP must be a mapping")
    else:
        warm_enabled = require_bool(warm, "WARMUP", "TRAIN.LR_WARMUP.WARMUP", errors)
        warm_epoch = require_int(warm, "EPOCH", "TRAIN.LR_WARMUP.EPOCH", errors, 0)
        warm_type = warm.get("TYPE")
        if warm_type not in LR_TYPES:
            errors.append("TRAIN.LR_WARMUP.TYPE must be one of {}".format(sorted(LR_TYPES)))
        kwargs = warm.get("KWARGS")
        if not isinstance(kwargs, dict):
            errors.append("TRAIN.LR_WARMUP.KWARGS must be a mapping")
        else:
            validate_lr_kwargs(warm_type, kwargs, "TRAIN.LR_WARMUP.KWARGS", errors, warnings)
        if warm_enabled and None not in (epoch, warm_epoch) and warm_epoch >= epoch:
            errors.append("warmup epoch must be less than TRAIN.EPOCH")

    names = dataset.get("NAMES")
    if not isinstance(names, (list, tuple)) or not names:
        errors.append("DATASET.NAMES must be a non-empty list")
        names = []
    elif any(not isinstance(name, str) or not name.strip() for name in names):
        errors.append("DATASET.NAMES entries must be non-empty strings")
        names = []
    elif len(set(names)) != len(names):
        errors.append("DATASET.NAMES must not contain duplicates")

    for key in ("NEG", "GRAY"):
        value = require_number(dataset, key, "DATASET." + key, errors, 0)
        if value is not None and value > 1:
            errors.append("DATASET.{} must be <= 1".format(key))
    for aug_name in ("TEMPLATE", "SEARCH"):
        aug = dataset.get(aug_name)
        if not isinstance(aug, dict):
            errors.append("DATASET.{} must be a mapping".format(aug_name))
            continue
        for key in ("SHIFT", "SCALE"):
            require_number(aug, key, "DATASET.{}.{}".format(aug_name, key), errors, 0)
        for key in ("BLUR", "FLIP", "COLOR"):
            value = require_number(aug, key, "DATASET.{}.{}".format(aug_name, key), errors, 0)
            if value is not None and value > 1:
                errors.append("DATASET.{}.{} must be <= 1".format(aug_name, key))

    videos = require_int(dataset, "VIDEOS_PER_EPOCH", "DATASET.VIDEOS_PER_EPOCH", errors, 0)
    usable_total = 0
    unknown_total = False
    active_records = []
    for name in names:
        record = dataset.get(name)
        label = "DATASET.{}".format(name)
        if not isinstance(record, dict):
            errors.append("{} must be a mapping with ROOT/ANNO/FRAME_RANGE/NUM_USE".format(label))
            continue
        root = record.get("ROOT")
        anno = record.get("ANNO")
        if not isinstance(root, str) or not root.strip():
            errors.append("{}.ROOT must be a non-empty path".format(label))
        if not isinstance(anno, str) or not anno.strip():
            errors.append("{}.ANNO must be a non-empty path".format(label))
        require_int(record, "FRAME_RANGE", label + ".FRAME_RANGE", errors, 0)
        num_use = record.get("NUM_USE")
        if not isinstance(num_use, int) or isinstance(num_use, bool) or num_use == 0 or num_use < -1:
            errors.append("{}.NUM_USE must be -1 or a positive integer".format(label))
        elif num_use == -1:
            unknown_total = True
        else:
            usable_total += num_use
        if isinstance(root, str) and root.strip() and isinstance(anno, str) and anno.strip():
            active_records.append((label, root, anno))

    samples_per_epoch = videos if isinstance(videos, int) and videos > 0 else None
    if samples_per_epoch is None and videos == 0 and not unknown_total:
        samples_per_epoch = usable_total
    if videos == 0 and unknown_total:
        warnings.append("epoch sample count depends on runtime video counts because NUM_USE=-1")
    if samples_per_epoch == 0:
        errors.append("effective samples per epoch is zero")
    if samples_per_epoch and batch:
        denom = batch * args.world_size
        num_per_epoch = samples_per_epoch // denom
        if num_per_epoch < 1:
            errors.append("effective samples per epoch is smaller than batch_size * world_size")
        if samples_per_epoch % denom:
            warnings.append(
                "effective samples per epoch ({}) is not divisible by batch_size * world_size ({})".format(
                    samples_per_epoch, denom
                )
            )
        notes.append("inferred optimizer batches per epoch: {}".format(num_per_epoch))

    if args.world_size > 1:
        if not args.allow_maintained_distributed:
            errors.append(
                "world_size > 1 is unsafe for the stock entry point; it hardcodes rank 0/world size 1"
            )
        else:
            warnings.append(
                "distributed static checks assume a separately maintained rank/device/sampler implementation"
            )

    compare_channels(adjust, ban, adjust_enabled, ban_enabled, errors, warnings)
    validate_paths(config, active_records, args, errors, warnings, notes)
    validate_cuda(args, errors, notes)
    return errors, warnings, notes


def validate_lr_kwargs(lr_type, kwargs, label, errors, warnings):
    for key in ("start_lr", "end_lr"):
        if key in kwargs and (not is_number(kwargs[key]) or kwargs[key] <= 0):
            errors.append("{}.{} must be a positive finite number".format(label, key))
    if lr_type == "step" and "step" in kwargs:
        step = kwargs["step"]
        if not isinstance(step, int) or isinstance(step, bool) or step <= 0:
            errors.append("{}.step must be a positive integer".format(label))
    if lr_type == "multi-step" and "steps" in kwargs:
        steps = kwargs["steps"]
        if not isinstance(steps, (list, tuple)) or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in steps
        ):
            errors.append("{}.steps must be a list of positive integers".format(label))
        elif list(steps) != sorted(set(steps)):
            warnings.append("{}.steps should be sorted and unique".format(label))


def compare_channels(adjust, ban, adjust_enabled, ban_enabled, errors, warnings):
    if not (adjust_enabled and ban_enabled):
        return
    adjust_kwargs = adjust.get("KWARGS", {})
    ban_kwargs = ban.get("KWARGS", {})
    if not isinstance(adjust_kwargs, dict) or not isinstance(ban_kwargs, dict):
        return
    adjust_out = adjust_kwargs.get("out_channels")
    ban_in = ban_kwargs.get("in_channels")
    if is_number(adjust_out) and is_number(ban_in) and adjust_out != ban_in:
        errors.append(
            "ADJUST.KWARGS.out_channels ({}) does not match BAN.KWARGS.in_channels ({})".format(
                adjust_out, ban_in
            )
        )
    else:
        warnings.append(
            "static checks cannot prove selected backbone/neck/BAN implementation channel compatibility"
        )


def validate_paths(config, active_records, args, errors, warnings, notes):
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else None
    if project_root is None:
        warnings.append("dataset, weight, resume, log, and snapshot paths were not checked (no --project-root)")
        return
    if not project_root.is_dir():
        errors.append("project root is not a directory: {}".format(project_root))
        return
    notes.append("project root: {}".format(project_root))
    for label, root, anno in active_records:
        root_path = resolve_project_path(project_root, root)
        anno_path = resolve_project_path(project_root, anno)
        if not root_path.is_dir():
            errors.append("{}.ROOT directory not found: {}".format(label, root_path))
        if not anno_path.is_file():
            errors.append("{}.ANNO file not found: {}".format(label, anno_path))

    for dotted in ("BACKBONE.PRETRAINED", "TRAIN.PRETRAINED", "TRAIN.RESUME"):
        raw = path_get(config, dotted, "")
        if raw is None:
            raw = ""
        if not isinstance(raw, str):
            errors.append("{} must be a path string".format(dotted))
        elif raw.strip():
            candidate = resolve_project_path(project_root, raw)
            if not candidate.is_file():
                errors.append("{} file not found: {}".format(dotted, candidate))

    resume = path_get(config, "TRAIN.RESUME", "")
    pretrained = path_get(config, "TRAIN.PRETRAINED", "")
    if isinstance(resume, str) and resume.strip() and isinstance(pretrained, str) and pretrained.strip():
        warnings.append("TRAIN.RESUME is set, so TRAIN.PRETRAINED is ignored")

    for dotted in ("TRAIN.LOG_DIR", "TRAIN.SNAPSHOT_DIR"):
        raw = path_get(config, dotted)
        if not isinstance(raw, str) or not raw.strip():
            errors.append("{} must be a non-empty path string".format(dotted))
        else:
            candidate = resolve_project_path(project_root, raw)
            if candidate.exists() and not candidate.is_dir():
                errors.append("{} exists but is not a directory: {}".format(dotted, candidate))
            elif candidate.exists() and any(candidate.iterdir()):
                warnings.append("{} is a non-empty directory; check for run collisions: {}".format(dotted, candidate))


def validate_cuda(args, errors, notes):
    if not args.require_cuda:
        return
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append("cannot import torch for CUDA probe: {}".format(exc))
        return
    notes.append("torch version: {}".format(torch.__version__))
    if not torch.cuda.is_available():
        errors.append("torch.cuda.is_available() is false")
        return
    try:
        device = torch.cuda.current_device()
        name = torch.cuda.get_device_name(device)
        probe = torch.ones(1, device="cuda")
        value = float(probe.item())
        del probe
        notes.append("CUDA allocation passed on logical device {} ({}, value={})".format(device, name, value))
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append("CUDA allocation probe failed: {}".format(exc))


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only NanoTrack training config preflight. Merges a conservative "
            "copy of maintained defaults; does not import the project or start training."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", help="explicit YAML or JSON config file to validate")
    source.add_argument(
        "--mapping",
        help="minimal JSON object to merge over defaults, e.g. '{\"BAN\":{\"BAN\":true}}'",
    )
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override a dotted key after loading; repeatable, values use safe YAML scalars",
    )
    parser.add_argument(
        "--project-root",
        help="optional launch root; when set, active data/weight paths are required to exist",
    )
    parser.add_argument(
        "--world-size",
        type=int,
        default=1,
        help="planned process count for epoch math (default: 1; stock only supports 1)",
    )
    parser.add_argument(
        "--allow-maintained-distributed",
        action="store_true",
        help="acknowledge world_size>1 refers to a separately maintained distributed adaptation",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="import torch and perform a one-scalar CUDA allocation probe",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="return failure when any warning remains",
    )
    parser.add_argument(
        "--print-effective",
        action="store_true",
        help="print the merged effective mapping (may contain local paths)",
    )
    parser.add_argument("--json-output", action="store_true", help="emit the result as JSON")
    return parser


def load_raw(args):
    if args.config:
        path = Path(args.config).expanduser()
        if not path.is_file():
            raise ConfigError("config file not found: {}".format(path))
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigError("cannot read config file {}: {}".format(path, exc))
        raw = simple_yaml_load(text)
    else:
        try:
            raw = json.loads(args.mapping)
        except json.JSONDecodeError as exc:
            raise ConfigError("--mapping must be a JSON object: {}".format(exc))
        if not isinstance(raw, dict):
            raise ConfigError("--mapping must decode to an object")
    for assignment in args.overrides:
        set_dotted(raw, assignment)
    return raw


def emit(args, errors, warnings, notes, effective):
    ok = not errors and not (args.strict_warnings and warnings)
    payload = {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
    }
    if args.print_effective:
        payload["effective"] = effective
    if args.json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print("NanoTrack training config: {}".format("OK" if ok else "FAILED"))
    for title, items in (("ERRORS", errors), ("WARNINGS", warnings), ("NOTES", notes)):
        if items:
            print("\n{}:".format(title))
            for item in items:
                print("- {}".format(item))
    if args.print_effective:
        print("\nEFFECTIVE CONFIG:")
        print(json.dumps(effective, indent=2, sort_keys=True))
    if ok:
        print("\nStatic preflight passed; runtime/data/model checks are still required.")
    elif args.strict_warnings and warnings and not errors:
        print("\nWarnings are fatal because --strict-warnings was set.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.world_size < 1:
        parser.error("--world-size must be >= 1")
    if args.allow_maintained_distributed and args.world_size == 1:
        parser.error("--allow-maintained-distributed only applies when --world-size > 1")
    try:
        raw = load_raw(args)
        effective = deep_merge(DEFAULTS, raw)
        errors, warnings, notes = validate(effective, raw, args)
    except ConfigError as exc:
        if args.json_output:
            print(json.dumps({"ok": False, "errors": [str(exc)], "warnings": [], "notes": []}, indent=2))
        else:
            print("configuration error: {}".format(exc), file=sys.stderr)
        return 2
    emit(args, errors, warnings, notes, effective)
    if errors or (args.strict_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
