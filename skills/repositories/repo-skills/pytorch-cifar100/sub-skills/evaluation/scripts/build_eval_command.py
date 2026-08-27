#!/usr/bin/env python3
"""Build a safe pytorch-cifar100 test.py command without executing it.

This helper is intentionally self-contained and does not import the repository.
"""

import argparse
import json as json_module
import re
import shlex
import sys
from pathlib import Path

VALID_NETS = (
    "attention56",
    "attention92",
    "densenet121",
    "densenet161",
    "densenet169",
    "densenet201",
    "googlenet",
    "inceptionresnetv2",
    "inceptionv3",
    "inceptionv4",
    "mobilenet",
    "mobilenetv2",
    "nasnet",
    "preactresnet18",
    "preactresnet34",
    "preactresnet50",
    "preactresnet101",
    "preactresnet152",
    "resnet18",
    "resnet34",
    "resnet50",
    "resnet101",
    "resnet152",
    "resnext50",
    "resnext101",
    "resnext152",
    "seresnet18",
    "seresnet34",
    "seresnet50",
    "seresnet101",
    "seresnet152",
    "shufflenet",
    "shufflenetv2",
    "squeezenet",
    "stochasticdepth18",
    "stochasticdepth34",
    "stochasticdepth50",
    "stochasticdepth101",
    "vgg11",
    "vgg13",
    "vgg16",
    "vgg19",
    "wideresnet",
    "xception",
)

CHECKPOINT_NAME_RE = re.compile(r"^(?P<net>[A-Za-z0-9]+)-(?P<epoch>[0-9]+)-(?P<kind>regular|best)(?:\.pth)?$")


def is_placeholder(value):
    stripped = value.strip()
    return (
        not stripped
        or (stripped.startswith("<") and stripped.endswith(">"))
        or "PLACEHOLDER" in stripped.upper()
    )


def shell_join(parts):
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_test_argv(args):
    cmd = [args.python, "test.py", "-net", args.net, "-weights", args.weights]
    if args.gpu:
        cmd.append("-gpu")
    cmd.extend(["-b", str(args.batch_size)])
    return cmd


def build_shell_command(args):
    command = shell_join(build_test_argv(args))
    root = args.repo_root_placeholder
    if root:
        return "cd {} && {}".format(shlex.quote(root), command)
    return command


def candidate_weight_paths(raw_weights, repo_root_placeholder):
    raw = Path(raw_weights).expanduser()
    candidates = [raw]
    if not raw.is_absolute() and repo_root_placeholder and not is_placeholder(repo_root_placeholder):
        candidates.append(Path(repo_root_placeholder).expanduser() / raw_weights)
    return candidates


def existing_weight_path(raw_weights, repo_root_placeholder):
    for candidate in candidate_weight_paths(raw_weights, repo_root_placeholder):
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def any_candidate_is_dir(raw_weights, repo_root_placeholder):
    return any(candidate.exists() and candidate.is_dir() for candidate in candidate_weight_paths(raw_weights, repo_root_placeholder))


def infer_checkpoint_net(raw_weights):
    name = Path(raw_weights).name
    match = CHECKPOINT_NAME_RE.match(name)
    if match and match.group("net") in VALID_NETS:
        return match.group("net")
    # The repository training filename pattern is intentionally strict.
    return None


def infer_parent_net(raw_weights):
    parts = [part for part in Path(raw_weights).parts if part in VALID_NETS]
    return parts[-1] if parts else None


