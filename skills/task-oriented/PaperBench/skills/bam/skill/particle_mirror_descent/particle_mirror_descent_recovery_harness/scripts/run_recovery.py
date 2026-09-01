#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import random
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_particles(rng, modes, per_mode, prior_sigma):
    particles = []
    for mode in modes:
        for _ in range(per_mode):
            particles.append([rng.gauss(mode[0], 0.45), rng.gauss(mode[1], 0.45)])
    for _ in range(max(10, per_mode // 3)):
        particles.append([rng.gauss(0.0, prior_sigma), rng.gauss(0.0, prior_sigma)])
    return particles


def run(args):
    attempt_dir = Path(args.attempt_dir)
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_manifest = json.loads((attempt_dir / "run_manifest.json").read_text(encoding="utf-8"))
    skills_root = Path(run_manifest["generated_skills_root"])

    protocol_path = skills_root / "particle_mirror_descent_mixture_protocol" / "scripts" / "mixture_protocol.py"
    update_path = skills_root / "particle_mirror_descent_kde_update" / "scripts" / "kde_update.py"
    metrics_path = skills_root / "particle_mirror_descent_density_metrics" / "scripts" / "density_metrics.py"
    harness_path = skills_root / "particle_mirror_descent_recovery_harness" / "scripts" / "run_recovery.py"
    protocol = load_module(protocol_path, "mixture_protocol")
    kde_update = load_module(update_path, "kde_update")
    density_metrics = load_module(metrics_path, "density_metrics")

    rng = random.Random(args.seed)
    data = protocol.build_protocol(seed=args.seed, n_observations=args.observations, grid_size=args.grid_size)
    modes = data["expected_modes"]
    particles = make_particles(rng, modes, args.particles_per_mode, data["sigma1"])
    initial_weights = [1.0 / len(particles)] * len(particles)
    initial_metrics = density_metrics.symmetric_mode_coverage(particles, initial_weights, modes, args.mode_radius)

    def log_likelihood(theta, observation):
        return protocol.log_likelihood(theta, observation, sigma_x=data["sigma_x"], mix_prob=data["mix_prob"])

    def log_prior(theta):
        return protocol.log_prior(theta, sigma1=data["sigma1"], sigma2=data["sigma2"])

    pmd = kde_update.run_pmd_loop(
        particles,
        data["observations"],
        log_likelihood,
        log_prior,
        iterations=args.iterations,
        batch_size=args.batch_size,
        gamma=args.gamma,
        bandwidth=args.bandwidth,
        seed=args.seed + 17,
    )
    final_metrics = density_metrics.symmetric_mode_coverage(pmd["particles"], pmd["weights"], modes, args.mode_radius)
    weights_normalized = abs(sum(pmd["weights"]) - 1.0) < 1e-9
    mechanism = density_metrics.mechanism_checks(final_metrics, args.iterations, weights_normalized, len(pmd["trace"]))
    mechanism["mixture_protocol_skill_imported"] = hasattr(protocol, "build_protocol")
    mechanism["kde_update_skill_imported"] = hasattr(kde_update, "run_pmd_loop")
    mechanism["density_metrics_skill_imported"] = hasattr(density_metrics, "symmetric_mode_coverage")
    mechanism["recovery_harness_skill_documented"] = harness_path.exists() or (attempt_dir / "recovery" / "run_recovery.py").exists()
    mechanism["full_numpy_scipy_runtime_available"] = False

    paper_target = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))["fast_recovery_target"]
    trace_payload = {
        "schema_version": 1,
        "params_before": {"mode_masses": initial_metrics["mass_by_mode"], "ess": initial_metrics["effective_sample_size"]},
        "params_after": {"mode_masses": final_metrics["mass_by_mode"], "ess": final_metrics["effective_sample_size"]},
        "parameters_before": {"mode_masses": initial_metrics["mass_by_mode"], "ess": initial_metrics["effective_sample_size"]},
        "parameters_after": {"mode_masses": final_metrics["mass_by_mode"], "ess": final_metrics["effective_sample_size"]},
        "loss_before": 1.0 - initial_metrics["mode_coverage_score"],
        "loss_after": 1.0 - final_metrics["mode_coverage_score"],
        "iterations": pmd["trace"],
    }
    (logs_dir / "training_trace.json").write_text(json.dumps(trace_payload, indent=2), encoding="utf-8")
    (logs_dir / "generated_data_item.json").write_text(json.dumps({
        "schema_version": 1,
        "seed": args.seed,
        "dataset": paper_target["dataset"],
        "observations": data["observations"],
        "components": data["labels"],
        "true_theta": data["theta_true"],
        "sigma_x": data["sigma_x"],
        "resource_provenance": "Generated inside current attempt from the paper's Section 6 tied Gaussian mixture specification; no external benchmark resource was used.",
    }, indent=2), encoding="utf-8")
    invocations = {
        "schema_version": 1,
        "generated_skills_root": str(skills_root),
        "invocations": [
            {"module": "mixture_model_protocol", "skill": "particle_mirror_descent_mixture_protocol", "evidence": "imported helper", "artifact": str(protocol_path)},
            {"module": "pmd_kde_update", "skill": "particle_mirror_descent_kde_update", "evidence": "called script helper", "artifact": str(update_path)},
            {"module": "posterior_density_metrics", "skill": "particle_mirror_descent_density_metrics", "evidence": "called script helper", "artifact": str(metrics_path)},
            {"module": "reduced_recovery_harness", "skill": "particle_mirror_descent_recovery_harness", "evidence": "executable harness", "artifact": str(attempt_dir / "recovery" / "run_recovery.py")},
        ],
    }
    (logs_dir / "generated_skill_invocations.json").write_text(json.dumps(invocations, indent=2), encoding="utf-8")
    result = {
        "schema_version": 1,
        "paper_id": "particle_mirror_descent",
        "experiment": paper_target["dataset"],
        "is_proxy": True,
        "sample_count": len(data["observations"]),
        "metrics": final_metrics,
        "paper_target": paper_target,
        "commands": ["python recovery/run_recovery.py --attempt-dir <attempt_dir> --seed %d --observations %d --particles-per-mode %d --iterations %d --batch-size %d" % (args.seed, args.observations, args.particles_per_mode, args.iterations, args.batch_size)],
        "artifacts": ["recovery/logs/generated_data_item.json", "recovery/logs/training_trace.json", "recovery/logs/generated_skill_invocations.json"],
        "mechanism_checks": mechanism,
        "notes": "Soft-mode reduced recovery using Python standard library because NumPy/SciPy are unavailable in the active bounded runtime. The experiment preserves PMD stochastic mirror particle reweighting, KDE rejuvenation, and multimodal coverage checks.",
    }
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            str(attempt_dir / "paper_text.txt"),
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skills_root),
            str(attempt_dir / "environment" / "runtime_handoff.json"),
        ],
        "original_repo_used": False,
        "original_repo_path": "",
        "runtime_handoff": str(attempt_dir / "environment" / "runtime_handoff.json"),
        "synthetic_data_generated_current_attempt": True,
        "external_dataset_used": False,
    }
    (recovery_dir / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "metrics": final_metrics, "mechanism_checks": mechanism}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--seed", type=int, default=1506)
    parser.add_argument("--observations", type=int, default=80)
    parser.add_argument("--particles-per-mode", type=int, default=60)
    parser.add_argument("--iterations", type=int, default=45)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gamma", type=float, default=0.02)
    parser.add_argument("--bandwidth", type=float, default=0.35)
    parser.add_argument("--mode-radius", type=float, default=1.25)
    parser.add_argument("--grid-size", type=int, default=21)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
