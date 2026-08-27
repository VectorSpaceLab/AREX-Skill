#!/usr/bin/env python3
"""Safely inspect the GluonCV MXNet model-zoo registry.

This helper is intentionally conservative:
- It imports the installed `gluoncv.model_zoo` package; it does not read a source checkout.
- It never requests pretrained weights and therefore should not download model files.
- `--dry-forward` is limited to `cifar_resnet20_v1` with `pretrained=False` on CPU.
"""

from __future__ import print_function

import argparse
import json
import sys
from collections import Counter

TINY_FORWARD_MODEL = "cifar_resnet20_v1"

FAMILY_RULES = [
    ("object-detection/ssd", lambda n: n.startswith("ssd_")),
    ("object-detection/yolo", lambda n: n.startswith("yolo3_")),
    ("object-detection/faster-rcnn", lambda n: n.startswith("faster_rcnn") or n.startswith("doublehead_rcnn")),
    ("object-detection/center-net", lambda n: n.startswith("center_net_")),
    ("instance-segmentation/mask-rcnn", lambda n: n.startswith("mask_rcnn") or n.startswith("custom_mask_rcnn")),
    ("semantic-segmentation", lambda n: n.startswith(("fcn_", "psp_", "deeplab_", "icnet_", "fastscnn", "danet_"))),
    ("pose", lambda n: n.startswith(("simple_pose_", "mobile_pose_", "alpha_pose_"))),
    ("action-recognition", lambda n: any(x in n for x in ["ucf101", "hmdb51", "kinetics", "sthsthv2", "c3d_", "p3d_", "r2plus1d", "i3d_", "slowfast_"])),
    ("depth", lambda n: n.startswith("monodepth2_")),
    ("tracking", lambda n: n.startswith("siamrpn_")),
    ("quantized-int8", lambda n: n.endswith("_int8")),
    ("cifar-classification", lambda n: n.startswith("cifar_")),
]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="List and validate GluonCV MXNet model-zoo names without downloading weights.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--count", action="store_true", help="Print the registry count. Count is included by default when no other output is selected.")
    parser.add_argument("--names", action="store_true", help="Print matching model names, one per line.")
    parser.add_argument("--filter", action="append", default=[], metavar="TEXT", help="Only include names containing TEXT. Repeat to require multiple substrings.")
    parser.add_argument("--model", action="append", default=[], metavar="NAME", help="Validate a specific model name. Repeat for multiple names.")
    parser.add_argument("--families", action="store_true", help="Print a coarse family summary inferred from registry name patterns.")
    parser.add_argument("--limit", type=int, default=0, help="Limit printed names after filtering; 0 means no limit.")
    parser.add_argument("--dry-forward", action="store_true", help="Run a tiny CPU forward for cifar_resnet20_v1 with pretrained=False. No downloads.")
    parser.add_argument("--dry-forward-model", default=TINY_FORWARD_MODEL, choices=[TINY_FORWARD_MODEL], help="Safety-limited model for --dry-forward.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument("--debug", action="store_true", help="Show exception tracebacks for import/forward failures.")
    return parser.parse_args(argv)


def import_registry(debug=False):
    try:
        import gluoncv  # noqa: F401
        from gluoncv import model_zoo
        names = sorted(str(name) for name in model_zoo.get_model_list())
        return gluoncv, model_zoo, names, None
    except Exception as exc:  # pragma: no cover - diagnostic path
        if debug:
            import traceback
            traceback.print_exc()
        return None, None, [], exc


def filter_names(names, filters):
    selected = names
    for text in filters:
        needle = text.lower()
        selected = [name for name in selected if needle in name.lower()]
    return selected


def classify_family(name):
    # Put int8 in its task family and also report quantized in a separate count by adding later.
    for family, pred in FAMILY_RULES:
        if family == "quantized-int8":
            continue
        if pred(name):
            return family
    return "image-classification/other"


def family_counts(names):
    counts = Counter(classify_family(name) for name in names)
    counts["quantized-int8"] = sum(1 for name in names if name.endswith("_int8"))
    return dict(sorted(counts.items()))


def validate_models(names, requested):
    lower_to_name = {name.lower(): name for name in names}
    result = {}
    for raw in requested:
        key = raw.lower()
        result[raw] = {
            "valid": key in lower_to_name,
            "canonical": lower_to_name.get(key),
        }
    return result


def run_tiny_forward(model_zoo, model_name):
    # Import mxnet lazily so inventory/listing still gives a clear model-zoo import failure first.
    import mxnet as mx

    ctx = mx.cpu()
    net = model_zoo.get_model(model_name, pretrained=False)
    net.initialize(ctx=ctx)
    x = mx.nd.random.uniform(shape=(1, 3, 32, 32), ctx=ctx)
    y = net(x)
    mx.nd.waitall()
    return {
        "model": model_name,
        "ctx": str(ctx),
        "input_shape": tuple(int(v) for v in x.shape),
        "output_shape": tuple(int(v) for v in y.shape),
        "pretrained": False,
    }


def print_text(result, args):
    should_print_count = args.count or not (args.names or args.model or args.families or args.dry_forward)
    if should_print_count:
        print("mxnet model count: {}".format(result["model_count"]))

    if args.families:
        print("families:")
        for family, count in result["families"].items():
            print("  {}: {}".format(family, count))

    if args.model:
        for requested, info in result["validations"].items():
            if info["valid"]:
                print("valid model: {}".format(info["canonical"]))
            else:
                print("invalid model: {}".format(requested), file=sys.stderr)

    if args.names:
        names_to_print = result["matching_names"]
        if args.limit and args.limit > 0:
            names_to_print = names_to_print[: args.limit]
        for name in names_to_print:
            print(name)
        if args.limit and args.limit > 0 and len(result["matching_names"]) > args.limit:
            print("... {} more not shown".format(len(result["matching_names"]) - args.limit), file=sys.stderr)

    if args.dry_forward:
        dry = result.get("dry_forward") or {}
        print(
            "dry forward: model={model} input_shape={input_shape} output_shape={output_shape} ctx={ctx} pretrained={pretrained}".format(
                **dry
            )
        )


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    gluoncv, model_zoo, names, import_error = import_registry(debug=args.debug)
    if import_error is not None:
        message = (
            "failed to import GluonCV MXNet model_zoo: {}: {}. "
            "Install a supported MXNet/GluonCV environment and retry."
        ).format(type(import_error).__name__, import_error)
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2, sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 1

    matching = filter_names(names, args.filter)
    validations = validate_models(names, args.model)
    invalid = [model for model, info in validations.items() if not info["valid"]]

    result = {
        "ok": not invalid,
        "gluoncv_version": getattr(gluoncv, "__version__", None),
        "model_count": len(names),
        "filters": args.filter,
        "matching_count": len(matching),
        "matching_names": matching,
        "validations": validations,
        "families": family_counts(names) if args.families else {},
    }

    if args.dry_forward:
        try:
            result["dry_forward"] = run_tiny_forward(model_zoo, args.dry_forward_model)
        except Exception as exc:  # pragma: no cover - diagnostic path
            if args.debug:
                import traceback
                traceback.print_exc()
            result["ok"] = False
            result["dry_forward_error"] = "{}: {}".format(type(exc).__name__, exc)

    if args.json:
        # Respect --limit in JSON only for matching_names; counts still describe full filtered set.
        if args.limit and args.limit > 0:
            result = dict(result)
            result["matching_names"] = result["matching_names"][: args.limit]
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result, args)
        if result.get("dry_forward_error"):
            print("dry forward failed: {}".format(result["dry_forward_error"]), file=sys.stderr)

    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
