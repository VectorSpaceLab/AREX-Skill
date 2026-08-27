#!/usr/bin/env python3
"""Run a tiny local DataChain SDK pipeline smoke test.

The default smoke creates temporary files, then checks local CSV reading, typed
UDF output, dataset saving, read-back, and CSV export in an in-memory DataChain
session. No network, credentials, persistent DataChain root, or repository
checkout are required.

Examples:
  python local_io_smoke.py
  python local_io_smoke.py --show
"""

import argparse
import csv
import json
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a safe local DataChain SDK read/map/save/export smoke test."
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the read-back rows and exported CSV path as JSON.",
    )
    return parser


def import_datachain():
    try:
        import datachain as dc  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Could not import datachain. Install DataChain in the active Python "
            "environment before running this smoke test."
        ) from exc
    return dc


def run_smoke(show: bool = False) -> dict:
    dc = import_datachain()
    with tempfile.TemporaryDirectory(prefix="datachain-sdk-smoke-") as tmp:
        tmpdir = Path(tmp)
        csv_path = tmpdir / "items.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "score", "flag"])
            writer.writeheader()
            writer.writerows(
                [
                    {"path": "images/cat.jpg", "score": "9", "flag": "true"},
                    {"path": "images/dog.png", "score": "7", "flag": "false"},
                    {"path": "notes/readme.txt", "score": "2", "flag": "true"},
                ]
            )

        class ItemInfo(dc.DataModel):
            name: str
            ext: str
            high_score: bool

        def describe(path: str, score: int) -> ItemInfo:
            name = path.rsplit("/", 1)[-1]
            ext = name.rsplit(".", 1)[-1]
            return ItemInfo(name=name, ext=ext, high_score=score >= 8)

        with dc.Session(in_memory=True) as session:
            saved = (
                dc.read_csv(csv_path.as_uri(), session=session)
                .map(info=describe, params=["path", "score"])
                .save(
                    "sdk_smoke_items",
                    description="Temporary SDK smoke dataset.",
                    attrs=["smoke:test"],
                )
            )

            rows = (
                dc.read_dataset("sdk_smoke_items", session=session)
                .order_by("path")
                .to_list("path", "score", "flag", "info.name", "info.ext", "info.high_score")
            )
            expected = [
                ("images/cat.jpg", 9, True, "cat.jpg", "jpg", True),
                ("images/dog.png", 7, False, "dog.png", "png", False),
                ("notes/readme.txt", 2, True, "readme.txt", "txt", False),
            ]
            assert rows == expected, rows
            assert saved.count() == 3

            export_path = tmpdir / "export.csv"
            dc.read_dataset("sdk_smoke_items", session=session).order_by("path").to_csv(export_path)

        with export_path.open(newline="") as f:
            header = next(csv.reader(f))
        assert "info.name" in header and "info.high_score" in header, header
        if hasattr(dc.Session, "cleanup_for_tests"):
            dc.Session.cleanup_for_tests()

        result = {
            "status": "passed",
            "rows": rows,
            "export_header": header,
            "export_path": str(export_path),
        }
        if show:
            print(json.dumps(result, indent=2))
        else:
            print("DataChain SDK local IO smoke passed")
        return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_smoke(show=args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
