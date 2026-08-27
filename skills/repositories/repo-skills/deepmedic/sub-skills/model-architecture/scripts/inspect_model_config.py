#!/usr/bin/env python3
"""Safely inspect literal DeepMedic modelConfig assignments.

This intentionally parses the Python syntax with AST and evaluates only
literal assignments. It does not import DeepMedic/TensorFlow and never execs
the supplied config.
"""

from __future__ import print_function

import argparse
import ast
import json
import os
import sys


DEFAULTS = {
    "modelName": "deepmedic",
    "useSubsampledPathway": False,
    "segmentsDimVal": None,
    "segmentsDimInference": None,
    "padTypePerLayerNormal": None,
    "padTypePerLayerSubsampled": None,
    "padTypePerLayerFC": None,
    "numberFMsPerLayerFC": [],
    "dropoutRatesNormal": [],
    "dropoutRatesSubsampled": [],
    "dropoutRatesFc": None,
    "convWeightsInit": ["fanIn", 2],
    "activationFunction": "prelu",
    "rollAverageForBNOverThatManyBatches": 60,
    "layersWithResidualConnNormal": [],
    "layersWithResidualConnSubsampled": None,
    "layersWithResidualConnFC": [],
    "lowerRankLayersNormal": [],
    "lowerRankLayersSubsampled": None,
    "subsampleFactor": [3, 3, 3],
}


def _literal_assignments(tree):
    values = {}
    skipped = []
    for node in tree.body:
        targets = []
        value_node = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value_node = node.value
        if value_node is None:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            try:
                values[target.id] = ast.literal_eval(value_node)
            except (ValueError, TypeError, SyntaxError):
                skipped.append(target.id)
    return values, sorted(set(skipped))


