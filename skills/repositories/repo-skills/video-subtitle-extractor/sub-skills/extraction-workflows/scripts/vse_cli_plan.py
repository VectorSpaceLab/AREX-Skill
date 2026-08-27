#!/usr/bin/env python3
"""Create a safe VSE extraction plan without running OCR."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(description="Print a non-mutating plan for a VSE source CLI extraction run.")
    ap.add_argument("--video", required=True, help="Input video path intended for VSE.")
    ap.add_argument("--area", nargs=4, type=int, metavar=("YMIN", "YMAX", "XMIN", "XMAX"), help="Pixel subtitle area for backend.main prompt.")
    ap.add_argument("--language", default="en", help="VSE language code, e.g. ch, en, japan, korean, ar, ru.")
    ap.add_argument("--mode", choices=["fast", "auto", "accurate"], default="fast")
    ap.add_argument("--output", help="Desired SRT output path. If omitted, VSE defaults beside the video.")
    ap.add_argument("--generate-txt", action="store_true", help="Plan optional TXT output.")
    ap.add_argument("--json", action="store_true", help="Emit JSON.")
    args = ap.parse_args()
    video = Path(args.video)
    warnings = []
    for label, value in [("video", str(video)), ("output", args.output or "")]:
        if value and (" " in value or any(ord(ch) > 127 for ch in value)):
            warnings.append(f"{label} path contains spaces or non-ASCII characters; VSE README warns this can fail.")
    if not args.area:
        warnings.append("No subtitle area provided; backend.main may prompt for watermark/scene filtering and is unsuitable for automation.")
    plan = {
        "command": "python -m backend.main",
        "interactive_inputs": {
            "video_path": str(video),
            "subtitle_area_ymin_ymax_xmin_xmax": args.area,
        },
        "settings_to_confirm": {
            "language": args.language,
            "mode": args.mode,
            "generate_txt": args.generate_txt,
            "output": args.output or "<video stem>.srt beside input or configured save directory",
        },
        "preflight": [
            "Run the root vse_environment_probe.py in the VSE environment.",
            "Verify OpenCV can open the video and report FPS/frame count.",
            "Use Fast or Auto first; use Accurate only after accepting slow runtime.",
        ],
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print("VSE extraction plan (no OCR was run)")
        print("Command:", plan["command"])
        print("Prompt video path:", plan["interactive_inputs"]["video_path"])
        print("Prompt subtitle area:", plan["interactive_inputs"]["subtitle_area_ymin_ymax_xmin_xmax"])
        print("Settings to configure before launch:", plan["settings_to_confirm"])
        for warning in warnings:
            print("WARNING:", warning)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
