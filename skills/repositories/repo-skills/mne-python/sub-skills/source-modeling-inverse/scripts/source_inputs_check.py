#!/usr/bin/env python3
"""Validate common MNE-Python source-modeling input paths without heavy compute.

This helper checks that paths needed for source-space, BEM, forward, inverse,
and morphing workflows exist and look like the expected artifact type. It does
not import the original MNE-Python repository and does not run FreeSurfer,
OpenMEEG, or any expensive modeling command.

Example:
    python source_inputs_check.py --trans sample-trans.fif --src sample-src.fif \
        --bem sample-bem-sol.fif --cov sample-cov.fif --subject sample \
        --subjects-dir subjects
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _check_path(label: str, value: str | None, suffix_hints: tuple[str, ...]) -> tuple[bool, str]:
    if not value:
        return True, f"{label}: not provided"
    path = Path(value).expanduser()
    if not path.exists():
        return False, f"{label}: missing path {path}"
    if suffix_hints and not any(str(path).endswith(suffix) for suffix in suffix_hints):
        return False, f"{label}: exists but suffix is unusual for {suffix_hints}: {path.name}"
    return True, f"{label}: ok ({path})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trans", help="Head<->MRI transform, typically *-trans.fif")
    parser.add_argument("--src", help="Source space file, typically *-src.fif")
    parser.add_argument("--bem", help="BEM solution/model, typically *-bem-sol.fif or *-bem.fif")
    parser.add_argument("--forward", help="Forward solution, typically *-fwd.fif")
    parser.add_argument("--cov", help="Noise/data covariance, typically *-cov.fif")
    parser.add_argument("--inverse", help="Inverse operator, typically *-inv.fif")
    parser.add_argument("--stc", help="SourceEstimate basename or file, e.g. *-lh.stc, *.h5")
    parser.add_argument("--subjects-dir", help="Directory containing FreeSurfer subjects")
    parser.add_argument("--subject", help="Subject name expected inside --subjects-dir")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for missing optional inputs too")
    args = parser.parse_args()

    checks = [
        _check_path("trans", args.trans, ("-trans.fif", ".fif")),
        _check_path("src", args.src, ("-src.fif", ".fif")),
        _check_path("bem", args.bem, ("-bem-sol.fif", "-bem.fif", ".fif")),
        _check_path("forward", args.forward, ("-fwd.fif", ".fif")),
        _check_path("cov", args.cov, ("-cov.fif", ".fif")),
        _check_path("inverse", args.inverse, ("-inv.fif", ".fif")),
    ]
    if args.stc:
        checks.append(_check_path("stc", args.stc, ("-lh.stc", "-rh.stc", ".h5", ".w", ".stc")))

    ok = True
    for passed, message in checks:
        ok = ok and passed
        print(("OK" if passed else "FAIL") + " " + message)

    if args.subjects_dir:
        subjects_dir = Path(args.subjects_dir).expanduser()
        if not subjects_dir.exists():
            ok = False
            print(f"FAIL subjects_dir: missing path {subjects_dir}")
        elif args.subject and not (subjects_dir / args.subject).exists():
            ok = False
            print(f"FAIL subject: {args.subject!r} not found under {subjects_dir}")
        else:
            detail = f"subject {args.subject!r}" if args.subject else "no subject requested"
            print(f"OK subjects_dir: {subjects_dir} ({detail})")
    elif args.subject:
        ok = False
        print("FAIL subject: --subject was provided without --subjects-dir")
    else:
        print("OK subjects_dir: not provided")

    provided = any(getattr(args, name) for name in ("trans", "src", "bem", "forward", "cov", "inverse", "stc"))
    if not provided and args.strict:
        ok = False
        print("FAIL strict: no source-modeling artifact paths were provided")

    if ok:
        print("Source input check passed. This does not prove the model is scientifically valid.")
        return 0
    print("Source input check failed. Provide/fix the reported inputs before heavy source modeling.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
