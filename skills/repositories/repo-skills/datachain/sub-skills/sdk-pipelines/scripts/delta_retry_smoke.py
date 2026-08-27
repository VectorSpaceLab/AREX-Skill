#!/usr/bin/env python3
"""Explain or run a tiny DataChain delta/retry contract smoke.

Default mode is read-only explanation because real delta pipelines depend on a
saved dataset history. Pass --run-demo to create a temporary local fixture and
run a minimal file-processing pipeline twice in an in-memory DataChain session.
No network, credentials, or repository checkout are required.

Examples:
  python delta_retry_smoke.py
  python delta_retry_smoke.py --run-demo --show
"""

import argparse
import json
import tempfile
from pathlib import Path

EXPLANATION = """\
DataChain delta/retry contract:
- `delta=True` narrows a source to new or changed records relative to the prior
  source version used by the result dataset.
- `delta_on` identifies logical records, commonly `file.path`.
- `delta_compare` identifies modifications, commonly `file.etag`, `file.version`,
  or a modified timestamp.
- `delta_retry` reprocesses rows missing from the result or rows whose selected
  error field is populated.
- Do not combine delta casually with merge/union/subtract/diff/file_diff,
  distinct, agg, or group_by. Use `delta_unsafe=True` only after reasoning about
  replaying a subset through the full query.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explain DataChain delta/retry or run a tiny local demo."
    )
    parser.add_argument(
        "--run-demo",
        action="store_true",
        help="Create a temporary local file fixture and run a tiny delta pipeline twice.",
    )
    parser.add_argument("--show", action="store_true", help="Print JSON demo details.")
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


def run_demo(show: bool = False) -> dict:
    with tempfile.TemporaryDirectory(prefix="datachain-delta-smoke-") as tmp:
        tmpdir = Path(tmp)
        data_dir = tmpdir / "data"
        data_dir.mkdir()
        (data_dir / "a.txt").write_text("alpha", encoding="utf-8")
        (data_dir / "b.txt").write_text("beta", encoding="utf-8")

        dc = import_datachain()

        class Processed(dc.DataModel):
            text: str
            error: str | None = None

        def process(file: dc.TextFile) -> Processed:
            try:
                return Processed(text=file.read())
            except Exception as exc:
                return Processed(text="", error=str(exc))

        with dc.Session(in_memory=True) as session:
            def build_and_save():
                return (
                    dc.read_storage(
                        data_dir.as_uri() + "/",
                        type="text",
                        session=session,
                        update=True,
                        delta=True,
                        delta_on="file.path",
                        delta_compare="file.etag",
                        delta_retry="result.error",
                    )
                    .map(result=process)
                    .save("delta_retry_smoke")
                )

            first = build_and_save()
            first_rows = first.order_by("file.path").to_list("file.path", "result.text")
            assert first_rows == [("a.txt", "alpha"), ("b.txt", "beta")], first_rows

            (data_dir / "c.txt").write_text("gamma", encoding="utf-8")
            second = build_and_save()
            second_rows = second.order_by("file.path").to_list("file.path", "result.text")
            assert ("c.txt", "gamma") in second_rows, second_rows

        if hasattr(dc.Session, "cleanup_for_tests"):
            dc.Session.cleanup_for_tests()
        result = {
            "status": "passed",
            "first_rows": first_rows,
            "second_rows": second_rows,
            "note": "Temporary fixture verified delta-enabled pipeline shape; backend/service delta behavior still depends on the selected storage backend.",
        }
        if show:
            print(json.dumps(result, indent=2))
        else:
            print("DataChain delta/retry local demo passed")
        return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.run_demo:
        print(EXPLANATION)
        return 0
    run_demo(show=args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
