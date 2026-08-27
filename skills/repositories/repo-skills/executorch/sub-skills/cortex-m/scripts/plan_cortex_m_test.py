#!/usr/bin/env python3
"""Plan Cortex-M validation commands without installing toolchains."""
from __future__ import annotations
import argparse, json


def main():
    ap = argparse.ArgumentParser(description="Plan Cortex-M dialect or implementation validation.")
    ap.add_argument("--mode", choices=["dialect", "implementation", "baremetal"], default="dialect")
    ap.add_argument("--model", default="<focused-test>")
    args = ap.parse_args()
    if args.mode == "dialect":
        command = ["python", "-m", "pytest", "<executorch-checkout>/backends/cortex_m/test", "-k", f"dialect and {args.model}", "-q"]
        prereq = "Python test dependencies; no FVP expected for dialect-only graph checks."
    elif args.mode == "implementation":
        command = ["python", "-m", "pytest", "<executorch-checkout>/backends/cortex_m/test", "-k", f"implementation and {args.model}", "-q"]
        prereq = "Arm toolchain/FVP setup and accepted licenses must already be available."
    else:
        command = ["<executorch-checkout>/backends/cortex_m/test/build_test_runner.sh"]
        prereq = "Bare-metal compiler/linker/toolchain setup must already be available."
    print(json.dumps({"mode": args.mode, "prerequisite": prereq, "command_template": command}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

