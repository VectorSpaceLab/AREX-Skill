"""
Decompiler postscript used to dump pseudo-code for every discovered function.
The repo's source examples label this route as Ghidra-facing, but the helper
imports IDA/Hex-Rays-style APIs and must be paired with the matching backend.
"""

from __future__ import annotations

import os
import sys

import ida_auto  # type: ignore
import ida_funcs  # type: ignore
import ida_hexrays  # type: ignore
import ida_pro  # type: ignore
import idautils  # type: ignore
import idc  # type: ignore


def _get_output_path() -> str:
    if len(idc.ARGV) < 2:
        raise RuntimeError("output path argument missing")
    return os.path.abspath(idc.ARGV[1])


def main() -> None:
    try:
        output_path = _get_output_path()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[dump_pseudo] {exc}", file=sys.stderr)
        ida_pro.qexit(1)
        return

    ida_auto.auto_wait()

    if not ida_hexrays.init_hexrays_plugin():
        print("[dump_pseudo] Hex-Rays decompiler is unavailable", file=sys.stderr)
        ida_pro.qexit(1)
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as handle:
        for ea in idautils.Functions():
            name = ida_funcs.get_func_name(ea)
            handle.write(f"/* {name} @ 0x{ea:x} */\n")
            try:
                cfunc = ida_hexrays.decompile(ea)
            except ida_hexrays.DecompilationFailure as exc:
                handle.write(f"// decompilation failed: {exc}\n\n")
                continue

            handle.write(str(cfunc))
            handle.write("\n\n")

    ida_pro.qexit(0)


if __name__ == "__main__":
    main()