def _get(values, key):
    return values[key] if key in values else DEFAULTS.get(key)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_three(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    if not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        return None
    return [int(item) for item in value]


def _kernel_list(value):
    if not isinstance(value, list) or not value:
        return None
    result = []
    for kernel in value:
        parsed = _as_three(kernel)
        if parsed is None:
            return None
        result.append(parsed)
    return result


def _fm_paths(value):
    """ModelParameters wraps a flat subsampled FM list into one path."""
    if not isinstance(value, list):
        return None
    if all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        return [[int(item) for item in value]]
    if all(isinstance(item, list) for item in value):
        result = []
        for path in value:
            if not all(isinstance(item, int) and not isinstance(item, bool) for item in path):
                return None
            result.append([int(item) for item in path])
        return result
    return None


def _factor_paths(value):
    if _as_three(value) is not None:
        return [_as_three(value)]
    if isinstance(value, list) and value and all(_as_three(item) is not None for item in value):
        return [_as_three(item) for item in value]
    return None


def _rf(kernels):
    if kernels is None:
        return None
    return [1 + sum(kernel[dim] - 1 for kernel in kernels) for dim in range(3)]


def _add_rf(first, second):
    if first is None or second is None:
        return None
    return [first[dim] + second[dim] - 1 for dim in range(3)]


def _padding_is_valid(mode):
    return mode is None or str(mode).lower() in ("valid", "none")


def _path_output(dims, kernels, pads):
    if dims is None or kernels is None:
        return None
    current = list(dims)
    for index, kernel in enumerate(kernels):
        mode = pads[index] if pads is not None and index < len(pads) else "VALID"
        if _padding_is_valid(mode):
            current = [current[d] - kernel[d] + 1 for d in range(3)]
        else:
            # DeepMedic's convolution dimension helper uses kernel-1 padding
            # for MIRROR, ZERO, and other non-VALID modes.
            current = list(current)
    return current


def _field_lengths(values, errors, warnings, normal, subs, fc_hidden):
    expected = {
        "padTypePerLayerNormal": len(normal) if normal is not None else None,
        "dropoutRatesNormal": len(normal) if normal is not None else None,
        "padTypePerLayerSubsampled": len(subs[0]) if subs else None,
        "dropoutRatesSubsampled": len(subs[0]) if subs else None,
        "padTypePerLayerFC": len(fc_hidden) + 1,
        "dropoutRatesFc": len(fc_hidden) + 1,
    }
    for name, count in expected.items():
        raw = _get(values, name)
        if raw is None or raw == []:
            continue
        if not isinstance(raw, list) or len(raw) != count:
            errors.append("{} should have {} entries (got {!r}).".format(name, count, raw))


def inspect(path):
    result = {
        "config": os.path.abspath(path),
        "normalized": {},
        "derived": {},
        "errors": [],
        "warnings": [],
        "skipped_dynamic_assignments": [],
    }
    if not os.path.isfile(path):
        result["errors"].append("Configuration file does not exist: {}".format(path))
        return result, 2
    try:
        with open(path, "r") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path, mode="exec")
    except SyntaxError as exc:
        result["errors"].append("Python syntax error at line {}: {}".format(exc.lineno, exc.msg))
        return result, 2
    except OSError as exc:
        result["errors"].append("Could not read configuration: {}".format(exc))
        return result, 2

    values, skipped = _literal_assignments(tree)
    result["skipped_dynamic_assignments"] = skipped
    normal = _fm_paths(values.get("numberFMsPerLayerNormal"))
    normal = normal[0] if normal and len(normal) == 1 else None
    normal_kernels = _kernel_list(values.get("kernelDimPerLayerNormal"))
    normal_rf = _rf(normal_kernels)
    use_subs = bool(_get(values, "useSubsampledPathway"))
    subs = []
    subs_kernels = None
    factors = []
    if use_subs:
        raw_sub_fms = values.get("numberFMsPerLayerSubsampled")
        if raw_sub_fms is None:
            raw_sub_fms = values.get("numberFMsPerLayerNormal")
        subs = _fm_paths(raw_sub_fms) or []
        factors = _factor_paths(_get(values, "subsampleFactor")) or []
        if subs and normal_kernels is not None:
            raw_sub_kernels = values.get("kernelDimPerLayerSubsampled")
            if raw_sub_kernels is None and len(subs[0]) == len(normal):
                subs_kernels = normal_kernels
            else:
                subs_kernels = _kernel_list(raw_sub_kernels)
    fc_hidden = _get(values, "numberFMsPerLayerFC")
    if not isinstance(fc_hidden, list):
        fc_hidden = None
    fc_kernels = _kernel_list(values.get("kernelDimPerLayerFC"))
    if fc_kernels is None and fc_hidden is not None:
        fc_kernels = [[1, 1, 1] for _ in range(len(fc_hidden) + 1)]
    fc_rf = _rf(fc_kernels)
    total_rf = _add_rf(normal_rf, fc_rf)

    normalized_keys = [
        "modelName", "folderForOutput", "numberOfOutputClasses", "numberOfInputChannels",
        "numberFMsPerLayerNormal", "kernelDimPerLayerNormal", "padTypePerLayerNormal",
        "useSubsampledPathway", "numberFMsPerLayerSubsampled", "kernelDimPerLayerSubsampled",
        "subsampleFactor", "numberFMsPerLayerFC", "kernelDimPerLayerFC",
        "padTypePerLayerFC", "segmentsDimTrain", "segmentsDimVal", "segmentsDimInference",
        "dropoutRatesNormal", "dropoutRatesSubsampled", "dropoutRatesFc",
        "convWeightsInit", "activationFunction", "rollAverageForBNOverThatManyBatches",
        "layersWithResidualConnNormal", "layersWithResidualConnSubsampled",
        "layersWithResidualConnFC", "lowerRankLayersNormal", "lowerRankLayersSubsampled",
    ]
    for key in normalized_keys:
        value = _get(values, key)
        if key == "segmentsDimVal" and value is None:
            value = normal_rf
        if key == "segmentsDimInference" and value is None:
            value = _get(values, "segmentsDimTrain")
        if key == "padTypePerLayerNormal" and value is None and normal is not None:
            value = ["VALID"] * len(normal)
        if key == "padTypePerLayerFC" and value is None and fc_hidden is not None:
            value = ["VALID"] * (len(fc_hidden) + 1)
        if key == "padTypePerLayerSubsampled" and value is None and subs:
            value = ["VALID"] * len(subs[0])
        if key == "layersWithResidualConnSubsampled" and value is None and use_subs:
            value = _get(values, "layersWithResidualConnNormal")
        if key == "lowerRankLayersSubsampled" and value is None and use_subs:
            value = _get(values, "lowerRankLayersNormal")
        if key == "numberFMsPerLayerSubsampled" and value is None and normal is not None:
            value = [normal]
        if key == "kernelDimPerLayerSubsampled" and value is None and normal_kernels is not None:
            value = normal_kernels
        result["normalized"][key] = value

    classes = values.get("numberOfOutputClasses")
    channels = values.get("numberOfInputChannels")
    if not isinstance(classes, int) or isinstance(classes, bool) or classes < 1:
        result["errors"].append("numberOfOutputClasses must be a positive integer and includes background.")
    if not isinstance(channels, int) or isinstance(channels, bool) or channels < 1:
        result["errors"].append("numberOfInputChannels must be a positive integer.")
    if normal is None or not normal:
        result["errors"].append("numberFMsPerLayerNormal must be a non-empty flat integer list.")
    elif any(item < 1 for item in normal):
        result["errors"].append("Every normal-pathway feature-map count must be positive.")
    if normal_kernels is None or (normal is not None and len(normal_kernels) != len(normal)):
        result["errors"].append("kernelDimPerLayerNormal must contain one 3-integer kernel per normal layer.")
    elif any(any(item < 1 for item in kernel) for kernel in normal_kernels):
        result["errors"].append("Normal kernel dimensions must be positive.")
    elif any(any(item % 2 == 0 for item in kernel) for kernel in normal_kernels):
        result["warnings"].append("Even normal kernels are not thoroughly tested; prefer odd dimensions.")

    if use_subs:
        if not factors:
            result["errors"].append("subsampleFactor must be a 3-vector or a list of 3-vectors.")
        else:
            for factor in factors:
                if any(item < 1 for item in factor):
                    result["errors"].append("Each subsampleFactor entry must be positive.")
                if any(item % 2 == 0 for item in factor):
                    result["warnings"].append("Even subsampling factors are not thoroughly tested: {}".format(factor))
        if not subs:
            result["errors"].append("numberFMsPerLayerSubsampled must be a flat list or list of integer lists.")
        elif any(item < 1 for path_fms in subs for item in path_fms):
            result["errors"].append("Every subsampled feature-map count must be positive.")
        elif any(len(path_fms) != len(subs[0]) for path_fms in subs):
            result["errors"].append("All subsampled FM paths must have the same number of layers.")
        if subs_kernels is None or (subs and len(subs_kernels) != len(subs[0])):
            result["errors"].append("kernelDimPerLayerSubsampled must contain one 3-integer kernel per shared subsampled layer.")
        elif normal_rf is not None and _rf(subs_kernels) != normal_rf:
            result["errors"].append("Normal and subsampled receptive fields differ: {} versus {}.".format(normal_rf, _rf(subs_kernels)))
        if len(subs) > len(factors):
            result["warnings"].append("There are more subsampled FM lists than factors; only factor-created paths are built.")
        if len(subs) < len(factors):
            result["warnings"].append("Missing subsampled FM lists are copied from the preceding list by the native parser.")

    if fc_hidden is None or any(not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in fc_hidden):
        result["errors"].append("numberFMsPerLayerFC must be a list of positive integers (or []).")
    if fc_kernels is None or (fc_hidden is not None and len(fc_kernels) != len(fc_hidden) + 1):
        result["errors"].append("kernelDimPerLayerFC must have one 3-vector per hidden layer plus classifier.")
    elif any(any(item < 1 for item in kernel) for kernel in fc_kernels):
        result["errors"].append("FC kernel dimensions must be positive.")
    elif any(any(item % 2 == 0 for item in kernel) for kernel in fc_kernels):
        result["warnings"].append("Even FC kernels are not thoroughly tested; prefer odd dimensions.")

    if _get(values, "activationFunction") == "selu":
        result["warnings"].append("selu is parser-accepted but its layer implementation raises NotImplementedError when applied.")
    if _get(values, "activationFunction") not in ("linear", "relu", "prelu", "elu", "selu"):
        result["errors"].append("activationFunction must be linear, relu, prelu, elu, or selu.")
    init = _get(values, "convWeightsInit")
    if not isinstance(init, list) or len(init) < 2 or init[0] not in ("normal", "fanIn"):
        result["errors"].append("convWeightsInit must be ['normal', std] or ['fanIn', scale].")

    _field_lengths(values, result["errors"], result["warnings"], normal or [], subs, fc_hidden or [])
    for name, depth in (("layersWithResidualConnNormal", len(normal or [])),
                        ("layersWithResidualConnSubsampled", len(subs[0]) if subs else 0),
                        ("layersWithResidualConnFC", len(fc_hidden or []) + 1)):
        entries = _get(values, name)
        if entries is None:
            continue
        if not isinstance(entries, list) or any(not isinstance(item, int) for item in entries):
            result["errors"].append("{} must be a list of integer layer numbers.".format(name))
        else:
            if 1 in entries:
                result["errors"].append("{} cannot contain layer 1 for a residual connection.".format(name))
            if any(item < 1 or item > depth for item in entries):
                result["warnings"].append("{} contains a layer outside the built depth {}.".format(name, depth))

    segment_values = {
        "train": values.get("segmentsDimTrain"),
        "val": _get(values, "segmentsDimVal") if _get(values, "segmentsDimVal") is not None else normal_rf,
        "inference": _get(values, "segmentsDimInference") if _get(values, "segmentsDimInference") is not None else values.get("segmentsDimTrain"),
    }
    if segment_values["train"] is None:
        result["errors"].append("segmentsDimTrain is required and must be a 3-vector.")
    for role, dims in segment_values.items():
        parsed = _as_three(dims)
        if parsed is None:
            result["errors"].append("segmentsDim{} must be a 3-integer vector.".format(role.capitalize()))
        elif normal_rf is not None and any(parsed[d] < normal_rf[d] for d in range(3)):
            result["errors"].append("{} segment {} is smaller than normal receptive field {}.".format(role, parsed, normal_rf))

    normal_pads = _get(values, "padTypePerLayerNormal")
    if normal_pads is None and normal is not None:
        normal_pads = ["VALID"] * len(normal)
    fc_pads = _get(values, "padTypePerLayerFC")
    if fc_pads is None and fc_hidden is not None:
        fc_pads = ["VALID"] * (len(fc_hidden) + 1)
    train_dims = _as_three(values.get("segmentsDimTrain"))
    normal_out = _path_output(train_dims, normal_kernels, normal_pads)
    full_out = _path_output(normal_out, fc_kernels, fc_pads)
    result["derived"] = {
        "normal_layer_count": len(normal or []),
        "normal_receptive_field": normal_rf,
        "active_subsampled_path_count": len(factors),
        "subsampled_receptive_field": _rf(subs_kernels),
        "subsample_factors": factors,
        "fc_hidden_layer_count": len(fc_hidden or []),
        "fc_total_layer_count": len(fc_hidden or []) + 1 if fc_hidden is not None else None,
        "fc_receptive_field": fc_rf,
        "approx_full_model_receptive_field_including_fc": total_rf,
        "fc_input_feature_maps": ((normal[-1] if normal else 0) + sum(path[-1] for path in subs if path)) if use_subs else (normal[-1] if normal else 0),
        "classifier_feature_maps": classes,
        "normal_output_dims_from_train_segment": normal_out,
        "full_output_dims_from_train_segment": full_out,
        "available_literal_fields": sorted(values.keys()),
    }
    if skipped:
        result["warnings"].append("Skipped non-literal assignments (not executed): {}".format(", ".join(skipped)))
    return result, 1 if result["errors"] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Safely inspect a DeepMedic modelConfig.py without importing TensorFlow or executing it."
    )
    parser.add_argument("model_config", help="Path to the Python-syntax model config")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    result, code = inspect(args.model_config)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Model config: {}".format(result["config"]))
        if result["errors"]:
            print("Errors:")
            for item in result["errors"]:
                print("  - {}".format(item))
        if result["warnings"]:
            print("Warnings:")
            for item in result["warnings"]:
                print("  - {}".format(item))
        print("Normalized fields:")
        for key in sorted(result["normalized"]):
            print("  {} = {!r}".format(key, result["normalized"][key]))
        print("Derived values:")
        for key in sorted(result["derived"]):
            print("  {} = {!r}".format(key, result["derived"][key]))
        if result["skipped_dynamic_assignments"]:
            print("Skipped dynamic assignments (not executed): {}".format(", ".join(result["skipped_dynamic_assignments"])))
    return code


if __name__ == "__main__":
    sys.exit(main())
