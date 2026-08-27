#!/usr/bin/env python3
"""Safe launcher for the LatentSync Gradio app.

The repo app's source launch uses in-browser and public-share defaults. This
launcher imports the same app from an explicit runtime root and makes share and
browser behavior opt-in/opt-out through CLI flags.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight, smoke-import, or launch LatentSync gradio_app.py with explicit flags.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=os.environ.get("LATENTSYNC_REPO_ROOT", "."),
        help="LatentSync runtime tree containing gradio_app.py, scripts/, configs/, and checkpoints/.",
    )
    parser.add_argument("--config", default="configs/unet/stage2_512.yaml", help="Config assigned to gradio_app.CONFIG_PATH.")
    parser.add_argument("--checkpoint", default="checkpoints/latentsync_unet.pt", help="Checkpoint assigned to gradio_app.CHECKPOINT_PATH.")
    parser.add_argument("--server-name", default="127.0.0.1", help="Gradio server host/interface.")
    parser.add_argument("--server-port", type=int, default=None, help="Gradio server port; omit for Gradio default.")
    share_group = parser.add_mutually_exclusive_group()
    share_group.add_argument("--share", dest="share", action="store_true", help="Create a public Gradio share link.")
    share_group.add_argument("--no-share", dest="share", action="store_false", help="Do not create a public Gradio share link.")
    parser.set_defaults(share=False)
    browser_group = parser.add_mutually_exclusive_group()
    browser_group.add_argument("--browser", dest="browser", action="store_true", help="Open a browser after launch.")
    browser_group.add_argument("--no-browser", dest="browser", action="store_false", help="Do not open a browser after launch.")
    parser.set_defaults(browser=False)
    parser.add_argument("--smoke-import", action="store_true", help="Import the app, verify key attributes, and exit without serving.")
    parser.add_argument("--preflight-only", action="store_true", help="Validate paths and exit without importing or serving.")
    parser.add_argument("--check-demo-assets", action="store_true", help="Also require bundled demo assets used by the app examples.")
    parser.add_argument("--prevent-thread-lock", action="store_true", help="Pass prevent_thread_lock=True to demo.launch for external supervisors.")
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def resolve_under(root: Path, value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"{label} not found: {path}")
    if not path.is_file():
        fail(f"{label} is not a file: {path}")
    if not os.access(path, os.R_OK):
        fail(f"{label} is not readable: {path}")


def require_dir(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"{label} not found: {path}")
    if not path.is_dir():
        fail(f"{label} is not a directory: {path}")


def preflight(args: argparse.Namespace, root: Path, config: Path, checkpoint: Path) -> None:
    require_dir(root, "repo root")
    require_file(root / "gradio_app.py", "Gradio app")
    require_file(root / "scripts" / "inference.py", "repo inference module")
    require_dir(root / "latentsync", "latentsync package directory")
    require_file(config, "U-Net config")
    require_file(checkpoint, "U-Net checkpoint")
    require_file(root / "configs" / "scheduler_config.json", "scheduler config")
    if shutil.which("ffmpeg") is None:
        fail("ffmpeg not found on PATH")
    if args.check_demo_assets:
        require_file(root / "assets" / "demo1_video.mp4", "demo1 video")
        require_file(root / "assets" / "demo1_audio.wav", "demo1 audio")


def import_app(root: Path, config: Path, checkpoint: Path):
    os.chdir(root)
    sys.path.insert(0, str(root))
    import gradio_app  # type: ignore

    gradio_app.CONFIG_PATH = config
    gradio_app.CHECKPOINT_PATH = checkpoint
    if not hasattr(gradio_app, "demo"):
        fail("gradio_app did not expose a demo object")
    if not callable(getattr(gradio_app, "process_video", None)):
        fail("gradio_app did not expose callable process_video")
    return gradio_app


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    config = resolve_under(root, args.config)
    checkpoint = resolve_under(root, args.checkpoint)

    preflight(args, root, config, checkpoint)
    print("Preflight OK")
    if args.preflight_only:
        return 0

    app = import_app(root, config, checkpoint)
    print("Gradio import OK")
    if args.smoke_import:
        return 0

    launch_kwargs = {
        "server_name": args.server_name,
        "inbrowser": args.browser,
        "share": args.share,
    }
    if args.server_port is not None:
        launch_kwargs["server_port"] = args.server_port
    if args.prevent_thread_lock:
        launch_kwargs["prevent_thread_lock"] = True

    app.demo.launch(**launch_kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
