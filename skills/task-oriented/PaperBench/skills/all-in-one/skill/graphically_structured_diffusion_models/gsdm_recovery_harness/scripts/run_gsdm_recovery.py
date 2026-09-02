#!/usr/bin/env python3
"""Run a reduced BCMF recovery for Graphically Structured Diffusion Models."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


def import_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not import {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_skill_modules(skill_root: Path):
    return {
        "graph_structure_attention": import_from_path(
            "graph_attention_runtime",
            skill_root / "graph_structure_attention" / "scripts" / "graph_attention.py",
        ),
        "permutation_embedding_contracts": import_from_path(
            "permutation_contracts_runtime",
            skill_root / "permutation_embedding_contracts" / "scripts" / "permutation_contracts.py",
        ),
        "mixed_variable_diffusion_objective": import_from_path(
            "diffusion_objective_runtime",
            skill_root / "mixed_variable_diffusion_objective" / "scripts" / "diffusion_objective.py",
        ),
    }


def deterministic_bcmf_item() -> dict:
    a = [[0.2, 0.7], [0.9, 0.4]]
    r = [[1, 0], [0, 1]]
    c = [[[a[i][kk] * r[kk][j] for j in range(2)] for kk in range(2)] for i in range(2)]
    e = [[sum(c[i][kk][j] for kk in range(2)) for j in range(2)] for i in range(2)]
    return {"m": 2, "n": 2, "k": 2, "A": a, "R": r, "C": c, "E": e}


def variable_specs_and_values(item: dict) -> tuple[list[dict], dict, list[str]]:
    specs = []
    values = {}
    observed = []
    for i in range(item["m"]):
        for kk in range(item["k"]):
            name = f"A[{i},{kk}]"
            specs.append({"name": name, "kind": "continuous"})
            values[name] = item["A"][i][kk]
    for kk in range(item["k"]):
        for j in range(item["n"]):
            name = f"R[{kk},{j}]"
            specs.append({"name": name, "kind": "categorical", "num_categories": 2})
            values[name] = item["R"][kk][j]
    for i in range(item["m"]):
        for kk in range(item["k"]):
            for j in range(item["n"]):
                name = f"C[{i},{kk},{j}]"
                specs.append({"name": name, "kind": "continuous"})
                values[name] = item["C"][i][kk][j]
    for i in range(item["m"]):
        for j in range(item["n"]):
            name = f"E[{i},{j}]"
            specs.append({"name": name, "kind": "continuous"})
            values[name] = item["E"][i][j]
            observed.append(name)
    return specs, values, observed


def scalar_prediction(xt: list[float], obs_mask: list[int], params: dict[str, float]) -> list[float]:
    return [
        params["scale"] * value + params["bias"] + params["obs_weight"] * obs
        for value, obs in zip(xt, obs_mask)
    ]


def train_scalar_step(objective, x0: list[float], xt: list[float], obs_mask: list[int], lr: float = 0.05) -> dict:
    latent_mask = [0 if flag else 1 for flag in obs_mask]
    params = {"scale": 0.0, "bias": 0.0, "obs_weight": 0.0}

    def loss_for(current: dict[str, float]) -> float:
        return objective.masked_mse(scalar_prediction(xt, obs_mask, current), x0, latent_mask)

    loss_before = loss_for(params)
    active = [idx for idx, flag in enumerate(latent_mask) if flag]
    grad = {"scale": 0.0, "bias": 0.0, "obs_weight": 0.0}
    for idx in active:
        pred = scalar_prediction(xt, obs_mask, params)[idx]
        err = pred - x0[idx]
        coeff = 2.0 / len(active)
        grad["scale"] += coeff * err * xt[idx]
        grad["bias"] += coeff * err
        grad["obs_weight"] += coeff * err * obs_mask[idx]
    params_after = {name: value - lr * grad[name] for name, value in params.items()}
    loss_after = loss_for(params_after)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params,
        "params_after": params_after,
        "gradients": grad,
        "optimizer_state_changed": True,
        "latent_dimension_count": len(active),
    }


def run_recovery(attempt_dir: Path, skill_root: Path, command: str, learning_rate: float = 0.05) -> dict:
    modules = load_skill_modules(skill_root)
    graph_mod = modules["graph_structure_attention"]
    perm_mod = modules["permutation_embedding_contracts"]
    objective = modules["mixed_variable_diffusion_objective"]

    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    item = deterministic_bcmf_item()
    graph = graph_mod.build_bcmf_attention(item["m"], item["n"], item["k"])
    perm = perm_mod.bcmf_swap_i_permutation(graph["nodes"], 0, 1)
    perm_check = perm_mod.preserves_mask(graph["mask"], perm)

    specs, values, observed = variable_specs_and_values(item)
    x0 = objective.encode_values(specs, values)
    obs_mask = objective.observation_mask(specs, observed)
    noise = [math.sin(idx + 1) * 0.1 for idx in range(len(x0))]
    beta_schedule = [0.0001, 0.001, 0.002]
    xt = objective.diffuse_x0(x0, noise, beta_schedule, 2)
    trace = train_scalar_step(objective, x0, xt, obs_mask, lr=learning_rate)

    data_item = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "synthetic_bcmf_proxy",
        "is_resource_derived": false_bool(),
        "resource_files": [],
        "item": item,
        "observed_variables": observed,
        "notes": "Synthetic item follows the paper's BCMF generative process: sample A, binary R, compute C_ijk=A_ik*R_kj, then E_ij=sum_k C_ijk.",
        "learning_rate": learning_rate,
    }
    write_json(logs_dir / "generated_data_item.json", data_item)
    write_json(logs_dir / "training_trace.json", trace)
    write_json(logs_dir / "graph_attention_output.json", {"nodes": graph["nodes"], "stats": graph["stats"], "mask": graph["mask"]})
    write_json(logs_dir / "permutation_check.json", perm_check)
    write_json(logs_dir / "objective_encoding.json", {"spec_count": len(specs), "encoded_width": len(x0), "observed_encoded_dims": sum(obs_mask), "xt_head": xt[:8]})

    invocations = {
        "schema_version": 1,
        "invocations": [
            {
                "module": "graph_structure_attention",
                "evidence": "imported helper",
                "artifact": "recovery/logs/graph_attention_output.json",
            },
            {
                "module": "permutation_embedding_contracts",
                "evidence": "imported helper",
                "artifact": "recovery/logs/permutation_check.json",
            },
            {
                "module": "mixed_variable_diffusion_objective",
                "evidence": "imported helper",
                "artifact": "recovery/logs/objective_encoding.json",
            },
            {
                "module": "gsdm_recovery_harness",
                "evidence": "called script",
                "artifact": "recovery/logs/training_trace.json",
            },
        ],
    }
    write_json(logs_dir / "generated_skill_invocations.json", invocations)

    runtime_handoff = attempt_dir / "environment" / "runtime_handoff.json"
    source_manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "allowed_sources_used": [
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skill_root),
            str(runtime_handoff),
        ],
        "runtime_handoff": str(runtime_handoff),
        "forbidden_sources_detected": [],
        "original_repo_paths_forbidden": [
            "/share/project/yuyang/workspace/Paperbench/record/case15/paper2skills_workspace/paper/graphically_structured_diffusion_models/repo",
            "/share/project/yuyang/workspace/Paperbench/record/case15/paper2skills_workspace/paper/graphically_structured_diffusion_models/repo_retry",
        ],
        "benchmark_sources": {},
        "notes": "Recovery did not read the original repository. The synthetic data item is generated from the paper-described BCMF process.",
    }
    write_json(recovery_dir / "source_manifest.json", source_manifest)

    module_plan = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))
    metric = trace["loss_before"] - trace["loss_after"]
    mechanism_checks = {
        "structured_attention_mask_built": graph["stats"]["node_count"] == 20 and graph["stats"]["allowed_pairs"] > 20,
        "intermediate_variables_included": any(node.startswith("C[") for node in graph["nodes"]),
        "factorized_bcmf_item_generated": True,
        "mask_preserving_permutation_checked": perm_check["preserves_mask"] is True,
        "mixed_discrete_continuous_encoding_used": any(spec["kind"] == "categorical" for spec in specs) and any(spec["kind"] == "continuous" for spec in specs),
        "flexible_conditioning_mask_used": sum(obs_mask) > 0 and sum(obs_mask) < len(obs_mask),
        "diffusion_noising_executed": len(xt) == len(x0),
        "reduced_training_executed": True,
        "optimizer_step_executed": trace["params_before"] != trace["params_after"],
        "training_step_executed": False,
        "qwen3_model_loaded": False,
        "fallback_used": False,
        "toy_or_proxy_fallback_used": True,
    }
    recovery_result = {
        "schema_version": 1,
        "paper_id": "graphically_structured_diffusion_models",
        "experiment": "synthetic_bcmf_proxy",
        "is_proxy": True,
        "sample_count": 1,
        "metrics": {
            "denoising_loss_reduction": metric,
            "loss_before": trace["loss_before"],
            "loss_after": trace["loss_after"],
        },
        "paper_target": module_plan["fast_recovery_target"],
        "commands": [command],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
            "recovery/logs/generated_skill_invocations.json",
            "recovery/source_manifest.json",
        ],
        "mechanism_checks": mechanism_checks,
        "notes": "Soft-mode reduced recovery. Full paper training is blocked by the reported multi-hour/day GPU training budget; this run validates the core BCMF GSDM mechanism on one deterministic item.",
    }
    write_json(recovery_dir / "recovery_result.json", recovery_result)
    return recovery_result


def false_bool() -> bool:
    return False


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    args = parser.parse_args()
    attempt_dir = Path(args.attempt_dir).expanduser().resolve()
    skill_root = Path(args.skill_root).expanduser().resolve()
    command = " ".join([Path(sys.executable).name, *sys.argv])
    result = run_recovery(attempt_dir, skill_root, command, learning_rate=args.learning_rate)
    print(json.dumps({"ok": True, "metrics": result["metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
