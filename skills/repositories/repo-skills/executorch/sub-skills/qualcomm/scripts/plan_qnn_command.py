#!/usr/bin/env python3
"""Print a safe QNN command plan without running SDK/device commands."""
from __future__ import annotations
import argparse, json, os


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan ExecuTorch QNN build/test command inputs.")
    ap.add_argument("--soc", required=True, help="Target Qualcomm SoC model, e.g. SM8750.")
    ap.add_argument("--build-dir", default="build-android")
    ap.add_argument("--artifact-dir", default="qnn-artifacts")
    ap.add_argument("--device", help="Optional Android device serial.")
    ap.add_argument("--host", help="Optional host address for device tests.")
    ap.add_argument("--x86", action="store_true", help="Plan x86 local execution/compile mode when supported.")
    ap.add_argument("--compile-only", action="store_true")
    args = ap.parse_args()
    required_env = ["QNN_SDK_ROOT", "ANDROID_NDK_ROOT or ANDROID_NDK"]
    test_cmd = ["python", "<qnn-test-or-example>.py", "-m", args.soc, "-b", args.build_dir, "-a", args.artifact_dir]
    if args.device:
        test_cmd += ["-s", args.device]
    if args.host:
        test_cmd += ["-H", args.host]
    if args.x86:
        test_cmd.append("-x")
    if args.compile_only:
        test_cmd.append("-c")
    report = {
        "required_env": required_env,
        "observed_env": {k: os.environ.get(k) for k in ["QNN_SDK_ROOT", "ANDROID_NDK_ROOT", "ANDROID_NDK"] if os.environ.get(k)},
        "build_plan": "Run the QNN backend build script in the user's checkout with the selected x86/Android/direct mode after SDK paths are confirmed.",
        "test_command_template": test_cmd,
        "notes": ["This planner does not run builds or touch devices.", "Replace <qnn-test-or-example>.py with the focused QNN test/example for the user's model."],
    }
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

