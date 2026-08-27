#!/usr/bin/env python3
"""Create a tiny fg-data-profiling report without network or repo examples.

Examples:
  python profile_dataframe_smoke.py --output-dir /tmp/fg-profile-smoke
  python profile_dataframe_smoke.py --output-dir /tmp/fg-profile-smoke --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a tiny ProfileReport HTML/JSON smoke output.")
    parser.add_argument("--output-dir", required=True, help="Directory where smoke outputs will be written.")
    parser.add_argument("--json", action="store_true", help="Also write and validate a JSON report.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
        from data_profiling import ProfileReport
    except ImportError as exc:
        print(
            "Missing dependency: install fg-data-profiling in this Python environment before running the smoke test.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    df = pd.DataFrame(
        {
            "amount": [10.0, 20.5, 20.5, None],
            "segment": ["retail", "enterprise", "enterprise", "trial"],
            "event_time": pd.date_range("2026-01-01", periods=4, freq="D"),
        }
    )

    try:
        profile = ProfileReport(df, title="fg-data-profiling smoke", minimal=True, progress_bar=False)
        html_path = out_dir / "profile-smoke.html"
        profile.to_file(html_path)
        if not html_path.exists() or html_path.stat().st_size == 0:
            print(f"HTML output was not created: {html_path}", file=sys.stderr)
            return 3

        payload = {"html": str(html_path), "html_size": html_path.stat().st_size}
        if args.json:
            json_path = out_dir / "profile-smoke.json"
            profile.to_file(json_path)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            missing = {"analysis", "table", "variables", "alerts", "package"} - set(data)
            if missing:
                print(f"JSON output missing expected keys: {sorted(missing)}", file=sys.stderr)
                return 4
            payload["json"] = str(json_path)
            payload["json_keys"] = sorted(data)

        print(json.dumps(payload, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - smoke diagnostic
        print(f"ProfileReport smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
