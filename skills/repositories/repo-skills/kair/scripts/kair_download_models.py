#!/usr/bin/env python3
"""Dry-run-first KAIR model-zoo downloader.

By default this helper only prints the checkpoint URLs and destination paths. Add
--execute to download selected files. Avoid --models all unless disk and network
budget are explicit.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote

MODEL_GROUPS: Dict[str, List[str]] = {
    "DnCNN": ["dncnn_15.pth", "dncnn_25.pth", "dncnn_50.pth", "dncnn3.pth", "dncnn_color_blind.pth", "dncnn_gray_blind.pth"],
    "SRMD": ["srmdnf_x2.pth", "srmdnf_x3.pth", "srmdnf_x4.pth", "srmd_x2.pth", "srmd_x3.pth", "srmd_x4.pth"],
    "DPSR": ["dpsr_x2.pth", "dpsr_x3.pth", "dpsr_x4.pth", "dpsr_x4_gan.pth"],
    "FFDNet": ["ffdnet_color.pth", "ffdnet_gray.pth", "ffdnet_color_clip.pth", "ffdnet_gray_clip.pth"],
    "USRNet": ["usrgan.pth", "usrgan_tiny.pth", "usrnet.pth", "usrnet_tiny.pth"],
    "DPIR": ["drunet_gray.pth", "drunet_color.pth", "drunet_deblocking_color.pth", "drunet_deblocking_grayscale.pth"],
    "BSRGAN": ["BSRGAN.pth", "BSRNet.pth", "BSRGANx2.pth"],
    "IRCNN": ["ircnn_color.pth", "ircnn_gray.pth"],
    "SwinIR": [
        "001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth", "001_classicalSR_DF2K_s64w8_SwinIR-M_x3.pth",
        "001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth", "001_classicalSR_DF2K_s64w8_SwinIR-M_x8.pth",
        "001_classicalSR_DIV2K_s48w8_SwinIR-M_x2.pth", "001_classicalSR_DIV2K_s48w8_SwinIR-M_x3.pth",
        "001_classicalSR_DIV2K_s48w8_SwinIR-M_x4.pth", "001_classicalSR_DIV2K_s48w8_SwinIR-M_x8.pth",
        "002_lightweightSR_DIV2K_s64w8_SwinIR-S_x2.pth", "002_lightweightSR_DIV2K_s64w8_SwinIR-S_x3.pth", "002_lightweightSR_DIV2K_s64w8_SwinIR-S_x4.pth",
        "003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth", "003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_PSNR.pth",
        "004_grayDN_DFWB_s128w8_SwinIR-M_noise15.pth", "004_grayDN_DFWB_s128w8_SwinIR-M_noise25.pth", "004_grayDN_DFWB_s128w8_SwinIR-M_noise50.pth",
        "005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth", "005_colorDN_DFWB_s128w8_SwinIR-M_noise25.pth", "005_colorDN_DFWB_s128w8_SwinIR-M_noise50.pth",
        "006_CAR_DFWB_s126w7_SwinIR-M_jpeg10.pth", "006_CAR_DFWB_s126w7_SwinIR-M_jpeg20.pth", "006_CAR_DFWB_s126w7_SwinIR-M_jpeg30.pth", "006_CAR_DFWB_s126w7_SwinIR-M_jpeg40.pth",
    ],
    "VRT": [
        "001_VRT_videosr_bi_REDS_6frames.pth", "002_VRT_videosr_bi_REDS_16frames.pth", "003_VRT_videosr_bi_Vimeo_7frames.pth",
        "004_VRT_videosr_bd_Vimeo_7frames.pth", "005_VRT_videodeblurring_DVD.pth", "006_VRT_videodeblurring_GoPro.pth",
        "007_VRT_videodeblurring_REDS.pth", "008_VRT_videodenoising_DAVIS.pth", "009_VRT_videofi_Vimeo_4frames.pth",
    ],
    "RVRT": [
        "001_RVRT_videosr_bi_REDS_30frames.pth", "002_RVRT_videosr_bi_Vimeo_14frames.pth", "003_RVRT_videosr_bd_Vimeo_14frames.pth",
        "004_RVRT_videodeblurring_DVD_16frames.pth", "005_RVRT_videodeblurring_GoPro_16frames.pth", "006_RVRT_videodenoising_DAVIS_16frames.pth",
    ],
    "others": ["msrresnet_x4_psnr.pth", "msrresnet_x4_gan.pth", "imdn_x4.pth", "RRDB.pth", "ESRGAN.pth", "FSSR_DPED.pth", "FSSR_JPEG.pth", "RealSR_DPED.pth", "RealSR_JPEG.pth"],
}
ALL_MODELS = {name for group in MODEL_GROUPS.values() for name in group}


def split_models(text: str) -> List[str]:
    return [tok for tok in re.split(r"[\s,]+", text.strip()) if tok]


def destination(model_dir: Path, name: str) -> Path:
    if "SwinIR" in name:
        return model_dir / "swinir" / name
    if "_VRT_" in name:
        return model_dir / "vrt" / name
    if "_RVRT_" in name:
        return model_dir / "rvrt" / name
    return model_dir / name


def url_for(name: str) -> str:
    safe = quote(name)
    if "SwinIR" in name:
        return f"https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/{safe}"
    if "_VRT_" in name:
        return f"https://github.com/JingyunLiang/VRT/releases/download/v0.0/{safe}"
    if "_RVRT_" in name:
        return f"https://github.com/JingyunLiang/RVRT/releases/download/v0.0/{safe}"
    return f"https://github.com/cszn/KAIR/releases/download/v1.0/{safe}"


def expand_tokens(tokens: Iterable[str], allow_all: bool) -> List[str]:
    expanded: List[str] = []
    for token in tokens:
        if token == "all":
            if not allow_all:
                raise SystemExit("Refusing --models all without --allow-all. Choose specific groups/models or confirm disk/network budget.")
            for group in MODEL_GROUPS.values():
                expanded.extend(group)
        elif token in MODEL_GROUPS:
            expanded.extend(MODEL_GROUPS[token])
        elif token in ALL_MODELS:
            expanded.append(token)
        else:
            print(f"WARN: unknown model or group: {token}")
    # preserve order while removing duplicates
    result: List[str] = []
    seen = set()
    for item in expanded:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def download(url: str, dest: Path, timeout: int) -> None:
    import requests  # imported only when --execute is used

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        tmp.replace(dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run-first KAIR checkpoint downloader.")
    parser.add_argument("--models", default="dncnn_25.pth", help="Space/comma-separated groups or filenames, e.g. 'DnCNN BSRGAN.pth'.")
    parser.add_argument("--model-dir", type=Path, default=Path("model_zoo"), help="Destination model_zoo root.")
    parser.add_argument("--execute", action="store_true", help="Actually download files. Without this flag, only print the plan.")
    parser.add_argument("--allow-all", action="store_true", help="Allow --models all.")
    parser.add_argument("--timeout", type=int, default=60, help="Per-request timeout in seconds for --execute.")
    args = parser.parse_args()

    selected = expand_tokens(split_models(args.models), args.allow_all)
    if not selected:
        print("No known models selected.")
        return 1
    for name in selected:
        dest = destination(args.model_dir, name)
        url = url_for(name)
        status = "exists" if dest.exists() else "missing"
        print(f"{name}\n  url: {url}\n  dest: {dest}\n  status: {status}")
        if args.execute:
            if dest.exists():
                print("  action: skip existing")
            else:
                print("  action: downloading")
                download(url, dest, args.timeout)
                print("  action: done")
    if not args.execute:
        print("\nDry run only. Re-run with --execute to download selected files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
