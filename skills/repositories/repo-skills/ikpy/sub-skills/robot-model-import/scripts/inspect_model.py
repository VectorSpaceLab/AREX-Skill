#!/usr/bin/env python3
"""Read-only inspection of an IKPy URDF or MJCF model.

The command parses the supplied XML, prints source and imported chain names,
and optionally computes zero-configuration FK. It never renders or writes a
file. The IKPy package must be installed in the executing Python environment.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence


def _bool_value(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean mask value: {value!r}")


def _mask_values(values: Sequence[str] | None) -> list[bool] | None:
    if values is None:
        return None
    result: list[bool] = []
    for value in values:
        for item in value.split(","):
            if item.strip():
                result.append(_bool_value(item))
    if not result:
        raise ValueError("--active-mask must contain at least one boolean")
    return result


def _detect_format(path: Path, requested: str) -> tuple[str, ET.Element]:
    tree = ET.parse(path)
    root = tree.getroot()
    if requested != "auto":
        return requested, root
    if root.tag == "mujoco":
        return "mjcf", root
    if root.tag == "robot":
        return "urdf", root
    suffix = path.suffix.lower()
    if suffix in {".xml", ".mjcf", ".mjb"}:
        return "mjcf", root
    return "urdf", root


def _build_chain(args: argparse.Namespace, model_format: str):
    from ikpy.chain import Chain

    common = {
        "last_link_vector": args.last_link_vector,
        "active_links_mask": _mask_values(args.active_mask),
        "symbolic": not args.no_symbolic,
    }
    if model_format == "urdf":
        common["base_elements"] = args.base_elements
        common["base_element_type"] = args.base_element_type
        return Chain.from_urdf_file(str(args.model), **common)
    if args.base_element_type != "link":
        raise ValueError("--base-element-type applies only to URDF models")
    common.pop("base_element_type", None)
    return Chain.from_mjcf_file(str(args.model), **common)


def _print_source(model_format: str, root: ET.Element) -> None:
    if model_format == "urdf":
        links = [element.get("name", "<unnamed>") for element in root.findall("link")]
        joints = [element.get("name", "<unnamed>") for element in root.findall("joint")]
        print(f"source_root: {root.tag}")
        print(f"source_links ({len(links)}): {links}")
        print(f"source_joints ({len(joints)}): {joints}")
        return

    worldbody = root.find("worldbody")
    bodies = []
    joints = []
    if worldbody is not None:
        bodies = [
            body.get("name", "<unnamed>")
            for body in worldbody.iter("body")
        ]
        joints = [
            joint.get("name", "<unnamed>")
            for joint in worldbody.iter("joint")
        ]
    print(f"source_root: {root.tag}")
    print(f"source_bodies ({len(bodies)}): {bodies}")
    print(f"source_joints ({len(joints)}): {joints}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="URDF or MJCF XML file to inspect")
    parser.add_argument(
        "--format",
        choices=("auto", "urdf", "mjcf"),
        default="auto",
        help="input format; auto uses the XML root tag and then the suffix",
    )
    parser.add_argument(
        "--base-elements",
        nargs="+",
        help="ordered URDF link/joint path or MJCF body path",
    )
    parser.add_argument(
        "--base-element-type",
        choices=("link", "joint"),
        default="link",
        help="type of the first URDF base element (ignored for MJCF)",
    )
    parser.add_argument(
        "--last-link-vector",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        help="fixed three-component tip translation",
    )
    parser.add_argument(
        "--active-mask",
        nargs="+",
        metavar="BOOL",
        help="optional booleans (for example: false true false or false,true,false)",
    )
    parser.add_argument(
        "--no-symbolic",
        action="store_true",
        help="construct numeric NumPy transforms instead of SymPy-lambdified transforms",
    )
    parser.add_argument("--fk", action="store_true", help="compute zero-configuration FK")
    parser.add_argument(
        "--full-fk",
        action="store_true",
        help="with --fk, print the number and shape of every intermediate frame",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        model_format, root = _detect_format(args.model, args.format)
        print(f"format: {model_format}")
        print(f"path: {args.model}")
        _print_source(model_format, root)
        chain = _build_chain(args, model_format)
        print(f"chain_name: {chain.name}")
        print(f"chain_links: {len(chain.links)}")
        print(f"active_mask ({len(chain.active_links_mask)}): {chain.active_links_mask.tolist()}")
        for index, link in enumerate(chain.links):
            print(
                f"link[{index}]: name={link.name!r} "
                f"joint_type={link.joint_type!r} bounds={tuple(link.bounds)!r}"
            )
        if args.fk or args.full_fk:
            values = [0.0] * len(chain.links)
            fk = chain.forward_kinematics(values, full_kinematics=args.full_fk)
            if args.full_fk:
                print(f"fk_frames: {len(fk)}")
                print(f"fk_frame_shapes: {[tuple(frame.shape) for frame in fk]}")
            else:
                print(f"fk_shape: {tuple(fk.shape)}")
        return 0
    except (OSError, ET.ParseError, ImportError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep this diagnostic CLI from emitting a traceback by default.
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
