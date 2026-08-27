#!/usr/bin/env python3
"""Print read-only LMDB conversion plans for KAIR dataset families.

This script does not import KAIR and does not create LMDBs. It prints source
roots, target LMDB names, key conventions, and cautions distilled from KAIR's
data-preparation helpers.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class LmdbItem:
    label: str
    source: str
    target: str
    scan: str
    key: str
    notes: str = ""


@dataclass(frozen=True)
class DatasetPlan:
    title: str
    intent: str
    prerequisites: List[str]
    items: List[LmdbItem]
    cautions: List[str]
    final_checks: List[str]


PLANS: Dict[str, DatasetPlan] = {
    "div2k": DatasetPlan(
        title="DIV2K image subimages",
        intent="Create flat HR/LR patch LMDBs after subimage extraction for image SR training.",
        prerequisites=[
            "Original DIV2K HR and LR bicubic images are already extracted under trainsets/DIV2K/.",
            "Subimage folders such as DIV2K_train_HR_sub and X4_sub already exist.",
        ],
        items=[
            LmdbItem("HR", "trainsets/DIV2K/DIV2K_train_HR_sub", "trainsets/DIV2K/DIV2K_train_HR_sub.lmdb", "nonrecursive PNG", "filename stem, e.g. 0801_s001"),
            LmdbItem("LR x2", "trainsets/DIV2K/DIV2K_train_LR_bicubic/X2_sub", "trainsets/DIV2K/DIV2K_train_LR_bicubic_X2_sub.lmdb", "nonrecursive PNG", "filename stem with x2 removed before patch suffix"),
            LmdbItem("LR x3", "trainsets/DIV2K/DIV2K_train_LR_bicubic/X3_sub", "trainsets/DIV2K/DIV2K_train_LR_bicubic_X3_sub.lmdb", "nonrecursive PNG", "filename stem with x3 removed before patch suffix"),
            LmdbItem("LR x4", "trainsets/DIV2K/DIV2K_train_LR_bicubic/X4_sub", "trainsets/DIV2K/DIV2K_train_LR_bicubic_X4_sub.lmdb", "nonrecursive PNG", "filename stem with x4 removed before patch suffix"),
        ],
        cautions=[
            "KAIR's original subimage and LMDB writers exit if the target folder already exists.",
            "Subimage extraction writes many PNGs; confirm disk budget first.",
        ],
        final_checks=[
            "Compare HR and LR patch counts before conversion.",
            "After conversion, check each .lmdb has data.mdb, lock.mdb, and meta_info.txt.",
        ],
    ),
    "reds": DatasetPlan(
        title="REDS video SR/deblurring",
        intent="Create REDS LMDBs whose keys match VRT/RVRT training configs and meta-info files.",
        prerequisites=[
            "Clip folders are arranged as trainsets/REDS/train_sharp/<clip>/<frame>.png and corresponding LQ roots.",
            "If bicubic frames are under an X4 subdirectory, convert from the X4 directory or flatten keys deliberately.",
        ],
        items=[
            LmdbItem("GT sharp", "trainsets/REDS/train_sharp", "trainsets/REDS/train_sharp_with_val.lmdb", "recursive PNG", "clip/frame, e.g. 000/00000000"),
            LmdbItem("LR bicubic", "trainsets/REDS/train_sharp_bicubic", "trainsets/REDS/train_sharp_bicubic_with_val.lmdb", "recursive PNG", "clip/frame, not X4/clip/frame"),
            LmdbItem("Blur", "trainsets/REDS_blur/train_blur", "trainsets/REDS_blur/train_blur_with_val.lmdb", "recursive PNG", "clip/frame"),
            LmdbItem("Blur bicubic", "trainsets/REDS_blur_bicubic/train_blur_bicubic", "trainsets/REDS_blur_bicubic/train_blur_bicubic_with_val.lmdb", "recursive PNG", "clip/frame"),
        ],
        cautions=[
            "REDS regrouping copies validation folders with shell cp -r and can duplicate a large amount of data.",
            "Training configs exclude REDS4 clips 000, 011, 015, 020 when val_partition is REDS4.",
        ],
        final_checks=[
            "Check meta_info_REDS_GT.txt first-token clip names against LMDB key prefixes.",
            "Verify no unintended extra path component appears in LMDB meta_info.txt.",
        ],
    ),
    "vimeo90k": DatasetPlan(
        title="Vimeo90K VRT/RVRT",
        intent="Create all-frame GT/LQ LMDBs for Vimeo90K video SR, BD, and VFI workflows.",
        prerequisites=[
            "Clean sequences are under vimeo_septuplet/sequences/<clip>/<seq>/im1.png..im7.png.",
            "Bicubic and blur-downsampled LR sequences are already generated.",
            "sep_trainlist.txt and KAIR meta-info files exist.",
        ],
        items=[
            LmdbItem("GT all frames", "trainsets/vimeo90k/vimeo_septuplet/sequences", "trainsets/vimeo90k/vimeo90k_train_GT_all.lmdb", "train list, im1..im7", "clip/seq/imN"),
            LmdbItem("LR BI", "trainsets/vimeo90k/vimeo_septuplet_matlabLRx4/sequences", "trainsets/vimeo90k/vimeo90k_train_LR7frames.lmdb", "train list, im1..im7", "clip/seq/imN"),
            LmdbItem("LR BD", "trainsets/vimeo90k/vimeo_septuplet_BDLRx4/sequences", "trainsets/vimeo90k/vimeo90k_train_BDLR7frames.lmdb", "train list, im1..im7", "clip/seq/imN"),
        ],
        cautions=[
            "Some helper variants keep only im4 for GT; that is insufficient for configs that require GT_all.",
            "Source MATLAB LR-generation scripts are reference-only and may contain local absolute paths in the original repo.",
        ],
        final_checks=[
            "Check every listed sequence has im1.png through im7.png.",
            "Check meta_info_Vimeo90K_* files select the intended fast/medium/slow/all subsets.",
        ],
    ),
    "dvd": DatasetPlan(
        title="DVD video deblurring",
        intent="Create train_GT and train_GT_blurred LMDBs after arranging DVD quantitative data as clip folders.",
        prerequisites=[
            "Original quantitative_datasets clips have GT/ and input/ frame folders.",
            "A reviewed copy has been rearranged into train_GT and train_GT_blurred clip roots.",
        ],
        items=[
            LmdbItem("GT", "trainsets/DVD/train_GT", "trainsets/DVD/train_GT.lmdb", "recursive JPG", "clip/frame, e.g. 720p_240fps_1/00000"),
            LmdbItem("Blurred", "trainsets/DVD/train_GT_blurred", "trainsets/DVD/train_GT_blurred.lmdb", "recursive JPG", "clip/frame"),
        ],
        cautions=["The original DVD rearranger moves folders and removes original clip directories; run only on a copy."],
        final_checks=["Meta-info should use five-digit start frames and expected frame counts."],
    ),
    "gopro": DatasetPlan(
        title="GoPro video deblurring",
        intent="Create GoPro sharp/blurred LMDBs after moving sharp/blur folders into KAIR's train_GT layout.",
        prerequisites=["GoPro train/test clips have sharp/ and blur/ subfolders and have been reviewed before moving."],
        items=[
            LmdbItem("GT", "trainsets/GoPro/train_GT", "trainsets/GoPro/train_GT.lmdb", "recursive PNG", "clip/frame, e.g. GOPR0372_07_00/000047"),
            LmdbItem("Blurred", "trainsets/GoPro/train_GT_blurred", "trainsets/GoPro/train_GT_blurred.lmdb", "recursive PNG", "clip/frame"),
        ],
        cautions=["The original GoPro helper moves sharp/blur folders and deletes the original train/test folders."],
        final_checks=["Meta-info should use six-digit or source-matching start frames consistent with filename_tmpl."],
    ),
    "davis": DatasetPlan(
        title="DAVIS video denoising",
        intent="Create clean DAVIS GT LMDB for non-blind video denoising training.",
        prerequisites=["DAVIS clean frames are arranged as trainsets/DAVIS/train_GT/<clip>/<frame>.jpg."],
        items=[LmdbItem("GT clean", "trainsets/DAVIS/train_GT", "trainsets/DAVIS/train_GT.lmdb", "recursive JPG", "clip/frame, e.g. bear/00000")],
        cautions=["Denoising uses clean frames and injects noise; do not create a separate noisy LQ LMDB unless the config was changed."],
        final_checks=["Check meta_info_DAVIS_train_GT.txt and frame counts before long training."],
    ),
    "set8": DatasetPlan(
        title="Set8 testing",
        intent="Check Set8 frame folders for VRT/RVRT denoising tests; LMDB is normally not needed.",
        prerequisites=["Set8 test clips are frame folders under testsets/Set8."],
        items=[],
        cautions=["Use frame folders directly for testing. Do not create LMDB unless a custom training config asks for it."],
        final_checks=["Run the video layout checker on testsets/Set8 and use the same root for LQ and GT when noise is generated on the fly."],
    ),
}


def print_plan(plan: DatasetPlan) -> None:
    print(f"# {plan.title}")
    print()
    print(plan.intent)
    print()
    print("Prerequisites:")
    for item in plan.prerequisites:
        print(f"- {item}")
    print()
    if plan.items:
        print("LMDB conversion items:")
        for item in plan.items:
            print(f"- {item.label}")
            print(f"  source: {item.source}")
            print(f"  target: {item.target}")
            print(f"  scan: {item.scan}")
            print(f"  key convention: {item.key}")
            if item.notes:
                print(f"  notes: {item.notes}")
    else:
        print("LMDB conversion items: none for the normal KAIR path.")
    print()
    print("Cautions:")
    for item in plan.cautions:
        print(f"- {item}")
    print()
    print("Final read-only checks:")
    for item in plan.final_checks:
        print(f"- {item}")
    print()
    print("This is a plan only. To write an LMDB, use a reviewed KAIR checkout helper or a small script around KAIR's make_lmdb_from_imgs after confirming the source root and target are safe.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print read-only KAIR LMDB conversion plans.")
    parser.add_argument("--dataset", choices=sorted(PLANS), required=True, help="Dataset family to plan.")
    args = parser.parse_args()
    print_plan(PLANS[args.dataset])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
