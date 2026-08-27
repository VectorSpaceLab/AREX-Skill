#!/usr/bin/env python3
"""Static source inspector for tf-faster-rcnn architecture APIs.

The script reads Python source files from a supplied checkout and reports
signatures/patterns using AST and text inspection only. It does not import the
repository, build TensorFlow graphs, run training/inference, or compile native
extensions.
"""
from __future__ import print_function

import argparse
import ast
import json
import sys
from pathlib import Path

REQUIRED_FILES = [
    "lib/nets/network.py",
    "lib/nets/vgg16.py",
    "lib/nets/resnet_v1.py",
    "lib/nets/mobilenet_v1.py",
    "lib/layer_utils/anchor_target_layer.py",
    "lib/layer_utils/generate_anchors.py",
    "lib/layer_utils/proposal_layer.py",
    "lib/layer_utils/proposal_target_layer.py",
    "lib/layer_utils/proposal_top_layer.py",
    "lib/layer_utils/snippets.py",
    "lib/model/bbox_transform.py",
    "lib/model/test.py",
    "lib/roi_data_layer/layer.py",
    "lib/roi_data_layer/minibatch.py",
    "lib/roi_data_layer/roidb.py",
    "lib/utils/blob.py",
    "lib/utils/timer.py",
    "lib/utils/visualization.py",
]

EXPECTED_SIGNATURES = {
    "Network.create_architecture": "(self, mode, num_classes, tag=None, anchor_scales=(8, 16, 32), anchor_ratios=(0.5, 1, 2))",
    "vgg16.__init__": "(self)",
    "resnetv1.__init__": "(self, num_layers=50)",
    "mobilenetv1.__init__": "(self)",
}

INTERESTING_CLASS_METHODS = {
    "Network": [
        "__init__", "create_architecture", "_build_network", "_anchor_component",
        "_region_proposal", "_region_classification", "_proposal_layer",
        "_proposal_top_layer", "_anchor_target_layer", "_proposal_target_layer",
        "_crop_pool_layer", "_image_to_head", "_head_to_tail",
        "get_variables_to_restore", "fix_variables", "test_image",
        "train_step", "train_step_with_summary", "extract_head",
    ],
    "vgg16": ["__init__", "_image_to_head", "_head_to_tail", "get_variables_to_restore", "fix_variables"],
    "resnetv1": ["__init__", "_crop_pool_layer", "_build_base", "_image_to_head", "_head_to_tail", "_decide_blocks", "get_variables_to_restore", "fix_variables"],
    "mobilenetv1": ["__init__", "_image_to_head", "_head_to_tail", "get_variables_to_restore", "fix_variables"],
    "RoIDataLayer": ["__init__", "_shuffle_roidb_inds", "_get_next_minibatch_inds", "_get_next_minibatch", "forward"],
    "Timer": ["__init__", "tic", "toc"],
}

INTERESTING_FUNCTIONS = {
    "lib/nets/resnet_v1.py": ["resnet_arg_scope"],
    "lib/nets/mobilenet_v1.py": ["separable_conv2d_same", "mobilenet_v1_base", "mobilenet_v1_arg_scope"],
    "lib/layer_utils/generate_anchors.py": ["generate_anchors", "_whctrs", "_mkanchors", "_ratio_enum", "_scale_enum"],
    "lib/layer_utils/snippets.py": ["generate_anchors_pre", "generate_anchors_pre_tf"],
    "lib/layer_utils/proposal_layer.py": ["proposal_layer", "proposal_layer_tf"],
    "lib/layer_utils/proposal_top_layer.py": ["proposal_top_layer", "proposal_top_layer_tf"],
    "lib/layer_utils/anchor_target_layer.py": ["anchor_target_layer", "_unmap", "_compute_targets"],
    "lib/layer_utils/proposal_target_layer.py": ["proposal_target_layer", "_get_bbox_regression_labels", "_compute_targets", "_sample_rois"],
    "lib/model/bbox_transform.py": ["bbox_transform", "bbox_transform_inv", "clip_boxes", "bbox_transform_inv_tf", "clip_boxes_tf"],
    "lib/model/test.py": ["_get_image_blob", "_get_blobs", "_clip_boxes", "_rescale_boxes", "im_detect", "apply_nms", "test_net"],
    "lib/roi_data_layer/minibatch.py": ["get_minibatch", "_get_image_blob"],
    "lib/roi_data_layer/roidb.py": ["prepare_roidb"],
    "lib/utils/blob.py": ["im_list_to_blob", "prep_im_for_blob"],
    "lib/utils/visualization.py": ["_draw_single_box", "draw_bounding_boxes"],
}


