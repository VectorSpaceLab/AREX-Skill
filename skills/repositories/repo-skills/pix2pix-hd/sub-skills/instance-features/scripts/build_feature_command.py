#!/usr/bin/env python3
"""Dry-run command builder for pix2pixHD feature workflows.

The script prints the feature-aware command sequence for the repo's bundled
`*feat*.sh` recipes. It does not launch training, clustering, or inference.
"""
from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import List, Sequence, Tuple

DEFAULT_512P_NAME = "label2city_512p_feat"
DEFAULT_1024P_NAME = "label2city_1024p_feat"
DEFAULT_N_CLUSTERS = 10
DEFAULT_FEAT_NUM = 3
DEFAULT_GPU_IDS = "0"
DEFAULT_DATAROOT = Path("datasets") / "cityscapes"
DEFAULT_CHECKPOINTS_DIR = Path("checkpoints")


def shell_join(parts: Sequence[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None and str(part) != "")



def resolve_path(base: Path, override: str | None, fallback: Path) -> Path:
    if override:
        return base / override
    return base / fallback


def common_flags(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> List[str]:
    flags: List[str] = [
        "--dataroot",
        str(dataroot),
        "--checkpoints_dir",
        str(checkpoints_dir),
        "--gpu_ids",
        args.gpu_ids,
        "--feat_num",
        str(args.feat_num),
    ]
    return flags


def repo_script(args: argparse.Namespace, script_name: str) -> str:
    return str(Path(args.repo_root) / script_name)


def cluster_filename(args: argparse.Namespace) -> str:
    if args.cluster_path:
        return args.cluster_path
    return f"features_clustered_{args.n_clusters:03d}.npy"


def build_train_512p(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    name = args.name or DEFAULT_512P_NAME
    commands = [["python", repo_script(args, "train.py"), "--name", name, *common_flags(args, dataroot, checkpoints_dir), "--instance_feat"]]
    notes = [
        "512p feature training keeps the stock feature encoder active",
    ]
    return commands, notes, False


def build_train_1024p_12g(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    source_name = args.source_name or DEFAULT_512P_NAME
    target_name = args.target_name or args.name or DEFAULT_1024P_NAME
    precompute_cmd = ["python", repo_script(args, "precompute_feature_maps.py"), "--name", source_name, *common_flags(args, dataroot, checkpoints_dir)]
    train_cmd = [
        "python",
        repo_script(args, "train.py"),
        "--name",
        target_name,
        "--netG",
        "local",
        "--ngf",
        "32",
        "--num_D",
        "3",
        "--load_pretrain",
        str(checkpoints_dir / source_name),
        "--niter_fix_global",
        "20",
        "--resize_or_crop",
        "crop",
        "--fineSize",
        "896",
        *common_flags(args, dataroot, checkpoints_dir),
        "--instance_feat",
        "--load_features",
    ]
    notes = [
        f"precompute feature maps from {source_name} before the target run",
        "the target 1024p run consumes `train_feat/` and does not build a new encoder",
    ]
    return [precompute_cmd, train_cmd], notes, False


def build_train_1024p_24g(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    source_name = args.source_name or DEFAULT_512P_NAME
    target_name = args.target_name or args.name or DEFAULT_1024P_NAME
    precompute_cmd = ["python", repo_script(args, "precompute_feature_maps.py"), "--name", source_name, *common_flags(args, dataroot, checkpoints_dir)]
    train_cmd = [
        "python",
        repo_script(args, "train.py"),
        "--name",
        target_name,
        "--netG",
        "local",
        "--ngf",
        "32",
        "--num_D",
        "3",
        "--load_pretrain",
        str(checkpoints_dir / source_name),
        "--niter",
        "50",
        "--niter_decay",
        "50",
        "--niter_fix_global",
        "10",
        "--resize_or_crop",
        "none",
        *common_flags(args, dataroot, checkpoints_dir),
        "--instance_feat",
        "--load_features",
    ]
    notes = [
        f"precompute feature maps from {source_name} before the target run",
        "this is the full-resolution feature-conditioned schedule from the source repo",
    ]
    return [precompute_cmd, train_cmd], notes, False


def build_encode(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path, *, is_1024p: bool = False) -> Tuple[List[List[str]], List[str], bool]:
    if is_1024p:
        name = args.name or args.target_name or DEFAULT_1024P_NAME
    else:
        name = args.name or DEFAULT_512P_NAME
    cmd = [
        "python",
        repo_script(args, "encode_features.py"),
        "--name",
        name,
        "--n_clusters",
        str(args.n_clusters),
        *common_flags(args, dataroot, checkpoints_dir),
    ]
    if is_1024p:
        cmd.extend(["--netG", "local", "--ngf", "32", "--resize_or_crop", "none"])
    notes = [
        "KMeans from scikit-learn is required for this stage",
    ]
    if is_1024p:
        notes.append("the 1024p encode command needs the local-enhancer flags shown in scripts/test_1024p_feat.sh")
    return [cmd], notes, True


def build_test_512p(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    name = args.name or DEFAULT_512P_NAME
    cluster_path = cluster_filename(args)
    encode_cmd = [
        "python",
        repo_script(args, "encode_features.py"),
        "--name",
        name,
        "--n_clusters",
        str(args.n_clusters),
        *common_flags(args, dataroot, checkpoints_dir),
    ]
    test_cmd = [
        "python",
        repo_script(args, "test.py"),
        "--name",
        name,
        *common_flags(args, dataroot, checkpoints_dir),
        "--instance_feat",
        "--cluster_path",
        cluster_path,
    ]
    notes = [
        f"the test command samples from {cluster_path} under checkpoints/{name}/",
        "the encode stage needs scikit-learn / KMeans",
    ]
    return [encode_cmd, test_cmd], notes, True


def build_test_1024p(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    name = args.name or args.target_name or DEFAULT_1024P_NAME
    cluster_path = cluster_filename(args)
    encode_cmd = [
        "python",
        repo_script(args, "encode_features.py"),
        "--name",
        name,
        "--n_clusters",
        str(args.n_clusters),
        "--netG",
        "local",
        "--ngf",
        "32",
        "--resize_or_crop",
        "none",
        *common_flags(args, dataroot, checkpoints_dir),
    ]
    test_cmd = [
        "python",
        repo_script(args, "test.py"),
        "--name",
        name,
        "--netG",
        "local",
        "--ngf",
        "32",
        "--resize_or_crop",
        "none",
        *common_flags(args, dataroot, checkpoints_dir),
        "--instance_feat",
        "--cluster_path",
        cluster_path,
    ]
    notes = [
        "the source repo contains a typo (`---netG`); this builder prints the corrected flag spelling",
        f"the test command samples from {cluster_path} under checkpoints/{name}/",
        "the encode stage needs scikit-learn / KMeans",
    ]
    return [encode_cmd, test_cmd], notes, True


def build_precompute_only(args: argparse.Namespace, dataroot: Path, checkpoints_dir: Path) -> Tuple[List[List[str]], List[str], bool]:
    source_name = args.source_name or DEFAULT_512P_NAME
    cmd = ["python", repo_script(args, "precompute_feature_maps.py"), "--name", source_name, *common_flags(args, dataroot, checkpoints_dir)]
    notes = [
        f"writes dense feature PNGs to {dataroot.as_posix()}/train_feat/",
    ]
    return [cmd], notes, False


def print_recipe(title: str, source_scripts: Sequence[str], commands: Sequence[Sequence[str]], notes: Sequence[str], warn_sklearn: bool, *, strict: bool) -> int:
    print(f"# pix2pixHD feature recipe: {title}")
    for source in source_scripts:
        print(f"# source: {source}")
    for note in notes:
        print(f"# {note}")
    if warn_sklearn:
        try:
            from sklearn.cluster import KMeans  # noqa: F401
        except Exception:
            print("# WARNING: scikit-learn (KMeans) is missing; the encode/clustering stage is unavailable until it is installed.")
            if strict:
                return 2
    for command in commands:
        print(shell_join(command))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe pix2pixHD feature-workflow command sequences.")
    parser.add_argument("--recipe", required=True, choices=[
        "train_512p_feat",
        "train_1024p_feat_12G",
        "train_1024p_feat_24G",
        "encode_features",
        "precompute_feature_maps",
        "test_512p_feat",
        "test_1024p_feat",
    ], help="Which feature workflow to print.")
    parser.add_argument("--repo-root", default=".", help="Repository root used to derive default dataset and checkpoint paths.")
    parser.add_argument("--name", help="Experiment name for single-name recipes and as a shorthand target name for 1024p recipes.")
    parser.add_argument("--source-name", help="Source checkpoint name for 1024p precompute/train recipes.")
    parser.add_argument("--target-name", help="Target experiment name for 1024p precompute/train recipes.")
    parser.add_argument("--dataroot", help="Override the dataset root; defaults to <repo-root>/datasets/cityscapes.")
    parser.add_argument("--checkpoints-dir", help="Override the checkpoint root; defaults to <repo-root>/checkpoints.")
    parser.add_argument("--gpu_ids", default=DEFAULT_GPU_IDS, help="GPU ids to print into the command sequence.")
    parser.add_argument("--feat_num", type=int, default=DEFAULT_FEAT_NUM, help="Feature-vector width to print into the command sequence.")
    parser.add_argument("--n_clusters", type=int, default=DEFAULT_N_CLUSTERS, help="KMeans cluster count used by encode_features.py.")
    parser.add_argument("--cluster_path", help="Override the cluster filename for test.py.")
    parser.add_argument("--strict", action="store_true", help="Fail when the encode/clustering stage is requested but scikit-learn is missing.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    dataroot = resolve_path(repo_root, args.dataroot, DEFAULT_DATAROOT)
    checkpoints_dir = resolve_path(repo_root, args.checkpoints_dir, DEFAULT_CHECKPOINTS_DIR)

    if args.recipe == "train_512p_feat":
        commands, notes, warn = build_train_512p(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, ["scripts/train_512p_feat.sh"], commands, notes, warn, strict=args.strict)
    if args.recipe == "train_1024p_feat_12G":
        commands, notes, warn = build_train_1024p_12g(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, ["scripts/train_1024p_feat_12G.sh"], commands, notes, warn, strict=args.strict)
    if args.recipe == "train_1024p_feat_24G":
        commands, notes, warn = build_train_1024p_24g(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, ["scripts/train_1024p_feat_24G.sh"], commands, notes, warn, strict=args.strict)
    if args.recipe == "encode_features":
        commands, notes, warn = build_encode(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, [repo_script(args, "encode_features.py")], commands, notes, warn, strict=args.strict)
    if args.recipe == "precompute_feature_maps":
        commands, notes, warn = build_precompute_only(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, [repo_script(args, "precompute_feature_maps.py")], commands, notes, warn, strict=args.strict)
    if args.recipe == "test_512p_feat":
        commands, notes, warn = build_test_512p(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, ["scripts/test_512p_feat.sh"], commands, notes, warn, strict=args.strict)
    if args.recipe == "test_1024p_feat":
        commands, notes, warn = build_test_1024p(args, dataroot, checkpoints_dir)
        return print_recipe(args.recipe, ["scripts/test_1024p_feat.sh"], commands, notes, warn, strict=args.strict)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
