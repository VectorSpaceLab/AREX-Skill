#!/usr/bin/env python3
"""Safe import and signature inspection for poisoning / privacy / extraction APIs.

This helper only imports ART classes and inspects their signatures. It does not
train models, download data, or run attacks.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


def _bootstrap_repo_root() -> None:
    """Add the repository root to sys.path when running from the skill tree."""

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "art").is_dir() and ((parent / "pyproject.toml").exists() or (parent / "setup.py").exists()):
            root = str(parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            return


_bootstrap_repo_root()


TARGETS: list[tuple[str, str, str]] = [
    ("PoisoningAttackSVM", "art.attacks.poisoning.poisoning_attack_svm", "PoisoningAttackSVM"),
    ("FeatureCollisionAttack", "art.attacks.poisoning.feature_collision_attack", "FeatureCollisionAttack"),
    ("PoisoningAttackBackdoor", "art.attacks.poisoning.backdoor_attack", "PoisoningAttackBackdoor"),
    (
        "PoisoningAttackCleanLabelBackdoor",
        "art.attacks.poisoning.clean_label_backdoor_attack",
        "PoisoningAttackCleanLabelBackdoor",
    ),
    (
        "PoisoningAttackAdversarialEmbedding",
        "art.attacks.poisoning.adversarial_embedding_attack",
        "PoisoningAttackAdversarialEmbedding",
    ),
    (
        "HiddenTriggerBackdoor",
        "art.attacks.poisoning.hidden_trigger_backdoor.hidden_trigger_backdoor",
        "HiddenTriggerBackdoor",
    ),
    ("GradientMatchingAttack", "art.attacks.poisoning.gradient_matching_attack", "GradientMatchingAttack"),
    ("SleeperAgentAttack", "art.attacks.poisoning.sleeper_agent_attack", "SleeperAgentAttack"),
    (
        "MembershipInferenceBlackBox",
        "art.attacks.inference.membership_inference.black_box",
        "MembershipInferenceBlackBox",
    ),
    (
        "MembershipInferenceBlackBoxRuleBased",
        "art.attacks.inference.membership_inference.black_box_rule_based",
        "MembershipInferenceBlackBoxRuleBased",
    ),
    (
        "LabelOnlyDecisionBoundary",
        "art.attacks.inference.membership_inference.label_only_boundary_distance",
        "LabelOnlyDecisionBoundary",
    ),
    (
        "LabelOnlyGapAttack",
        "art.attacks.inference.membership_inference.label_only_gap_attack",
        "LabelOnlyGapAttack",
    ),
    (
        "ShadowModels",
        "art.attacks.inference.membership_inference.shadow_models",
        "ShadowModels",
    ),
    (
        "AttributeInferenceBlackBox",
        "art.attacks.inference.attribute_inference.black_box",
        "AttributeInferenceBlackBox",
    ),
    ("MIFace", "art.attacks.inference.model_inversion.mi_face", "MIFace"),
    (
        "DatabaseReconstruction",
        "art.attacks.inference.reconstruction.white_box",
        "DatabaseReconstruction",
    ),
    ("CopycatCNN", "art.attacks.extraction.copycat_cnn", "CopycatCNN"),
    ("KnockoffNets", "art.attacks.extraction.knockoff_nets", "KnockoffNets"),
    (
        "FunctionallyEquivalentExtraction",
        "art.attacks.extraction.functionally_equivalent_extraction",
        "FunctionallyEquivalentExtraction",
    ),
    (
        "ActivationDefence",
        "art.defences.detector.poison.activation_defence",
        "ActivationDefence",
    ),
    (
        "SpectralSignatureDefense",
        "art.defences.detector.poison.spectral_signature_defense",
        "SpectralSignatureDefense",
    ),
    (
        "ProvenanceDefense",
        "art.defences.detector.poison.provenance_defense",
        "ProvenanceDefense",
    ),
    ("RONIDefense", "art.defences.detector.poison.roni", "RONIDefense"),
    ("NeuralCleanse", "art.defences.transformer.poisoning.neural_cleanse", "NeuralCleanse"),
    ("STRIP", "art.defences.transformer.poisoning.strip", "STRIP"),
    (
        "KerasNeuralCleanse",
        "art.estimators.poison_mitigation.neural_cleanse.keras",
        "KerasNeuralCleanse",
    ),
    (
        "NeuralCleanseMixin",
        "art.estimators.poison_mitigation.neural_cleanse.neural_cleanse",
        "NeuralCleanseMixin",
    ),
    ("STRIPMixin", "art.estimators.poison_mitigation.strip.strip", "STRIPMixin"),
]

METHOD_HINTS = [
    "poison",
    "extract",
    "infer",
    "fit",
    "detect_poison",
    "evaluate_defence",
    "mitigate",
    "generate_shadow_dataset",
    "generate_synthetic_shadow_dataset",
    "calibrate_distance_threshold",
    "calibrate_distance_threshold_unsupervised",
    "backdoor_examples",
    "predict",
]


@dataclass
class InspectionResult:
    name: str
    module: str
    attr: str
    status: str
    signature: str | None = None
    doc_first_line: str | None = None
    methods: list[str] | None = None
    error: str | None = None


def inspect_target(name: str, module_path: str, attr_name: str) -> InspectionResult:
    try:
        module = importlib.import_module(module_path)
        obj: Any = getattr(module, attr_name)
        signature = str(inspect.signature(obj))
        doc = inspect.getdoc(obj)
        methods = [method for method in METHOD_HINTS if hasattr(obj, method)]
        return InspectionResult(
            name=name,
            module=module_path,
            attr=attr_name,
            status="ok",
            signature=signature,
            doc_first_line=(doc.splitlines()[0] if doc else None),
            methods=methods,
        )
    except Exception as exc:  # pragma: no cover - import failures depend on env
        return InspectionResult(
            name=name,
            module=module_path,
            attr=attr_name,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
        )


def render_text(results: list[InspectionResult]) -> str:
    lines: list[str] = []
    ok_count = sum(1 for item in results if item.status == "ok")
    lines.append(f"ok={ok_count} total={len(results)}")
    for item in results:
        if item.status == "ok":
            lines.append(f"[ok] {item.name}")
            lines.append(f"     {item.module}.{item.attr}")
            if item.signature:
                lines.append(f"     {item.signature}")
            if item.methods:
                lines.append(f"     methods: {', '.join(item.methods)}")
        else:
            lines.append(f"[err] {item.name}: {item.error}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely inspect ART poisoning, privacy inference, extraction, and mitigation APIs."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    results = [inspect_target(name, module_path, attr_name) for name, module_path, attr_name in TARGETS]
    payload = {
        "summary": {
            "ok": sum(1 for item in results if item.status == "ok"),
            "error": sum(1 for item in results if item.status != "ok"),
            "total": len(results),
        },
        "items": [asdict(item) for item in results],
    }

    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render_text(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