def render_node(node):
    """Render a small AST expression without depending on ast.unparse."""
    if node is None:
        return "None"
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):  # Python 3.8+
        return repr(node.value)
    # Avoid direct ast.Num/ast.Str/ast.NameConstant references so modern
    # Python does not emit deprecation warnings, while Python 3.7 still works.
    node_type = type(node).__name__
    if node_type == "Num":
        return repr(node.n)
    if node_type == "Str":
        return repr(node.s)
    if node_type == "NameConstant":
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return render_node(node.value) + "." + node.attr
    if isinstance(node, ast.Tuple):
        parts = [render_node(e) for e in node.elts]
        if len(parts) == 1:
            return "(" + parts[0] + ",)"
        return "(" + ", ".join(parts) + ")"
    if isinstance(node, ast.List):
        return "[" + ", ".join(render_node(e) for e in node.elts) + "]"
    if isinstance(node, ast.Dict):
        parts = []
        for key, value in zip(node.keys, node.values):
            parts.append(render_node(key) + ": " + render_node(value))
        return "{" + ", ".join(parts) + "}"
    if isinstance(node, ast.UnaryOp):
        op = "-" if isinstance(node.op, ast.USub) else "+" if isinstance(node.op, ast.UAdd) else "not "
        return op + render_node(node.operand)
    if isinstance(node, ast.BinOp):
        ops = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//",
            ast.Mod: "%", ast.Pow: "**", ast.LShift: "<<", ast.RShift: ">>",
            ast.BitOr: "|", ast.BitAnd: "&",
        }
        return render_node(node.left) + " " + ops.get(type(node.op), "?") + " " + render_node(node.right)
    if isinstance(node, ast.Call):
        args = [render_node(a) for a in node.args]
        args.extend((kw.arg or "**") + "=" + render_node(kw.value) for kw in node.keywords)
        return render_node(node.func) + "(" + ", ".join(args) + ")"
    if isinstance(node, ast.Subscript):
        return render_node(node.value) + "[...]"
    return "<" + node.__class__.__name__ + ">"


def function_signature(fn):
    args_obj = fn.args
    positional = list(getattr(args_obj, "posonlyargs", [])) + list(args_obj.args)
    defaults = list(args_obj.defaults)
    default_offset = len(positional) - len(defaults)
    parts = []
    for idx, arg in enumerate(positional):
        part = arg.arg
        if idx >= default_offset:
            part += "=" + render_node(defaults[idx - default_offset])
        parts.append(part)
    if args_obj.vararg:
        parts.append("*" + args_obj.vararg.arg)
    if args_obj.kwonlyargs:
        if not args_obj.vararg:
            parts.append("*")
        for arg, default in zip(args_obj.kwonlyargs, args_obj.kw_defaults):
            part = arg.arg
            if default is not None:
                part += "=" + render_node(default)
            parts.append(part)
    if args_obj.kwarg:
        parts.append("**" + args_obj.kwarg.arg)
    return "(" + ", ".join(parts) + ")"


def public_signature(sig):
    if sig.startswith("(self, "):
        return "(" + sig[len("(self, "):]
    if sig == "(self)":
        return "()"
    return sig


def parse_file(path):
    text = path.read_text(encoding="utf-8")
    return ast.parse(text, filename=str(path)), text


