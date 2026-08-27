#!/usr/bin/env python3
"""Build a safe GUI-Owl v3.5 browser command template."""
from __future__ import annotations

import argparse
import shlex


def env_ref(name: str) -> str:
    if not name or not name.replace("_", "").replace("-", "").isalnum():
        raise SystemExit(f"invalid environment variable name: {name!r}")
    return f'"${{{name}}}"'


def val(value: str | None, env: str | None, label: str, default: str | None = None) -> str:
    if value is not None:
        return shlex.quote(value)
    if env:
        return env_ref(env)
    if default is not None:
        return shlex.quote(default)
    raise SystemExit(f"missing --{label} or --{label}-env")


def main() -> int:
    p = argparse.ArgumentParser(description="Print a safe GUI-Owl v3.5 browser command template.")
    p.add_argument("--repo-root")
    p.add_argument("--repo-root-env", default="MOBILE_AGENT_REPO")
    p.add_argument("--task-id", default="WebAgent_task_0")
    p.add_argument("--task", required=True)
    p.add_argument("--web", default="")
    p.add_argument("--login", action="store_true")
    p.add_argument("--rollout-id", default="0")
    p.add_argument("--max-iter", type=int, default=100)
    p.add_argument("--output-dir", default="results_log")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--image-type", choices=["base64", "file", "oss"], default="base64")
    p.add_argument("--download-dir", default="downloads")
    p.add_argument("--model")
    p.add_argument("--model-env", default="GUI_OWL_MODEL")
    p.add_argument("--base-url")
    p.add_argument("--base-url-env", default="GUI_OWL_BASE_URL")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--use-css-som", action="store_true")
    p.add_argument("--use-omni-som", action="store_true")
    p.add_argument("--omni-url", default="")
    p.add_argument("--eval", action="store_true")
    p.add_argument("--eval-model", default="")
    p.add_argument("--eval-mode", default="")
    p.add_argument("--one-line", action="store_true")
    args = p.parse_args()
    if args.use_css_som and args.use_omni_som:
        raise SystemExit("choose only one of --use-css-som or --use-omni-som")
    repo = shlex.quote(args.repo_root) if args.repo_root else env_ref(args.repo_root_env)
    parts = ["cd", f"{repo}/Mobile-Agent-v3.5/browser_use", "&&", "python", "run_gui_owl_1_5_for_web.py",
             "--task_id", shlex.quote(args.task_id), "--task", shlex.quote(args.task), "--rollout_id", shlex.quote(args.rollout_id),
             "--max_iter", str(args.max_iter), "--output_dir", shlex.quote(args.output_dir), "--seed", str(args.seed),
             "--image_type", shlex.quote(args.image_type), "--download_dir", shlex.quote(args.download_dir),
             "--model", val(args.model, args.model_env, "model"), "--base_url", val(args.base_url, args.base_url_env, "base-url")]
    if args.web:
        parts += ["--web", shlex.quote(args.web)]
    if args.login:
        parts.append("--login")
    if args.headless:
        parts.append("--headless")
    if args.use_css_som:
        parts.append("--use_css_som")
    if args.use_omni_som:
        parts.append("--use_omni_som")
    if args.omni_url:
        parts += ["--omni_url", shlex.quote(args.omni_url)]
    if args.eval:
        parts.append("--eval")
        if args.eval_model:
            parts += ["--eval_model", shlex.quote(args.eval_model)]
        if args.eval_mode:
            parts += ["--eval_mode", shlex.quote(args.eval_mode)]
    command = " ".join(parts)
    if not args.one_line:
        print("# Safe template only: install Playwright/Chromium and verify website/login/API/optional OSS or OmniParser before running.")
        print("# image_type=oss requires private OSS credentials in the runtime environment; base64/file avoid OSS upload.")
    print(command)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