def validate(args):
    errors = []
    warnings = [
        "test.py may download CIFAR-100 into ./data relative to the command working directory.",
        "The weights file must be a plain state_dict for the same architecture selected by --net.",
    ]

    if not args.net:
        errors.append("--net is required unless --list-nets is used.")
    elif args.net not in VALID_NETS:
        errors.append("unsupported --net {!r}; use --list-nets to see valid names.".format(args.net))

    if args.batch_size <= 0:
        errors.append("--batch-size must be a positive integer.")

    resolved_weights = None
    if not args.weights:
        errors.append("--weights is required unless --list-nets is used.")
    else:
        if any_candidate_is_dir(args.weights, args.repo_root_placeholder):
            errors.append("--weights points to a directory; pass a checkpoint file path.")
        else:
            resolved_weights = existing_weight_path(args.weights, args.repo_root_placeholder)
            if resolved_weights is None:
                message = "weights path was not found"
                if args.allow_missing_weights:
                    warnings.append(message + "; command is being drafted with --allow-missing-weights.")
                else:
                    errors.append(message + "; pass --allow-missing-weights only when drafting a future command.")

        suffix = Path(args.weights).suffix.lower()
        if suffix and suffix != ".pth":
            warnings.append("weights path does not end in .pth; this is allowed only if it is still a torch state_dict file.")

        hinted_net = infer_checkpoint_net(args.weights)
        if hinted_net and args.net and hinted_net != args.net:
            warnings.append(
                "checkpoint filename looks like net {!r}, which differs from --net {!r}.".format(hinted_net, args.net)
            )
        parent_net = infer_parent_net(args.weights)
        if parent_net and args.net and parent_net != args.net:
            warnings.append(
                "checkpoint parent path contains net {!r}, which differs from --net {!r}.".format(parent_net, args.net)
            )

    if args.gpu:
        warnings.append("--gpu will make test.py call CUDA and print memory summaries; verify CUDA availability and memory first.")
    else:
        warnings.append("GPU is not requested; evaluation will use CPU unless test.py or the environment is modified.")

    if is_placeholder(args.repo_root_placeholder):
        warnings.append("replace the repo-root placeholder with the actual repository root before running the printed shell command.")

    return errors, warnings, resolved_weights


def make_parser():
    parser = argparse.ArgumentParser(
        description="Validate pytorch-cifar100 evaluation options and print a test.py command without executing it."
    )
    parser.add_argument("--net", help="network CLI name for test.py")
    parser.add_argument("--weights", help="path to a checkpoint state_dict file")
    parser.add_argument("--batch-size", type=int, default=16, help="test batch size for -b (default: 16)")
    parser.add_argument("--gpu", action="store_true", help="include -gpu in the printed command")
    parser.add_argument("--python", default="python", help="Python executable token to print (default: python)")
    parser.add_argument(
        "--repo-root-placeholder",
        default="<repo-root>",
        help="working-directory token for the printed cd command; use an empty string to omit cd",
    )
    parser.add_argument(
        "--allow-missing-weights",
        action="store_true",
        help="allow command drafting when --weights does not exist yet",
    )
    parser.add_argument("--explain", action="store_true", help="print validation notes and warnings")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit JSON instead of human text")
    parser.add_argument("--list-nets", action="store_true", help="print supported evaluator net names and exit")
    return parser


def emit_json(payload, exit_code):
    print(json_module.dumps(payload, indent=2, sort_keys=True))
    return exit_code


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.list_nets:
        if args.as_json:
            return emit_json({"valid_nets": list(VALID_NETS)}, 0)
        for net in VALID_NETS:
            print(net)
        return 0

    errors, warnings, resolved_weights = validate(args)
    command_argv = build_test_argv(args) if not errors else []
    shell_command = build_shell_command(args) if not errors else ""

    if args.as_json:
        return emit_json(
            {
                "ok": not errors,
                "errors": errors,
                "warnings": warnings,
                "valid_nets": list(VALID_NETS),
                "net": args.net,
                "weights": args.weights,
                "resolved_weights": str(resolved_weights) if resolved_weights is not None else None,
                "batch_size": args.batch_size,
                "gpu": args.gpu,
                "command_argv": command_argv,
                "shell_command": shell_command,
                "executes": False,
            },
            0 if not errors else 2,
        )

    if errors:
        for error in errors:
            print("error: {}".format(error), file=sys.stderr)
        print("hint: run with --list-nets to inspect supported net names.", file=sys.stderr)
        return 2

    print(shell_command)

    if args.explain:
        print("\nValidation:")
        print("- net {!r} is supported by the evaluator factory.".format(args.net))
        if resolved_weights is not None:
            print("- weights path exists: {}".format(resolved_weights))
        elif args.allow_missing_weights:
            print("- weights path does not exist yet, but missing weights were explicitly allowed.")
        print("- batch size: {}".format(args.batch_size))
        print("- GPU requested: {}".format(args.gpu))
        print("\nWarnings:")
        for warning in warnings:
            print("- {}".format(warning))
    else:
        for warning in warnings:
            print("warning: {}".format(warning), file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
