#!/usr/bin/env python3
"""Check SongMASS or TeleMelody asset layouts before heavyweight inference/training."""

from __future__ import annotations

import argparse
from pathlib import Path


def check_path(label: str, path: Path, expect_dir: bool | None = None) -> bool:
    exists = path.exists()
    kind_ok = True
    if exists and expect_dir is True:
        kind_ok = path.is_dir()
    if exists and expect_dir is False:
        kind_ok = path.is_file()
    status = "OK" if exists and kind_ok else "MISSING" if not exists else "WRONG-KIND"
    print(f"{status:10} {label}: {path}")
    return exists and kind_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SongMASS/TeleMelody paths without importing Fairseq or running models.")
    sub = parser.add_subparsers(dest="workflow", required=True)

    sm = sub.add_parser("songmass", help="Check SongMASS data/user-dir/checkpoint layout.")
    sm.add_argument("--data-dir", required=True, help="SongMASS data directory or binarized data prefix.")
    sm.add_argument("--user-dir", required=True, help="Path to the SongMASS Fairseq user module directory.")
    sm.add_argument("--model", required=True, help="Checkpoint path such as checkpoint_best.pt or songmass.pth.")
    sm.add_argument("--dict-lyric", default=None, help="Optional lyric dictionary path to check.")
    sm.add_argument("--dict-melody", default=None, help="Optional melody dictionary path to check.")

    tm = sub.add_parser("telemelody", help="Check TeleMelody inference asset prefixes.")
    tm.add_argument("--lyric2rhythm-prefix", required=True, help="Prefix/folder for lyric-to-rhythm checkpoint and data-bin files.")
    tm.add_argument("--template2melody-prefix", required=True, help="Prefix/folder for template-to-melody checkpoint and data-bin files.")
    tm.add_argument("--data-prefix", required=True, help="Input lyric/rhythm/template data prefix.")
    tm.add_argument("--save-prefix", required=True, help="Output prefix/directory that should be writable or creatable.")

    args = parser.parse_args()
    ok = True
    if args.workflow == "songmass":
        ok &= check_path("data-dir", Path(args.data_dir), None)
        ok &= check_path("user-dir", Path(args.user_dir), True)
        ok &= check_path("model", Path(args.model), False)
        if args.dict_lyric:
            ok &= check_path("dict-lyric", Path(args.dict_lyric), False)
        if args.dict_melody:
            ok &= check_path("dict-melody", Path(args.dict_melody), False)
        print("\nExpected next step: run the relevant SongMASS infer or train shell command only after Fairseq/Torch dependencies are prepared.")
    else:
        l2r = Path(args.lyric2rhythm_prefix)
        t2m = Path(args.template2melody_prefix)
        data = Path(args.data_prefix)
        save = Path(args.save_prefix)
        ok &= check_path("lyric2rhythm-prefix", l2r, None)
        ok &= check_path("template2melody-prefix", t2m, None)
        ok &= check_path("data-prefix", data, None)
        parent = save if save.suffix == "" else save.parent
        if not parent.exists():
            print(f"CREATE?    save-prefix parent: {parent}")
        else:
            print(f"OK         save-prefix parent: {parent}")
        print("\nExpected next step: run infer_en.py or infer_zh.py with these four prefixes in a compatible TeleMelody environment.")
    if not ok:
        print("\nResolve missing or wrong-kind paths before launching model code.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
