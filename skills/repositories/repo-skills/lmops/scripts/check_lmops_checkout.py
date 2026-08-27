#!/usr/bin/env python3
"""Read-only LMOps checkout structure checker.

This helper maps a user-provided checkout to generated LMOps sub-skills. It
checks directory/file presence only; it does not import source code, execute
repo scripts, download data, or modify the checkout.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class ProjectSpec:
    label: str
    subskill: str
    description: str
    expected: List[str]


PROJECTS: List[ProjectSpec] = [
    ProjectSpec("prompt_optimization", "prompt-optimization", "ProTeGi text prompt optimization", ["prompt_optimization/README.md", "prompt_optimization/main.py"]),
    ProjectSpec("promptist", "prompt-optimization", "Promptist prompt rewriting and RL training planning", ["promptist/README.md"]),
    ProjectSpec("uprise", "example-retrieval", "UPRISE universal prompt retrieval", ["uprise/README.md", "uprise/get_cmds.py"]),
    ProjectSpec("se2", "example-retrieval", "SE2 sequential example selection", ["se2/README.md", "se2/get_cmds.py"]),
    ProjectSpec("llm_retriever", "example-retrieval", "LLM-feedback example retriever", ["llm_retriever/README.md"]),
    ProjectSpec("ced_icl", "example-retrieval", "CED-ICL demonstration selection", ["ced_icl/ced_exp/README.md"]),
    ProjectSpec("structured_prompting", "example-retrieval", "Structured Prompting many-shot ICL", ["structured_prompting/hf-version/README.md"]),
    ProjectSpec("understand_icl", "example-retrieval", "ICL meta-optimizer analysis", ["understand_icl/README.md"]),
    ProjectSpec("adaptllm", "adaptation-and-training", "Domain adaptation via reading comprehension", ["adaptllm/README.md", "adaptllm/raw2read.py"]),
    ProjectSpec("instruction_pretrain", "adaptation-and-training", "Instruction-augmented corpus generation", ["instruction_pretrain/README.md"]),
    ProjectSpec("data_selection", "adaptation-and-training", "Optimal-control data selection", ["data_selection/README.md", "data_selection/train.py"]),
    ProjectSpec("reslora", "adaptation-and-training", "ResLoRA wrapper planning", ["reslora/README.md", "reslora/myloralib/reslora.py"]),
    ProjectSpec("learning_law", "adaptation-and-training", "Learning policy optimization", ["learning_law/README.md"]),
    ProjectSpec("minillm", "distillation-and-post-training", "MiniLLM distillation", ["minillm/README.md", "minillm/train_minillm.py"]),
    ProjectSpec("dpkd", "distillation-and-post-training", "Direct Preference Knowledge Distillation", ["dpkd/README.md", "dpkd/main.py"]),
    ProjectSpec("tuna", "distillation-and-post-training", "Tuna ranking finetuning", ["tuna/README.md", "tuna/src/train_tuna.py"]),
    ProjectSpec("oel", "rl-experiential-learning", "Online Experiential Learning", ["oel/README.md"]),
    ProjectSpec("opcd", "rl-experiential-learning", "On-Policy Context Distillation", ["opcd/README.md"]),
    ProjectSpec("llm-as-a-coach", "rl-experiential-learning", "LLM-as-a-Coach experiential learning", ["llm-as-a-coach/README.md", "llm-as-a-coach/usage_example.sh"]),
    ProjectSpec("gad", "rl-experiential-learning", "Generative adversarial distillation", ["gad/README.md"]),
    ProjectSpec("opo", "rl-experiential-learning", "On-policy optimal reward baseline", ["opo/README.md"]),
    ProjectSpec("corag", "rag-and-acceleration", "Chain-of-retrieval augmented generation", ["corag/README.md"]),
    ProjectSpec("llma", "rag-and-acceleration", "LLMA reference-based decoding", ["llma/README.md", "llma/src/decode.py"]),
    ProjectSpec("LLM4Science", "root-reference-only", "Notebook evidence only", ["LLM4Science"]),
]


def project_status(repo_root: Path, spec: ProjectSpec) -> Dict[str, object]:
    checks = []
    present_count = 0
    for rel in spec.expected:
        path = repo_root / rel
        exists = path.exists()
        present_count += int(exists)
        checks.append({"path": rel, "exists": exists, "type": "directory" if path.is_dir() else "file" if path.is_file() else "missing"})
    status = "present" if present_count == len(spec.expected) else "partial" if present_count else "missing"
    return {
        "label": spec.label,
        "subskill": spec.subskill,
        "description": spec.description,
        "status": status,
        "checks": checks,
    }


def summarize(statuses: List[Dict[str, object]]) -> Dict[str, object]:
    by_subskill: Dict[str, List[str]] = {}
    for item in statuses:
        if item["status"] != "missing":
            by_subskill.setdefault(str(item["subskill"]), []).append(str(item["label"]))
    return {
        "present_or_partial_projects": sum(1 for item in statuses if item["status"] != "missing"),
        "missing_projects": sum(1 for item in statuses if item["status"] == "missing"),
        "subskill_routes": by_subskill,
    }


def render_markdown(repo_root: Path, statuses: List[Dict[str, object]]) -> str:
    lines = [
        "# LMOps checkout check",
        "",
        f"Checked root: `{repo_root}`",
        "",
        "| Project | Status | Route | Purpose |",
        "| --- | --- | --- | --- |",
    ]
    for item in statuses:
        lines.append(f"| `{item['label']}` | {item['status']} | `{item['subskill']}` | {item['description']} |")
    lines += [
        "",
        "Use the generated sub-skill route instead of assuming all LMOps paper projects are present or installed.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True, help="Path to a candidate LMOps checkout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--require-root-readme", action="store_true", help="Return non-zero if README.md is missing from the checkout root.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    statuses = [project_status(repo_root, spec) for spec in PROJECTS]
    payload = {
        "repo_root": str(repo_root),
        "root_readme_present": (repo_root / "README.md").is_file(),
        "safe": True,
        "executes_source": False,
        "summary": summarize(statuses),
        "projects": statuses,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(repo_root, statuses))

    if args.require_root_readme and not payload["root_readme_present"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
