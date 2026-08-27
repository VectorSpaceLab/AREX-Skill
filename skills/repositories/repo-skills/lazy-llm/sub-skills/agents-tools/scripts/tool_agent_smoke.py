#!/usr/bin/env python3
"""No-network LazyLLM tool registration smoke check."""
from __future__ import annotations

import argparse
import json
from typing import Dict


def run() -> Dict[str, object]:
    import lazyllm
    from lazyllm.tools import ToolManager, fc_register

    @fc_register("tool", execute_in_sandbox=False, input_files_parm="input_path", output_files_parm="output_path", output_files=["report.txt"])
    def lazyllm_skill_tool_smoke(input_path: str, output_path: str):
        """Smoke tool that echoes an output path.

        Args:
            input_path: Path to a local input file.
            output_path: Path where a report would be written.
        """
        return output_path

    tool = lazyllm.tool.lazyllm_skill_tool_smoke()
    assert tool.execute_in_sandbox is False
    assert tool.input_files_parm == "input_path"
    assert tool.output_files_parm == "output_path"
    assert tool.output_files == ["report.txt"]

    manager = ToolManager([lazyllm_skill_tool_smoke])
    return {
        "tool_name": getattr(tool, "name", "lazyllm_skill_tool_smoke"),
        "execute_in_sandbox": tool.execute_in_sandbox,
        "input_files_parm": tool.input_files_parm,
        "output_files_parm": tool.output_files_parm,
        "output_files": tool.output_files,
        "tool_manager_type": type(manager).__name__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe LazyLLM tool registration smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
