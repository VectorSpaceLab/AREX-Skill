#!/usr/bin/env python3
"""Build a safe StudioGAN checkpoint-analysis command without executing it.

The helper validates obvious StudioGAN analysis constraints, then prints a
shell command that runs the public ``src/main.py`` entry point from an explicit
StudioGAN checkout. It does not train, download data, contact services, or write
outputs by itself.

Example:
    python scripts/build_checkpoint_analysis_command.py \
      --repo-root /path/to/PyTorch-StudioGAN \
      --cfg src/configs/CIFAR10/ContraGAN.yaml \
      --checkpoint /path/to/checkpoints/run-name \
      --save-dir /path/to/analysis-output \
      --data-dir /path/to/data \
      --gpus 0 --visualize --save-fake --fake-count 64
"""

from __future__ import annotations

import argparse
import glob
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CORE_ACTIONS = (
    "save_real",
    "save_fake",
    "visualize",
    "knn",
    "interpolation",
    "frequency",
    "tsne",
    "ifid",
    "gan_train",
    "gan_test",
    "sefa",
)

DATASET_DEPENDENT_ACTIONS = {
    "save_real",
    "knn",
    "frequency",
    "tsne",
    "ifid",
    "gan_train",
    "gan_test",
}

BATCH_MULTIPLE_OF_8_ACTIONS = {
    "visualize",
    "knn",
    "interpolation",
    "ifid",
    "gan_train",
    "gan_test",
}

INTERPOLATION_BACKBONES = {
    "big_resnet",
    "big_resnet_deep_legacy",
    "big_resnet_deep_studiogan",
}

STYLEGAN_BACKBONES = {"stylegan2", "stylegan3"}

DEFAULTS: Dict[str, Dict[str, Any]] = {
    "MODEL": {
        "backbone": "resnet",
        "d_cond_mtd": "W/O",
        "z_prior": "gaussian",
    },
    "LOSS": {
        "apply_lo": False,
    },
    "OPTIMIZATION": {
        "batch_size": 64,
    },
}


