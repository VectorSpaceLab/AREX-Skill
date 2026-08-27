#!/usr/bin/env python3
"""Run an explicitly authorized, bounded Bell smoke test against a local QVM.

This helper never starts qvm/quilc, never selects a QPU, and never loads QCS
credentials. Without --execute it only prints the prerequisite boundary. With
--execute it constructs an explicit local QCSClient, compiles before running,
and asserts the register shape and Bell-state bit correlation.

Examples:
  python qvm_bell_smoke.py --help
  python qvm_bell_smoke.py
  python qvm_bell_smoke.py --execute --shots 32 --compiler-timeout 5 --execution-timeout 5
"""

from __future__ import annotations

import argparse
import sys


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="explicitly opt in to a local QVM/quilc compile and execution request",
    )
    parser.add_argument("--shots", type=int, default=32, help="Bell shots, 1..10000 (default: 32)")
    parser.add_argument(
        "--compiler-timeout", type=float, default=5.0, help="quilc request timeout in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--execution-timeout", type=float, default=5.0, help="QVM request timeout in seconds (default: 5.0)"
    )
    parser.add_argument("--qvm-url", default="http://127.0.0.1:5000", help="local QVM URL")
    parser.add_argument("--quilc-url", default="tcp://127.0.0.1:5555", help="local quilc URL")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not 1 <= args.shots <= 10_000:
        parser.error("--shots must be between 1 and 10000")
    if not 0 < args.compiler_timeout <= 300:
        parser.error("--compiler-timeout must be > 0 and <= 300 seconds")
    if not 0 < args.execution_timeout <= 300:
        parser.error("--execution-timeout must be > 0 and <= 300 seconds")

    if not args.execute:
        print("NOT RUN: pass --execute to opt in to local qvm/quilc network requests.")
        print("Prerequisites: qvm and quilc must already be running at the selected URLs.")
        print("This helper will not start services or load QPU credentials.")
        return 0

    try:
        import numpy as np
        from qcs_sdk import QCSClient
        from qcs_sdk.compiler.quilc import QuilcClient
        from qcs_sdk.qvm import QVMClient
        from pyquil import Program, get_qc
        from pyquil.gates import CNOT, H, MEASURE
    except Exception as exc:
        print(f"ERROR: required pyQuil/QCS imports failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Install a compatible pyQuil environment before retrying; no service was contacted.", file=sys.stderr)
        return 2

    try:
        # Explicit URLs avoid QCSClient.load(), profile discovery, and QPU
        # credential use. get_qc is forced to the generic service-backed QVM.
        client = QCSClient(qvm_url=args.qvm_url, quilc_url=args.quilc_url)
        qc = get_qc(
            "2q-qvm",
            client_configuration=client,
            qvm_client=QVMClient.new_http(args.qvm_url),
            quilc_client=QuilcClient.new_rpcq(args.quilc_url),
            compiler_timeout=args.compiler_timeout,
            execution_timeout=args.execution_timeout,
        )

        program = Program()
        ro = program.declare("ro", "BIT", 2)
        program += H(0)
        program += CNOT(0, 1)
        program += MEASURE(0, ro[0])
        program += MEASURE(1, ro[1])
        program.wrap_in_numshots_loop(args.shots)

        # Deliberately separate the lifecycle: compile first, then run the
        # returned executable. No source Program is passed to qc.run here.
        executable = qc.compile(program)
        result = qc.run(executable)
        bits = result.get_register_map().get("ro")
        if bits is None:
            raise AssertionError("QVM returned no 'ro' register")
        if bits.shape != (args.shots, 2):
            raise AssertionError(f"expected ro shape {(args.shots, 2)}, got {bits.shape}")
        if not np.all((bits == 0) | (bits == 1)):
            raise AssertionError("ro contains values outside the BIT domain {0, 1}")
        if not np.all(bits[:, 0] == bits[:, 1]):
            raise AssertionError("Bell correlation assertion failed: ro columns differ")
    except Exception as exc:
        print(f"ERROR: local QVM Bell smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check that qvm and quilc are already running, that --qvm-url/--quilc-url "
            "match their listeners, and that their versions are compatible. "
            "This is not a QPU or credential failure path.",
            file=sys.stderr,
        )
        return 2

    print(f"PASS: compiled and ran {args.shots} Bell shots on the explicitly selected local QVM.")
    print("PASS: ro shape and bit-for-bit correlation assertions succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
