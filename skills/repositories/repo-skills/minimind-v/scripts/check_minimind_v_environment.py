#!/usr/bin/env python3
"""Safe MiniMind-V environment and resource preflight.

The helper checks imports and project-relative resources for selected workflows.
It does not download resources, load model weights, train, serve, run generation,
or execute checkpoint conversion.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

WORKFLOW_MODULES = {
    "data": ["pyarrow", "PIL"],
    "api": ["torch", "transformers"],
    "inference-native": ["torch", "transformers", "PIL"],
    "inference-transformers": ["torch", "transformers", "PIL"],
    "training-pretrain": ["torch", "transformers", "datasets", "PIL"],
    "training-sft": ["torch", "transformers", "datasets", "PIL"],
    "export": ["torch", "transformers"],
    "webui": ["torch", "transformers", "PIL", "gradio"],
}

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Check MiniMind-V workflow prerequisites without downloads, model loading, training, serving, or generation.")
    p.add_argument("--repo-root", default=".", help="MiniMind-V checkout root to inspect (default: current directory).")
    p.add_argument("--workflow", choices=sorted(WORKFLOW_MODULES), default="api", help="Workflow prerequisite set to check.")
    p.add_argument("--hidden-size", type=int, default=768, help="Hidden size used in native checkpoint names (default: 768).")
    p.add_argument("--use-moe", type=int, choices=[0, 1], default=0, help="Use MoE checkpoint suffix convention (default: 0).")
    p.add_argument("--weight", default="sft_vlm", help="Native checkpoint prefix for inference/export checks (default: sft_vlm).")
    p.add_argument("--transformers-dir", help="Transformers-format directory for inference-transformers/webui/export checks.")
    p.add_argument("--data-path", help="Parquet path for data/training checks; relative paths resolve under repo root.")
    p.add_argument("--json", action="store_true", help="Emit JSON report instead of text.")
    return p

def rel_or_abs(repo: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else repo / path

def module_status(name: str) -> dict[str, object]:
    return {"module": name, "available": importlib.util.find_spec(name) is not None}

def check_path(path: Path, label: str, required: bool = True) -> dict[str, object]:
    return {"label": label, "path": label, "exists": path.exists(), "is_file": path.is_file(), "is_dir": path.is_dir(), "required": required}

def weight_name(weight: str, hidden_size: int, use_moe: int) -> str:
    return f"{weight}_{hidden_size}{'_moe' if use_moe else ''}.pth"

def collect(args: argparse.Namespace) -> dict[str, object]:
    repo = Path(args.repo_root).expanduser().resolve()
    checks: list[dict[str, object]] = [{"label": "repo root", "path": ".", "exists": repo.is_dir(), "is_file": repo.is_file(), "is_dir": repo.is_dir(), "required": True}]
    warnings: list[str] = []
    if args.workflow != "data":
        checks += [
            check_path(repo / "model" / "model_vlm.py", "model/model_vlm.py"),
            check_path(repo / "model" / "model_minimind.py", "model/model_minimind.py"),
            check_path(repo / "model" / "tokenizer.json", "model/tokenizer.json"),
            check_path(repo / "model" / "tokenizer_config.json", "model/tokenizer_config.json"),
            {"label": "SigLIP2 vision encoder directory", "path": "model/siglip2-base-p32-256-ve/", "exists": (repo / "model" / "siglip2-base-p32-256-ve").is_dir(), "is_file": False, "is_dir": (repo / "model" / "siglip2-base-p32-256-ve").is_dir(), "required": args.workflow != "api"},
        ]
    if args.workflow == "data":
        data = rel_or_abs(repo, args.data_path or "dataset/sft_i2t.parquet")
        checks.append(check_path(data, args.data_path or "dataset/sft_i2t.parquet"))
    if args.workflow == "training-pretrain":
        checks.append(check_path(rel_or_abs(repo, args.data_path or "dataset/pretrain_i2t.parquet"), args.data_path or "dataset/pretrain_i2t.parquet"))
        checks.append(check_path(repo / "out" / weight_name("llm", args.hidden_size, args.use_moe), f"out/{weight_name('llm', args.hidden_size, args.use_moe)}"))
        checks.append(check_path(repo / "trainer" / "train_pretrain_vlm.py", "trainer/train_pretrain_vlm.py"))
    elif args.workflow == "training-sft":
        checks.append(check_path(rel_or_abs(repo, args.data_path or "dataset/sft_i2t.parquet"), args.data_path or "dataset/sft_i2t.parquet"))
        pre = repo / "out" / weight_name("pretrain_vlm", args.hidden_size, args.use_moe)
        llm = repo / "out" / weight_name("llm", args.hidden_size, args.use_moe)
        ok = pre.is_file() or llm.is_file()
        checks.append({"label": "SFT initial weight (pretrain_vlm or llm)", "path": f"out/{pre.name} or out/{llm.name}", "exists": ok, "is_file": ok, "is_dir": False, "required": True})
        checks.append(check_path(repo / "trainer" / "train_sft_vlm.py", "trainer/train_sft_vlm.py"))
    elif args.workflow == "inference-native":
        checks.append(check_path(repo / "eval_vlm.py", "eval_vlm.py"))
        checks.append(check_path(repo / "out" / weight_name(args.weight, args.hidden_size, args.use_moe), f"out/{weight_name(args.weight, args.hidden_size, args.use_moe)}"))
    elif args.workflow in {"inference-transformers", "webui"}:
        if args.transformers_dir:
            tdir = rel_or_abs(repo, args.transformers_dir)
            checks.append({"label": "Transformers directory", "path": args.transformers_dir, "exists": tdir.is_dir(), "is_file": False, "is_dir": tdir.is_dir(), "required": True})
            checks.append(check_path(tdir / "config.json", f"{args.transformers_dir}/config.json"))
            checks.append(check_path(tdir / "tokenizer.json", f"{args.transformers_dir}/tokenizer.json", required=False))
        else:
            warnings.append("No --transformers-dir supplied; only generic repository/WebUI prerequisites were checked.")
        if args.workflow == "webui":
            checks.append(check_path(repo / "scripts" / "web_demo_vlm.py", "scripts/web_demo_vlm.py"))
    elif args.workflow == "export":
        checks.append(check_path(repo / "out" / weight_name(args.weight, args.hidden_size, args.use_moe), f"out/{weight_name(args.weight, args.hidden_size, args.use_moe)}"))
        checks.append(check_path(repo / "scripts" / "convert_vlm.py", "scripts/convert_vlm.py"))
    imports = [module_status(name) for name in WORKFLOW_MODULES[args.workflow]]
    missing_required = [c for c in checks if c.get("required") and not c.get("exists")]
    missing_modules = [m for m in imports if not m["available"]]
    return {"workflow": args.workflow, "repo_root_checked": str(repo), "imports": imports, "resource_checks": checks, "warnings": warnings, "missing_required_count": len(missing_required), "missing_module_count": len(missing_modules), "ready_for_static_planning": True, "ready_to_run_selected_workflow": not missing_required and not missing_modules, "note": "This helper did not download resources, load weights, train, serve, convert, or run generation."}

def print_text(report: dict[str, object]) -> None:
    print(f"MiniMind-V preflight for workflow: {report['workflow']}")
    print("Imports:")
    for item in report["imports"]:  # type: ignore[index]
        print(f"  [{'OK' if item['available'] else 'MISSING'}] {item['module']}")  # type: ignore[index]
    print("Resource checks:")
    for item in report["resource_checks"]:  # type: ignore[index]
        status = "OK" if item["exists"] else ("MISSING" if item["required"] else "WARN")  # type: ignore[index]
        print(f"  [{status}] {item['label']}: {item['path']}")  # type: ignore[index]
    if report["warnings"]:
        print("Warnings:")
        for w in report["warnings"]: print(f"  - {w}")  # type: ignore[union-attr]
    print(f"Ready to run selected workflow: {report['ready_to_run_selected_workflow']}")
    print(report["note"])

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ready_to_run_selected_workflow"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