class CommandError(RuntimeError):
    """Raised for user-correctable command-construction errors."""


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def normalize_path(value: str, *, base: Optional[Path] = None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve(strict=False)


def load_yaml_if_available(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        warn("PyYAML is not importable; skipping config-derived compatibility checks.")
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
    except Exception as exc:  # noqa: BLE001 - show a concise parser-facing error.
        raise CommandError(f"could not read YAML config {path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise CommandError(f"YAML config {path} did not parse to a mapping")
    return loaded


def nested_get(cfg: Dict[str, Any], section: str, key: str) -> Any:
    section_data = cfg.get(section, {})
    if isinstance(section_data, dict) and key in section_data:
        return section_data[key]
    return DEFAULTS.get(section, {}).get(key)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def selected_core_actions(args: argparse.Namespace) -> List[str]:
    return [name for name in CORE_ACTIONS if getattr(args, name)]


def validate_checkpoint_dir(checkpoint: Path, *, load_best: bool) -> None:
    if not checkpoint.exists():
        raise CommandError(f"checkpoint directory does not exist: {checkpoint}")
    if not checkpoint.is_dir():
        raise CommandError(f"StudioGAN -ckpt expects a checkpoint directory, not a file: {checkpoint}")

    best_g = glob.glob(str(checkpoint / "model=G-best-weights-step*.pth"))
    best_d = glob.glob(str(checkpoint / "model=D-best-weights-step*.pth"))
    current_g = glob.glob(str(checkpoint / "model=G-current-weights-step*.pth"))
    current_d = glob.glob(str(checkpoint / "model=D-current-weights-step*.pth"))

    if load_best:
        if not (best_g and best_d):
            warn(
                "--load-best was selected, but the checkpoint directory does not appear to contain both "
                "model=G-best-weights-step*.pth and model=D-best-weights-step*.pth."
            )
    else:
        if not (current_g and current_d):
            warn(
                "checkpoint directory does not appear to contain both current G/D checkpoint files; "
                "initial -ckpt loading may fail unless --load-best is used and best files exist."
            )
        if not (best_g and best_d):
            warn(
                "checkpoint directory does not appear to contain both best G/D checkpoint files; "
                "StudioGAN's final analysis reload step may fail if it cannot find best weights."
            )


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise CommandError(message)


def validate_args(args: argparse.Namespace, cfg: Dict[str, Any], *, config_checks_available: bool) -> None:
    actions = selected_core_actions(args)
    ensure(actions, "select one or more checkpoint analysis actions such as --visualize, --save-fake, --knn, or --sefa")

    if config_checks_available:
        backbone = str(nested_get(cfg, "MODEL", "backbone"))
        d_cond_mtd = str(nested_get(cfg, "MODEL", "d_cond_mtd"))
        z_prior = str(nested_get(cfg, "MODEL", "z_prior"))
        apply_lo = as_bool(nested_get(cfg, "LOSS", "apply_lo"))
        batch_size_value = nested_get(cfg, "OPTIMIZATION", "batch_size")
        try:
            batch_size = int(batch_size_value)
        except Exception:
            batch_size = None
            warn(f"could not interpret OPTIMIZATION.batch_size={batch_size_value!r}; skipping batch-size multiple-of-8 check.")
    else:
        backbone = d_cond_mtd = z_prior = "unknown"
        apply_lo = False
        batch_size = None
        warn("config-derived checks are unavailable; skipping backbone, batch-size, CAS-conditioning, latent-prior, and latent-optimization checks.")

    if args.fake_count is not None:
        ensure(args.save_fake, "--fake-count maps to -sf_num and requires --save-fake")
        ensure(args.fake_count > 0, "--fake-count must be positive")

    ensure(not (args.gan_train and args.gan_test), "StudioGAN CAS modes are mutually exclusive: choose --gan-train or --gan-test, not both")
    if args.resume_classifier_train:
        ensure(args.gan_train or args.gan_test, "--resume-classifier-train only applies to --gan-train or --gan-test")

    if args.sefa_axis is not None:
        ensure(args.sefa, "--sefa-axis maps to -sefa_axis and requires --sefa")
    if args.sefa_max is not None:
        ensure(args.sefa, "--sefa-max maps to -sefa_max and requires --sefa")
    if args.sefa:
        ensure(args.sefa_axis is not None and args.sefa_axis > 0, "SeFa requires --sefa-axis to be a positive integer")
        if config_checks_available:
            ensure(backbone not in STYLEGAN_BACKBONES, "StudioGAN config compatibility rejects SeFa for StyleGAN2/StyleGAN3 backbones")
            if backbone not in INTERPOLATION_BACKBONES:
                warn(f"SeFa is BigGAN-focused in StudioGAN; backbone={backbone!r} may fail if the generator lacks the expected linear layer.")
        else:
            warn("could not confirm whether the config backbone is BigGAN-compatible for SeFa.")
        if args.sefa_max is None:
            warn("--sefa was selected without --sefa-max; native default is -1, which may be unintuitive for semantic traversals.")

    if args.interpolation:
        if config_checks_available:
            ensure(
                backbone in INTERPOLATION_BACKBONES,
                "StudioGAN interpolation is supported only for big_resnet, big_resnet_deep_legacy, or big_resnet_deep_studiogan backbones",
            )
        else:
            warn("could not confirm interpolation backbone compatibility; StudioGAN supports it only for Big ResNet-style backbones.")

    if args.batch_stat:
        ensure(not args.standing_stats, "-batch_stat and -std_stat are mutually exclusive")
    if args.standing_stats:
        ensure(args.standing_max is not None and args.standing_step is not None, "--standing-stats requires --standing-max and --standing-step")
        ensure(args.standing_max > 0 and args.standing_step > 0, "--standing-max and --standing-step must be positive")
    else:
        ensure(args.standing_max is None and args.standing_step is None, "--standing-max/--standing-step require --standing-stats")

    if args.truncation_factor is not None:
        ensure(args.truncation_factor == -1 or args.truncation_factor >= 0, "truncation factor must be -1 or non-negative")
        if config_checks_available and backbone in STYLEGAN_BACKBONES:
            ensure(0 <= args.truncation_factor <= 1, "StyleGAN truncation factor must be between 0 and 1")
        elif not config_checks_available and args.truncation_factor > 1:
            warn("could not confirm backbone; StyleGAN truncation would require a value between 0 and 1.")
        if args.truncation_factor == -1:
            warn("--truncation-factor -1 is StudioGAN's no-truncation sentinel.")
    if args.truncation_cutoff is not None:
        if config_checks_available and backbone not in STYLEGAN_BACKBONES:
            warn("--truncation-cutoff is used by StyleGAN sampling and is ignored by non-StyleGAN generators.")
        elif not config_checks_available:
            warn("could not confirm StyleGAN backbone for --truncation-cutoff.")

    if args.langevin:
        ensure(args.lgv_rate is not None and args.lgv_std is not None and args.lgv_steps is not None, "--langevin requires --lgv-rate, --lgv-std, and --lgv-steps")
        ensure(args.lgv_rate > 0, "--lgv-rate must be positive")
        ensure(args.lgv_std > 0, "--lgv-std must be positive")
        ensure(args.lgv_steps > 0, "--lgv-steps must be positive")
        if config_checks_available:
            ensure(not apply_lo, "Langevin/DDLS sampling cannot be combined with latent optimization (LOSS.apply_lo=True)")
            ensure(z_prior == "gaussian", "Langevin/DDLS sampling requires MODEL.z_prior='gaussian'")
        else:
            warn("could not confirm Langevin requirements from config: MODEL.z_prior must be gaussian and LOSS.apply_lo must be false.")
        if (args.lgv_decay is None) ^ (args.lgv_decay_steps is None):
            raise CommandError("use both --lgv-decay and --lgv-decay-steps, or neither")
        if args.lgv_decay is not None:
            ensure(args.lgv_decay > 0 and args.lgv_decay_steps is not None and args.lgv_decay_steps > 0, "Langevin decay and decay steps must be positive")
    else:
        lgv_params = [args.lgv_rate, args.lgv_std, args.lgv_decay, args.lgv_decay_steps, args.lgv_steps]
        ensure(all(value is None for value in lgv_params), "-lgv_* parameters require --langevin")

    missing_data_actions = sorted(DATASET_DEPENDENT_ACTIONS.intersection(actions))
    if missing_data_actions and args.data_dir is None:
        raise CommandError(
            "--data-dir is required for dataset/reference-dependent analyses: " + ", ".join(missing_data_actions)
        )
    if args.data_dir is None and any(name in actions for name in {"visualize", "interpolation", "sefa"}):
        warn(
            "these analyses mostly sample from the checkpoint, but current StudioGAN config checks may still request -data; "
            "provide --data-dir if the native command raises a data_dir assertion."
        )

    if batch_size is not None:
        affected = sorted(BATCH_MULTIPLE_OF_8_ACTIONS.intersection(actions))
        if affected:
            ensure(batch_size % 8 == 0, f"OPTIMIZATION.batch_size={batch_size} is not divisible by 8, required for: {', '.join(affected)}")

    if args.gan_train or args.gan_test:
        if config_checks_available:
            ensure(d_cond_mtd != "W/O", "Classifier Accuracy Score requires a class-conditioned discriminator configuration")
        else:
            warn("could not confirm CAS conditioning from config; CAS requires a class-conditioned discriminator.")
        warn("CAS trains a classifier and can be much longer than visualization/sampling analyses.")

    if any(name in actions for name in {"knn", "ifid"}):
        warn("KNN/iFID may download or require metric/backbone weights and can be memory/time heavy.")
    if args.tsne:
        warn("TSNE uses discriminator embeddings over real and fake batches and can be memory/time heavy.")


def append_if(cmd: List[str], condition: bool, *parts: str) -> None:
    if condition:
        cmd.extend(parts)


def build_command(args: argparse.Namespace, repo_root: Path, cfg_path: Path, checkpoint: Path) -> List[str]:
    main_py = repo_root / "src" / "main.py"
    save_dir = normalize_path(args.save_dir)
    data_dir = normalize_path(args.data_dir) if args.data_dir is not None else None

    cmd: List[str] = []
    if args.gpus:
        cmd.append(f"CUDA_VISIBLE_DEVICES={args.gpus}")
    cmd.extend([
        args.python,
        str(main_py),
        "-cfg",
        str(cfg_path),
        "-ckpt",
        str(checkpoint),
        "-save",
        str(save_dir),
        "-metrics",
        "none",
    ])
    if data_dir is not None:
        cmd.extend(["-data", str(data_dir)])
    if args.load_best:
        cmd.append("-best")

    append_if(cmd, args.save_real, "-sr")
    append_if(cmd, args.save_fake, "-sf")
    if args.fake_count is not None:
        cmd.extend(["-sf_num", str(args.fake_count)])
    append_if(cmd, args.visualize, "-v")
    append_if(cmd, args.knn, "-knn")
    append_if(cmd, args.interpolation, "-itp")
    append_if(cmd, args.frequency, "-fa")
    append_if(cmd, args.tsne, "-tsne")
    append_if(cmd, args.ifid, "-ifid")
    append_if(cmd, args.gan_train, "--GAN_train")
    append_if(cmd, args.gan_test, "--GAN_test")
    append_if(cmd, args.resume_classifier_train, "-resume_ct")
    append_if(cmd, args.sefa, "-sefa")
    if args.sefa_axis is not None:
        cmd.extend(["-sefa_axis", str(args.sefa_axis)])
    if args.sefa_max is not None:
        cmd.extend(["-sefa_max", str(args.sefa_max)])
    if args.truncation_factor is not None:
        cmd.extend(["--truncation_factor", str(args.truncation_factor)])
    if args.truncation_cutoff is not None:
        cmd.extend(["--truncation_cutoff", str(args.truncation_cutoff)])
    append_if(cmd, args.standing_stats, "-std_stat")
    if args.standing_max is not None:
        cmd.extend(["-std_max", str(args.standing_max)])
    if args.standing_step is not None:
        cmd.extend(["-std_step", str(args.standing_step)])
    append_if(cmd, args.batch_stat, "-batch_stat")
    append_if(cmd, args.langevin, "-lgv")
    if args.lgv_rate is not None:
        cmd.extend(["-lgv_rate", str(args.lgv_rate)])
    if args.lgv_std is not None:
        cmd.extend(["-lgv_std", str(args.lgv_std)])
    if args.lgv_decay is not None:
        cmd.extend(["-lgv_decay", str(args.lgv_decay)])
    if args.lgv_decay_steps is not None:
        cmd.extend(["-lgv_decay_steps", str(args.lgv_decay_steps)])
    if args.lgv_steps is not None:
        cmd.extend(["-lgv_steps", str(args.lgv_steps)])
    return cmd


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build, validate, and print a StudioGAN src/main.py command for checkpoint sampling and analysis. "
            "The printed command is not executed and includes '-metrics none' so standalone metric evaluation is not run by surprise."
        )
    )
    parser.add_argument("--repo-root", required=True, help="Path to a StudioGAN checkout containing src/main.py.")
    parser.add_argument("--cfg", required=True, help="StudioGAN YAML config path; relative paths are resolved under --repo-root.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint directory passed to native -ckpt.")
    parser.add_argument("--save-dir", required=True, help="Output root passed to native -save.")
    parser.add_argument("--data-dir", help="Dataset/reference root passed to native -data when an analysis needs real data.")
    parser.add_argument("--gpus", help="Value for CUDA_VISIBLE_DEVICES in the printed command, such as '0' or '0,1'.")
    parser.add_argument("--python", default="python", help="Python executable token to print. Default: python")
    parser.add_argument("--load-best", action="store_true", help="Add native -best during initial checkpoint loading.")
    parser.add_argument("--dry-run-no-path-check", action="store_true", help="Skip repo/config/checkpoint existence checks for command drafting.")

    action_group = parser.add_argument_group("checkpoint analysis actions")
    action_group.add_argument("--save-real", action="store_true", help="Add native -sr/--save_real_images.")
    action_group.add_argument("--save-fake", action="store_true", help="Add native -sf/--save_fake_images.")
    action_group.add_argument("--fake-count", type=int, help="Add native -sf_num; requires --save-fake.")
    action_group.add_argument("--visualize", action="store_true", help="Add native -v/--vis_fake_images.")
    action_group.add_argument("--knn", action="store_true", help="Add native -knn/--k_nearest_neighbor.")
    action_group.add_argument("--interpolation", action="store_true", help="Add native -itp/--interpolation.")
    action_group.add_argument("--frequency", action="store_true", help="Add native -fa/--frequency_analysis.")
    action_group.add_argument("--tsne", action="store_true", help="Add native -tsne/--tsne_analysis.")
    action_group.add_argument("--ifid", action="store_true", help="Add native -ifid/--intra_class_fid.")
    action_group.add_argument("--gan-train", action="store_true", help="Add native --GAN_train for CAS recall.")
    action_group.add_argument("--gan-test", action="store_true", help="Add native --GAN_test for CAS precision.")
    action_group.add_argument("--resume-classifier-train", "--resume-classifier", dest="resume_classifier_train", action="store_true", help="Add native -resume_ct for CAS classifier training.")
    action_group.add_argument("--sefa", action="store_true", help="Add native -sefa/--semantic_factorization.")
    action_group.add_argument("--sefa-axis", type=int, help="Add native -sefa_axis; must be positive and requires --sefa.")
    action_group.add_argument("--sefa-max", type=float, help="Add native -sefa_max; requires --sefa.")

    sampling_group = parser.add_argument_group("sampling modifiers")
    sampling_group.add_argument("--truncation-factor", type=float, help="Add native --truncation_factor.")
    sampling_group.add_argument("--truncation-cutoff", type=float, help="Add native --truncation_cutoff for StyleGAN sampling.")
    sampling_group.add_argument("--standing-stats", action="store_true", help="Add native -std_stat; requires --standing-max and --standing-step.")
    sampling_group.add_argument("--standing-max", type=int, help="Add native -std_max; requires --standing-stats.")
    sampling_group.add_argument("--standing-step", type=int, help="Add native -std_step; requires --standing-stats.")
    sampling_group.add_argument("--batch-stat", action="store_true", help="Add native -batch_stat. Mutually exclusive with --standing-stats.")
    sampling_group.add_argument("--langevin", action="store_true", help="Add native -lgv for DDLS/Langevin-aware sampling.")
    sampling_group.add_argument("--lgv-rate", type=float, help="Add native -lgv_rate; requires --langevin.")
    sampling_group.add_argument("--lgv-std", type=float, help="Add native -lgv_std; requires --langevin.")
    sampling_group.add_argument("--lgv-decay", type=float, help="Add native -lgv_decay; requires --langevin and --lgv-decay-steps.")
    sampling_group.add_argument("--lgv-decay-steps", type=int, help="Add native -lgv_decay_steps; requires --langevin and --lgv-decay.")
    sampling_group.add_argument("--lgv-steps", type=int, help="Add native -lgv_steps; requires --langevin.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        repo_root = normalize_path(args.repo_root)
        cfg_path = normalize_path(args.cfg, base=repo_root)
        checkpoint = normalize_path(args.checkpoint)

        if not args.dry_run_no_path_check:
            ensure(repo_root.exists() and repo_root.is_dir(), f"--repo-root does not exist or is not a directory: {repo_root}")
            ensure((repo_root / "src" / "main.py").exists(), f"--repo-root does not look like StudioGAN; missing src/main.py under {repo_root}")
            ensure(cfg_path.exists() and cfg_path.is_file(), f"--cfg does not exist or is not a file: {cfg_path}")
            validate_checkpoint_dir(checkpoint, load_best=args.load_best)
        else:
            if cfg_path.exists() and cfg_path.is_file():
                pass
            else:
                warn("skipping config-derived checks because --dry-run-no-path-check was used and the config file was not found.")

        cfg = load_yaml_if_available(cfg_path) if cfg_path.exists() and cfg_path.is_file() else {}
        validate_args(args, cfg, config_checks_available=bool(cfg))
        cmd = build_command(args, repo_root, cfg_path, checkpoint)
        print(quote_command(cmd))
        return 0
    except CommandError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
