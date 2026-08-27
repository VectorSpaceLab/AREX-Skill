#!/usr/bin/env python3
"""Preflight StyleGAN-Human asset paths without downloads or model execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def exists(path: Path):
    return {"path": str(path), "exists": path.exists()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check asset files/directories required by StyleGAN-Human workflows.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Local DragGAN checkout containing stylegan_human/.")
    parser.add_argument("--pretrained-dir", type=Path, default=Path("stylegan_human/pretrained_models"))
    parser.add_argument("--check-alignment", action="store_true", help="Check OpenPose and PP-HumanSeg alignment assets.")
    parser.add_argument("--check-pti", action="store_true", help="Check PTI inversion assets and default config paths.")
    parser.add_argument("--check-editing", action="store_true", help="Check latent-direction assets used by edit.py.")
    parser.add_argument("--check-insetgan", action="store_true", help="Check dlib/FFHQ/face-body assets used by insetgan.py.")
    parser.add_argument("--training-data", type=Path, help="Optional SHHQ training dataset path to check.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = args.repo_root.expanduser().resolve()
    pretrained = args.pretrained_dir.expanduser()
    if not pretrained.is_absolute():
        pretrained = repo / pretrained

    checks = []
    checks.append({"workflow": "stylegan_human_root", **exists(repo / "stylegan_human")})
    checks.append({"workflow": "pretrained_dir", **exists(pretrained)})

    if args.check_alignment:
        checks.extend([
            {"workflow": "alignment_openpose_body_model", **exists(repo / "stylegan_human/openpose/model/body_pose_model.pth")},
            {"workflow": "alignment_pphumanseg_export", **exists(repo / "stylegan_human/PP_HumanSeg/export_model/deeplabv3p_resnet50_os8_humanseg_512x512_100k_with_softmax/deploy.yaml")},
            {"workflow": "alignment_pphumanseg_train_model", **exists(repo / "stylegan_human/PP_HumanSeg/pretrained_model/deeplabv3p_resnet50_os8_humanseg_512x512_100k")},
        ])
    if args.check_pti:
        checks.extend([
            {"workflow": "pti_e4e_weight", **exists(repo / "stylegan_human/pti/e4e_w+.pt")},
            {"workflow": "pti_default_shhq_pkl", **exists(pretrained / "stylegan_human_v2_1024.pkl")},
            {"workflow": "pti_default_input_data", **exists(repo / "stylegan_human/aligned_image")},
        ])
    if args.check_editing:
        checks.extend([
            {"workflow": "editing_interfacegan_upper", **exists(repo / "stylegan_human/latent_direction/ss/upper_length")},
            {"workflow": "editing_interfacegan_bottom", **exists(repo / "stylegan_human/latent_direction/ss/bottom_length")},
            {"workflow": "editing_stylespace_stats", **exists(repo / "stylegan_human/latent_direction/ss_statics")},
            {"workflow": "editing_sefa_upper", **exists(repo / "stylegan_human/latent_direction/sefa/upper_length.pt")},
            {"workflow": "editing_sefa_bottom", **exists(repo / "stylegan_human/latent_direction/sefa/bottom_length.pt")},
        ])
    if args.check_insetgan:
        checks.extend([
            {"workflow": "insetgan_body_pkl", **exists(pretrained / "stylegan_human_v2_1024.pkl")},
            {"workflow": "insetgan_face_pkl", **exists(pretrained / "ffhq.pkl")},
            {"workflow": "insetgan_dlib_landmarks", **exists(pretrained / "shape_predictor_68_face_landmarks.dat")},
            {"workflow": "insetgan_dlib_cnn_detector", **exists(pretrained / "mmod_human_face_detector.dat")},
        ])
    if args.training_data:
        data = args.training_data.expanduser()
        if not data.is_absolute():
            data = repo / data
        checks.append({"workflow": "training_data", **exists(data)})

    missing = [c for c in checks if not c["exists"]]
    payload = {"checks": checks, "missing": missing}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for c in checks:
            status = "OK" if c["exists"] else "MISSING"
            print(f"{status} {c['workflow']}: {c['path']}")
        if missing:
            print("Missing assets mean the corresponding workflow should be treated as preflight-blocked, not executed.")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
