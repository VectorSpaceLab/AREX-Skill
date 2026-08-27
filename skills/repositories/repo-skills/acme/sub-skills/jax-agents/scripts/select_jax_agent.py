#!/usr/bin/env python3
"""Suggest Acme JAX agents from high-level task signals.

This helper is intentionally safe: it imports only Python standard-library
modules, so --help and recommendation runs work even when Acme/JAX extras are
not installed.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable, List, Sequence


CATALOG_REF = "references/agent-catalog.md"
WORKFLOW_REF = "references/experiment-workflows.md"
API_REF = "references/api-reference.md"
TROUBLESHOOTING_REF = "references/troubleshooting.md"


@dataclass(frozen=True)
class Candidate:
    identifier: str
    family: str
    package: str
    config: str
    builder: str
    setting: str
    action_spaces: Sequence[str]
    needs_demonstrations: bool
    multiagent: bool
    model_based: bool
    summary: str
    references: Sequence[str]


CANDIDATES: Sequence[Candidate] = (
    Candidate(
        "sac",
        "Soft Actor-Critic",
        "acme.agents.jax.sac",
        "SACConfig",
        "SACBuilder",
        "online",
        ("continuous",),
        False,
        False,
        False,
        "Strong default for online bounded continuous-control actor-critic workflows.",
        (CATALOG_REF, WORKFLOW_REF, API_REF),
    ),
    Candidate(
        "d4pg",
        "Distributed Distributional DDPG",
        "acme.agents.jax.d4pg",
        "D4PGConfig",
        "D4PGBuilder",
        "online",
        ("continuous",),
        False,
        False,
        False,
        "Use for distributed deterministic continuous control with a distributional critic.",
        (CATALOG_REF, WORKFLOW_REF, TROUBLESHOOTING_REF),
    ),
    Candidate(
        "td3",
        "Twin Delayed DDPG",
        "acme.agents.jax.td3",
        "TD3Config",
        "TD3Builder",
        "online",
        ("continuous",),
        False,
        False,
        False,
        "Deterministic continuous-control option; can add BC regularization with TD3Config.bc_alpha.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "mpo",
        "Maximum a Posteriori Policy Optimization",
        "acme.agents.jax.mpo",
        "MPOConfig",
        "MPOBuilder",
        "online",
        ("continuous", "discrete"),
        False,
        False,
        False,
        "Policy optimization with KL constraints, mixed replay, and categorical/Gaussian policies.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "wpo",
        "Wasserstein Policy Optimization",
        "acme.agents.jax.wpo",
        "WPOConfig",
        "WPOBuilder",
        "online",
        ("continuous",),
        False,
        False,
        False,
        "MPO-derived online continuous-control optimizer for WPO-style updates.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "ppo",
        "Proximal Policy Optimization",
        "acme.agents.jax.ppo",
        "PPOConfig",
        "PPOBuilder",
        "online",
        ("continuous", "discrete"),
        False,
        False,
        False,
        "Policy-gradient baseline for continuous or discrete action spaces.",
        (CATALOG_REF, WORKFLOW_REF, API_REF),
    ),
    Candidate(
        "dqn",
        "Deep Q-Network",
        "acme.agents.jax.dqn",
        "DQNConfig",
        "DQNBuilder or DistributionalDQNBuilder",
        "online",
        ("discrete",),
        False,
        False,
        False,
        "Value-based discrete-control baseline with prioritized replay and DQN variants.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "impala",
        "IMPALA",
        "acme.agents.jax.impala",
        "IMPALAConfig",
        "IMPALABuilder",
        "online",
        ("discrete",),
        False,
        False,
        False,
        "Discrete actor-learner architecture, especially for Atari-style recurrent workflows.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "r2d2",
        "Recurrent Replay Distributed DQN",
        "acme.agents.jax.r2d2",
        "R2D2Config",
        "R2D2Builder",
        "online",
        ("discrete",),
        False,
        False,
        False,
        "Choose for recurrent discrete value learning with sequence replay.",
        (CATALOG_REF, TROUBLESHOOTING_REF, API_REF),
    ),
    Candidate(
        "bc",
        "Behavior Cloning",
        "acme.agents.jax.bc",
        "BCConfig",
        "BCBuilder",
        "offline",
        ("continuous", "discrete"),
        True,
        False,
        False,
        "Supervised imitation from fixed observation/action demonstrations.",
        (CATALOG_REF, WORKFLOW_REF, API_REF),
    ),
    Candidate(
        "cql",
        "Conservative Q-Learning",
        "acme.agents.jax.cql",
        "CQLConfig",
        "CQLBuilder",
        "offline",
        ("continuous",),
        True,
        False,
        False,
        "Offline continuous RL with conservative critic regularization and no training env interaction.",
        (CATALOG_REF, WORKFLOW_REF, TROUBLESHOOTING_REF),
    ),
    Candidate(
        "crr",
        "Critic-Regularized Regression",
        "acme.agents.jax.crr",
        "CRRConfig",
        "CRRBuilder",
        "offline",
        ("continuous",),
        True,
        False,
        False,
        "Offline continuous policy learning from data using critic-regularized regression.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "bve",
        "Behavior Value Estimation",
        "acme.agents.jax.bve",
        "BVEConfig",
        "BVEBuilder",
        "offline",
        ("discrete",),
        True,
        False,
        False,
        "Offline value estimation with DQN-style networks and one-step policy improvement.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "mbop",
        "Model-Based Offline Planning",
        "acme.agents.jax.mbop",
        "MBOPConfig",
        "MBOPBuilder",
        "offline",
        ("continuous",),
        True,
        False,
        True,
        "Model-based offline planning with learned ensembles and MPPI control.",
        (CATALOG_REF, WORKFLOW_REF, TROUBLESHOOTING_REF),
    ),
    Candidate(
        "ail",
        "Adversarial Imitation Learning",
        "acme.agents.jax.ail",
        "AILConfig, GAILConfig, or DACConfig",
        "AILBuilder, GAILBuilder, or DACBuilder",
        "imitation",
        ("continuous", "discrete"),
        True,
        False,
        False,
        "Adversarial imitation wrapper around a direct RL ActorLearnerBuilder.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "sqil",
        "Soft Q Imitation Learning",
        "acme.agents.jax.sqil",
        "direct RL config plus SQIL builder args",
        "SQILBuilder",
        "imitation",
        ("continuous", "discrete"),
        True,
        False,
        False,
        "SQIL imitation wrapper around an off-policy direct RL builder.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "pwil",
        "Primal Wasserstein Imitation Learning",
        "acme.agents.jax.pwil",
        "PWILConfig and PWILDemonstrations",
        "PWILBuilder",
        "imitation",
        ("continuous", "discrete"),
        True,
        False,
        False,
        "Distance-based imitation reward wrapper with demonstration replay prefill.",
        (CATALOG_REF, TROUBLESHOOTING_REF),
    ),
    Candidate(
        "sacfd-td3fd",
        "Learning from Demonstrations",
        "acme.agents.jax.lfd",
        "LfdConfig plus SACfDConfig or TD3fDConfig",
        "SACfDBuilder or TD3fDBuilder",
        "learning-from-demonstrations",
        ("continuous",),
        True,
        False,
        False,
        "Use when demonstrations include environment rewards and should augment SAC or TD3 replay.",
        (CATALOG_REF, API_REF),
    ),
    Candidate(
        "decentralized-multiagent",
        "Decentralized Multiagent Learning",
        "acme.agents.jax.multiagent.decentralized",
        "DecentralizedMultiagentConfig",
        "DecentralizedMultiAgentBuilder",
        "online",
        ("continuous", "discrete", "mixed"),
        False,
        True,
        False,
        "Homogeneous decentralized sub-agents for dict-style multiagent environments.",
        (CATALOG_REF, WORKFLOW_REF, TROUBLESHOOTING_REF),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recommend Acme JAX agents from task signals without importing Acme.",
    )
    parser.add_argument(
        "--action-space",
        choices=("continuous", "discrete", "mixed", "unknown"),
        default="unknown",
        help="Dominant action-space type for the target environment or dataset.",
    )
    parser.add_argument(
        "--setting",
        choices=("online", "offline", "imitation", "learning-from-demonstrations", "unknown"),
        default="unknown",
        help="Training setting: env interaction, fixed data, imitation, or LfD.",
    )
    parser.add_argument(
        "--needs-demonstrations",
        action="store_true",
        help="Set when the workflow depends on demonstrations or fixed datasets.",
    )
    parser.add_argument(
        "--multiagent",
        action="store_true",
        help="Set when observations/rewards/actions are keyed by agent ids.",
    )
    parser.add_argument(
        "--model-based",
        action="store_true",
        help="Set when the task asks for learned dynamics/planning/model-based control.",
    )
    parser.add_argument(
        "--prefer-distributed",
        action="store_true",
        help="Boost agents/workflows commonly used with distributed Launchpad execution.",
    )
    parser.add_argument(
        "--avoid-environment-interaction",
        action="store_true",
        help="Boost offline learner-only candidates and warn against online runners.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Maximum number of candidates to print.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args()


def score_candidate(candidate: Candidate, args: argparse.Namespace) -> int:
    score = 0

    if args.multiagent:
        score += 12 if candidate.multiagent else -8
    elif candidate.multiagent:
        score -= 4

    if args.model_based:
        score += 10 if candidate.model_based else -3
    elif candidate.model_based:
        score -= 1

    if args.action_space != "unknown":
        if args.action_space in candidate.action_spaces or "mixed" in candidate.action_spaces:
            score += 4
        elif args.action_space == "mixed" and len(candidate.action_spaces) > 1:
            score += 3
        else:
            score -= 5

    if args.setting != "unknown":
        if args.setting == candidate.setting:
            score += 7
        elif args.setting == "offline" and candidate.setting in ("imitation", "learning-from-demonstrations"):
            score += 2
        elif args.setting == "imitation" and candidate.needs_demonstrations:
            score += 2
        elif args.setting == "online" and candidate.setting == "learning-from-demonstrations":
            score += 1
        else:
            score -= 4

    if args.needs_demonstrations:
        score += 5 if candidate.needs_demonstrations else -2
    elif candidate.setting in ("imitation", "learning-from-demonstrations"):
        score -= 2

    if args.avoid_environment_interaction:
        score += 6 if candidate.setting == "offline" else -4

    if args.prefer_distributed:
        if candidate.setting == "online" and candidate.builder != "BCBuilder":
            score += 2
        if candidate.identifier in {"d4pg", "impala", "r2d2", "decentralized-multiagent"}:
            score += 2

    if candidate.identifier == "sac" and args.setting in ("online", "unknown") and args.action_space in ("continuous", "unknown"):
        score += 1
    if candidate.identifier == "dqn" and args.action_space == "discrete" and args.setting in ("online", "unknown"):
        score += 1
    if candidate.identifier == "bc" and args.needs_demonstrations and args.setting in ("offline", "imitation", "unknown"):
        score += 1

    return score


def candidate_to_dict(candidate: Candidate, score: int) -> dict:
    return {
        "id": candidate.identifier,
        "score": score,
        "family": candidate.family,
        "package": candidate.package,
        "config": candidate.config,
        "builder": candidate.builder,
        "setting": candidate.setting,
        "action_spaces": list(candidate.action_spaces),
        "summary": candidate.summary,
        "references": list(candidate.references),
    }


def warnings_for(args: argparse.Namespace, selected: Sequence[Candidate]) -> List[str]:
    warnings: List[str] = []
    if args.avoid_environment_interaction or args.setting == "offline":
        warnings.append(
            "Use OfflineExperimentConfig/run_offline_experiment or make_distributed_offline_experiment; do not collect training environment steps."
        )
    if args.prefer_distributed:
        warnings.append(
            "Distributed JAX experiments require the shared Launchpad/Reverb/TensorFlow stack from the JAX extra."
        )
    if args.model_based and not any(candidate.model_based for candidate in selected):
        warnings.append("No model-based candidate was selected; inspect MBOP if planning from an offline dataset is intended.")
    if args.multiagent and not any(candidate.multiagent for candidate in selected):
        warnings.append("No multiagent candidate was selected; inspect decentralized multiagent support for dict-style multiagent environments.")
    return warnings


def print_text(results: Sequence[dict], warnings: Iterable[str]) -> None:
    print("Acme JAX agent recommendations")
    print("================================")
    for index, result in enumerate(results, start=1):
        print(f"\n{index}. {result['id']} — {result['family']} (score {result['score']})")
        print(f"   package: {result['package']}")
        print(f"   config:  {result['config']}")
        print(f"   builder: {result['builder']}")
        print(f"   why:     {result['summary']}")
        print(f"   refs:    {', '.join(result['references'])}")
    warning_list = list(warnings)
    if warning_list:
        print("\nNotes")
        print("-----")
        for warning in warning_list:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    scored = [(candidate, score_candidate(candidate, args)) for candidate in CANDIDATES]
    scored.sort(key=lambda item: (item[1], item[0].identifier), reverse=True)
    top_n = max(args.top, 1)
    selected = [candidate for candidate, score in scored[:top_n] if score > -10]
    if not selected:
        selected = [scored[0][0]]
    selected_scores = {candidate.identifier: score for candidate, score in scored}
    results = [candidate_to_dict(candidate, selected_scores[candidate.identifier]) for candidate in selected]
    warnings = warnings_for(args, selected)

    if args.format == "json":
        print(json.dumps({"recommendations": results, "notes": warnings}, indent=2, sort_keys=True))
    else:
        print_text(results, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
