#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from typing import Dict, List, Sequence

IMG_EXTENSIONS = {
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".png",
    ".PNG",
    ".ppm",
    ".PPM",
    ".bmp",
    ".BMP",
    ".tiff",
    ".TIFF",
}

ROLE_SUFFIXES = {
    "label": ("_gtFine_labelIds", "_label", "_A"),
    "inst": ("_gtFine_instanceIds", "_inst"),
    "image": ("_leftImg8bit", "_img", "_B"),
}


class LayoutError(RuntimeError):
    pass


def fail(message: str, code: int = 2) -> int:
    print(message, file=sys.stderr)
    return code


def _supported_images(directory: Path) -> List[Path]:
    if not directory.is_dir():
        raise LayoutError(f"[layout-error] missing folder: {directory}")
    files = sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in IMG_EXTENSIONS
    )
    if not files:
        raise LayoutError(
            f"[layout-error] no supported images found in: {directory}\n"
            f"supported extensions: {', '.join(sorted(IMG_EXTENSIONS))}"
        )
    return files


def _canonical_id(path: Path, base_dir: Path, role: str) -> str:
    rel = path.relative_to(base_dir).as_posix()
    if path.suffix and rel.endswith(path.suffix):
        rel = rel[: -len(path.suffix)]
    for suffix in ROLE_SUFFIXES[role]:
        if rel.endswith(suffix):
            return rel[: -len(suffix)]
    return rel


def _describe_dir(role: str, phase: str, label_nc: int) -> str:
    if label_nc == 0:
        return f"{phase}_{'A' if role == 'label' else 'B' if role == 'image' else 'inst'}"
    if role == "label":
        return f"{phase}_label"
    if role == "inst":
        return f"{phase}_inst"
    return f"{phase}_img"


def _collect_role(base_dir: Path, role: str, phase: str, label_nc: int, required: bool) -> Dict[str, object] | None:
    directory = base_dir / _describe_dir(role, phase, label_nc)
    if not directory.exists():
        if required:
            convention = "<phase>_A and <phase>_B" if label_nc == 0 else "<phase>_label, <phase>_inst, and <phase>_img"
            raise LayoutError(
                f"[layout-error] missing folder: {directory}\n"
                f"expected naming convention: {convention}"
            )
        return None
    files = _supported_images(directory)
    ids = [_canonical_id(path, directory, role) for path in files]
    return {"directory": directory, "files": files, "ids": ids}


def validate_cityscapes_layout(
    repo_root: Path,
    phases: Sequence[str] = ("train", "test"),
    label_nc: int = 35,
    no_instance: bool = False,
    use_encoded_image: bool = False,
) -> Dict[str, object]:
    repo_root = Path(repo_root).expanduser().resolve()
    fixture_root = repo_root / "datasets" / "cityscapes"
    if not fixture_root.is_dir():
        raise LayoutError(
            f"[layout-error] missing bundled fixture root: {fixture_root}\n"
            "expected layout: datasets/cityscapes/{train_label,train_inst,train_img,test_label,test_inst}"
        )

    report: Dict[str, object] = {"repo_root": str(repo_root), "fixture_root": str(fixture_root), "phases": {}}

    for phase in phases:
        phase_report: Dict[str, object] = {}
        label_group = _collect_role(fixture_root, "label", phase, label_nc, required=True)
        inst_required = not no_instance
        inst_group = None if no_instance else _collect_role(fixture_root, "inst", phase, label_nc, required=inst_required)
        image_required = phase == "train" or use_encoded_image
        image_group = _collect_role(fixture_root, "image", phase, label_nc, required=image_required)

        phase_report["label"] = {
            "present": True,
            "directory": label_group["directory"],
            "count": len(label_group["files"]),
        }
        if no_instance:
            phase_report["inst"] = {"present": False, "count": 0, "skipped": True}
        else:
            phase_report["inst"] = {
                "present": True,
                "directory": inst_group["directory"],
                "count": len(inst_group["files"]),
            }

        if image_group is None:
            phase_report["image"] = {"present": False, "count": 0, "required": image_required}
        else:
            phase_report["image"] = {
                "present": True,
                "directory": image_group["directory"],
                "count": len(image_group["files"]),
                "required": image_required,
            }

        label_ids = label_group["ids"]
        role_ids = {"label": label_ids}
        role_counts = {"label": len(label_ids)}

        if not no_instance:
            inst_ids = inst_group["ids"]
            role_ids["inst"] = inst_ids
            role_counts["inst"] = len(inst_ids)
        if image_group is not None:
            img_ids = image_group["ids"]
            role_ids["image"] = img_ids
            role_counts["image"] = len(img_ids)

        if len(set(role_counts.values())) != 1:
            ordered = ", ".join(f"{role}={count}" for role, count in role_counts.items())
            raise LayoutError(f"[layout-error] sample-count mismatch in phase {phase}: {ordered}")

        reference_role = "label"
        reference_ids = role_ids[reference_role]
        for role, ids in role_ids.items():
            if ids != reference_ids:
                missing = [item for item in reference_ids if item not in ids]
                extra = [item for item in ids if item not in reference_ids]
                parts = []
                if missing:
                    parts.append(f"missing in {role}: {', '.join(missing[:3])}")
                if extra:
                    parts.append(f"extra in {role}: {', '.join(extra[:3])}")
                detail = "; ".join(parts) if parts else "file order mismatch"
                raise LayoutError(f"[layout-error] sample-id mismatch in phase {phase}: {detail}")

        report["phases"][phase] = phase_report

    return report


def print_report(report: Dict[str, object]) -> None:
    print(f"[ok] repo-root: {report['repo_root']}")
    print(f"[ok] fixture-root: {report['fixture_root']}")
    for phase, phase_report in report["phases"].items():
        label = phase_report["label"]["count"]
        inst = phase_report["inst"]
        image = phase_report["image"]
        if inst.get("skipped"):
            inst_text = "skipped (--no-instance)"
        else:
            inst_text = str(inst["count"])
        if image.get("present"):
            image_text = str(image["count"])
        else:
            image_text = "absent (optional)" if not image.get("required") else "absent (required)"
        print(f"[ok] {phase}: label={label} inst={inst_text} image={image_text}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the bundled Cityscapes-style folder layout for pix2pixHD.")
    parser.add_argument("--repo-root", required=True, help="Path to the pix2pixHD repository root.")
    parser.add_argument("--label-nc", type=int, default=35, help="Label-channel count used to choose label/image folder names.")
    parser.add_argument("--no-instance", action="store_true", help="Skip instance-folder checks when the dataset does not use instances.")
    parser.add_argument("--use-encoded-image", action="store_true", help="Require test-time image folders because encoded-image inference will use them.")
    parser.add_argument("--phases", nargs="+", default=["train", "test"], help="Phases to validate, usually train test.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = validate_cityscapes_layout(
            args.repo_root,
            phases=args.phases,
            label_nc=args.label_nc,
            no_instance=args.no_instance,
            use_encoded_image=args.use_encoded_image,
        )
        print_report(report)
        return 0
    except LayoutError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