def class_methods(tree, class_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            found = {}
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    found[item.name] = function_signature(item)
            return found
    return {}


def module_functions(tree):
    return {node.name: function_signature(node) for node in tree.body if isinstance(node, ast.FunctionDef)}


def find_string_patterns(text):
    patterns = {
        "uses_tf_py_func": "tf.py_func" in text,
        "uses_cfg_use_e2e_tf": "cfg.USE_E2E_TF" in text,
        "uses_cfg_use_gpu_nms": "cfg.USE_GPU_NMS" in text,
        "uses_test_mode_nms": "cfg.TEST.MODE == 'nms'" in text or 'cfg.TEST.MODE == "nms"' in text,
        "uses_test_mode_top": "cfg.TEST.MODE == 'top'" in text or 'cfg.TEST.MODE == "top"' in text,
        "single_image_placeholder": "shape=[1, None, None, 3]" in text,
        "single_batch_assertion": "Single batch only" in text or "Only single-image batch implemented" in text,
        "pooling_crop_only": "cfg.POOLING_MODE == 'crop'" in text or 'cfg.POOLING_MODE == "crop"' in text,
    }
    return {k: v for k, v in patterns.items() if v}


def inspect_repo(repo_root):
    repo_root = repo_root.resolve()
    missing = []
    parse_errors = []
    parsed = {}
    for rel in REQUIRED_FILES:
        path = repo_root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        try:
            parsed[rel] = parse_file(path)
        except SyntaxError as exc:
            parse_errors.append({"file": rel, "error": str(exc)})

    result = {
        "status": "ok",
        "repo_root": str(repo_root),
        "inspection_mode": "AST and text patterns only; no repo imports or training/inference execution",
        "checked_files": sorted(parsed.keys()),
        "missing_files": missing,
        "parse_errors": parse_errors,
        "network_api": {},
        "function_api": {},
        "patterns": {},
        "signature_checks": {},
        "warnings": [],
    }

    if missing or parse_errors:
        result["status"] = "needs_review"

    # Classes and methods
    class_locations = {
        "Network": "lib/nets/network.py",
        "vgg16": "lib/nets/vgg16.py",
        "resnetv1": "lib/nets/resnet_v1.py",
        "mobilenetv1": "lib/nets/mobilenet_v1.py",
        "RoIDataLayer": "lib/roi_data_layer/layer.py",
        "Timer": "lib/utils/timer.py",
    }
    for class_name, rel in class_locations.items():
        if rel not in parsed:
            continue
        tree, _ = parsed[rel]
        methods = class_methods(tree, class_name)
        selected = {}
        for method in INTERESTING_CLASS_METHODS.get(class_name, sorted(methods)):
            if method in methods:
                selected[method] = methods[method]
        result["network_api" if class_name in {"Network", "vgg16", "resnetv1", "mobilenetv1"} else "function_api"][class_name] = {
            "file": rel,
            "methods": selected,
        }

    # Module-level functions
    for rel, names in INTERESTING_FUNCTIONS.items():
        if rel not in parsed:
            continue
        tree, _ = parsed[rel]
        funcs = module_functions(tree)
        result["function_api"][rel] = {name: funcs[name] for name in names if name in funcs}

    # Pattern checks
    for rel, (_tree, text) in parsed.items():
        patterns = find_string_patterns(text)
        if patterns:
            result["patterns"][rel] = patterns

    # Expected signature checks
    actuals = {}
    network = result["network_api"].get("Network", {}).get("methods", {})
    actuals["Network.create_architecture"] = network.get("create_architecture")
    for cls in ("vgg16", "resnetv1", "mobilenetv1"):
        actuals[cls + ".__init__"] = result["network_api"].get(cls, {}).get("methods", {}).get("__init__")

    for key, expected in EXPECTED_SIGNATURES.items():
        actual = actuals.get(key)
        ok = actual == expected
        result["signature_checks"][key] = {"expected": expected, "actual": actual, "ok": ok}
        if not ok:
            result["status"] = "needs_review"

    ca = actuals.get("Network.create_architecture")
    if ca:
        result["network_api"]["Network"]["public_create_architecture"] = "create_architecture" + public_signature(ca)
    for cls in ("vgg16", "resnetv1", "mobilenetv1"):
        sig = actuals.get(cls + ".__init__")
        if sig and cls in result["network_api"]:
            result["network_api"][cls]["public_constructor"] = cls + public_signature(sig)

    # Source-derived warnings and boundaries
    result["warnings"].append("This report is source inspection only and does not prove TensorFlow graph execution.")
    result["warnings"].append("Default full runtime still depends on legacy TensorFlow/Cython/NMS/CUDA/checkpoint/dataset setup outside this script.")
    if result["status"] != "ok":
        result["warnings"].append("Review missing files, parse errors, or signature drift before updating the skill guidance.")

    return result


def print_text(report):
    print("tf-faster-rcnn API source inspection")
    print("status: {}".format(report["status"]))
    print("mode: {}".format(report["inspection_mode"]))
    print("checked files: {}".format(len(report["checked_files"])))
    if report["missing_files"]:
        print("missing files:")
        for rel in report["missing_files"]:
            print("  - " + rel)
    if report["parse_errors"]:
        print("parse errors:")
        for item in report["parse_errors"]:
            print("  - {file}: {error}".format(**item))

    print("\nverified signature checks:")
    for key in sorted(report["signature_checks"]):
        item = report["signature_checks"][key]
        marker = "OK" if item["ok"] else "DRIFT"
        print("  - {key}: {marker}".format(key=key, marker=marker))
        print("      actual:   {}".format(item["actual"]))
        print("      expected: {}".format(item["expected"]))

    print("\npublic constructors / architecture:")
    for cls in ("vgg16", "resnetv1", "mobilenetv1"):
        data = report["network_api"].get(cls, {})
        if data.get("public_constructor"):
            print("  - " + data["public_constructor"])
    net = report["network_api"].get("Network", {})
    if net.get("public_create_architecture"):
        print("  - " + net["public_create_architecture"])

    print("\nkey method signatures:")
    for cls in ("Network", "vgg16", "resnetv1", "mobilenetv1"):
        data = report["network_api"].get(cls)
        if not data:
            continue
        print("  {} ({})".format(cls, data["file"]))
        for name, sig in sorted(data["methods"].items()):
            print("    - {}{}".format(name, sig))

    print("\nlayer/data utility signatures:")
    for rel in sorted(report["function_api"]):
        if rel in ("RoIDataLayer", "Timer"):
            continue
        print("  " + rel)
        funcs = report["function_api"][rel]
        for name, sig in sorted(funcs.items()):
            print("    - {}{}".format(name, sig))

    if report["warnings"]:
        print("\nwarnings:")
        for warning in report["warnings"]:
            print("  - " + warning)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect tf-faster-rcnn architecture/source APIs via AST without importing the repo."
    )
    parser.add_argument("--repo-root", required=True, help="Path to a tf-faster-rcnn source checkout to inspect.")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format. Default: json.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when required files are missing, parse errors occur, or expected signatures drift.")
    args = parser.parse_args(argv)

    report = inspect_repo(Path(args.repo_root))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.strict and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
