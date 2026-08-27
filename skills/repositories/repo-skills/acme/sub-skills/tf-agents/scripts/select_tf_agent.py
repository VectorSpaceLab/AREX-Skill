#!/usr/bin/env python3
"""Select candidate Acme TensorFlow agents without importing TensorFlow.

This helper maps task signals to Acme TF/Sonnet agent families and example
patterns. It is intentionally metadata-only so `--help` and normal selection
work in environments that do not have TensorFlow, Reverb, Launchpad, or Sonnet
installed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set


@dataclass(frozen=True)
class Candidate:
    key: str
    display: str
    module: str
    entry_points: str
    action_spaces: Set[str]
    settings: Set[str]
    needs: Set[str]
    examples: str
    notes: str


CANDIDATES: Sequence[Candidate] = (
    Candidate(
        key="dqn",
        display="DQN / DistributedDQN",
        module="acme.agents.tf.dqn",
        entry_points="DQN(...), DistributedDQN(...).build(name='dqn')",
        action_spaces={"discrete"},
        settings={"online", "single", "distributed", "bsuite", "openspiel"},
        needs={"q-learning", "baseline"},
        examples="Bsuite DQN; OpenSpiel DQN with legal-action masking",
        notes="Default discrete-action Q-learning choice.",
    ),
    Candidate(
        key="r2d2",
        display="R2D2 / DistributedR2D2",
        module="acme.agents.tf.r2d2",
        entry_points="R2D2(...), DistributedR2D2(...).build(name='r2d2')",
        action_spaces={"discrete"},
        settings={"online", "single", "distributed", "atari"},
        needs={"recurrent", "sequence-replay", "memory"},
        examples="Recurrent replay distributed DQN family",
        notes="Use for partial observability or LSTM state with burn-in/trace sequences.",
    ),
    Candidate(
        key="impala",
        display="IMPALA / DistributedIMPALA",
        module="acme.agents.tf.impala",
        entry_points="IMPALA(...), DistributedIMPALA(...).build(name='impala')",
        action_spaces={"discrete"},
        settings={"online", "single", "distributed", "bsuite", "atari"},
        needs={"actor-learner", "throughput", "recurrent"},
        examples="Bsuite IMPALA; Atari IMPALA-style recurrent policy/value network",
        notes="Use when actor throughput and sequence actor-learner architecture matter.",
    ),
    Candidate(
        key="mcts",
        display="MCTS / DistributedMCTS",
        module="acme.agents.tf.mcts",
        entry_points="MCTS(...), DistributedMCTS(...).build(name='MCTS')",
        action_spaces={"discrete"},
        settings={"online", "single", "distributed", "bsuite"},
        needs={"planning", "model-based", "simulator"},
        examples="Bsuite MCTS with simulator or learned model",
        notes="Use for model-based planning with a simulator/model and policy-value network.",
    ),
    Candidate(
        key="ddpg",
        display="DDPG / DistributedDDPG",
        module="acme.agents.tf.ddpg",
        entry_points="DDPG(...), DistributedDDPG(...).build(name='ddpg')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed", "control-suite"},
        needs={"deterministic-policy", "actor-critic"},
        examples="Control Suite DDPG Launchpad family",
        notes="Simpler deterministic actor-critic baseline for bounded continuous actions.",
    ),
    Candidate(
        key="d4pg",
        display="D4PG / DistributedD4PG",
        module="acme.agents.tf.d4pg",
        entry_points="D4PG(...), DistributedD4PG(...).build(name='d4pg')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed", "control-suite"},
        needs={"distributional-critic", "deterministic-policy", "actor-critic"},
        examples="Control Suite D4PG Launchpad family",
        notes="Use deterministic policy with a C51-style distributional critic.",
    ),
    Candidate(
        key="mpo",
        display="MPO / DistributedMPO",
        module="acme.agents.tf.mpo",
        entry_points="MPO(...), DistributedMPO(...).build(name='mpo')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed", "control-suite"},
        needs={"stochastic-policy", "mpo-loss", "actor-critic"},
        examples="Control Suite MPO Launchpad family",
        notes="Use stochastic policies and MPO KL-constrained policy improvement.",
    ),
    Candidate(
        key="dmpo",
        display="DistributionalMPO / DistributedDistributionalMPO",
        module="acme.agents.tf.dmpo",
        entry_points="DistributionalMPO(...), DistributedDistributionalMPO(...).build(name='dmpo')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed", "control-suite", "pixels"},
        needs={"stochastic-policy", "mpo-loss", "distributional-critic", "pixels"},
        examples="Control Suite DMPO; pixels and DRQ-v2-style DMPO families",
        notes="Use MPO-style policy improvement with a distributional critic.",
    ),
    Candidate(
        key="mompo",
        display="MultiObjectiveMPO / DistributedMultiObjectiveMPO",
        module="acme.agents.tf.mompo",
        entry_points="MultiObjectiveMPO(...), DistributedMultiObjectiveMPO(...).build(name='mompo')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed"},
        needs={"multi-objective", "mpo-loss", "stochastic-policy"},
        examples="Multi-objective MPO with reward and Q-value objectives",
        notes="Use for per-objective reward/Q constraints rather than a single scalar objective.",
    ),
    Candidate(
        key="mog-mpo",
        display="DistributedMoGMPO",
        module="acme.agents.tf.mog_mpo",
        entry_points="DistributedMoGMPO(...).build(name='dmpo')",
        action_spaces={"continuous"},
        settings={"online", "distributed", "control-suite"},
        needs={"mixture-of-gaussians", "distributional-critic", "mpo-loss"},
        examples="Distributed MoG distributional MPO family",
        notes="Distributed-only TF family for mixture-of-Gaussians critic variants.",
    ),
    Candidate(
        key="svg0-prior",
        display="SVG0 / DistributedSVG0",
        module="acme.agents.tf.svg0_prior",
        entry_points="SVG0(...), DistributedSVG0(...).build(name='svg0')",
        action_spaces={"continuous"},
        settings={"online", "single", "distributed", "control-suite"},
        needs={"prior-policy", "distillation", "actor-critic"},
        examples="Control Suite SVG0 with prior Launchpad family",
        notes="Use when a learned policy is regularized or distilled against a prior network.",
    ),
    Candidate(
        key="dqfd",
        display="DQfD",
        module="acme.agents.tf.dqfd",
        entry_points="DQfD(..., demonstration_dataset=..., demonstration_ratio=...)",
        action_spaces={"discrete"},
        settings={"online", "single", "demonstrations"},
        needs={"demonstrations", "q-learning"},
        examples="Offline/online demonstrations for discrete DQN-style learning",
        notes="Use for Deep Q-learning from Demonstrations.",
    ),
    Candidate(
        key="r2d3",
        display="R2D3",
        module="acme.agents.tf.r2d3",
        entry_points="R2D3(..., demonstration_dataset=..., demonstration_ratio=...)",
        action_spaces={"discrete"},
        settings={"online", "single", "demonstrations"},
        needs={"demonstrations", "recurrent", "sequence-replay"},
        examples="Recurrent replay distributed DQN from demonstrations",
        notes="Use when demonstrations and recurrent state are both needed.",
    ),
    Candidate(
        key="bc",
        display="BCLearner",
        module="acme.agents.tf.bc.learning",
        entry_points="BCLearner(network, learning_rate, dataset, counter, logger, checkpoint)",
        action_spaces={"discrete", "continuous", "any"},
        settings={"offline", "learner-only", "imitation"},
        needs={"behavior-cloning", "supervised"},
        examples="Offline behavior cloning learner",
        notes="Use for learner-only supervised imitation from dataset batches.",
    ),
    Candidate(
        key="bcq",
        display="DiscreteBCQLearner",
        module="acme.agents.tf.bcq.discrete_learning",
        entry_points="DiscreteBCQLearner(network, dataset, learning_rate, counter, bc_logger, bcq_logger, **kwargs)",
        action_spaces={"discrete"},
        settings={"offline", "learner-only"},
        needs={"offline-rl", "behavior-constraint", "q-learning"},
        examples="Offline discrete BCQ learner",
        notes="Use for discrete offline Q-learning constrained by behavior cloning.",
    ),
    Candidate(
        key="iqn",
        display="IQNLearner",
        module="acme.agents.tf.iqn.learning",
        entry_points="IQNLearner(network, target_network, discount, importance_sampling_exponent, ...)",
        action_spaces={"discrete"},
        settings={"offline", "learner-only", "online-component"},
        needs={"quantile", "distributional", "q-learning"},
        examples="Implicit Quantile Network learner component",
        notes="Use when adapting quantile/distributional DQN-style learning.",
    ),
    Candidate(
        key="rcrr",
        display="RCRRLearner",
        module="acme.agents.tf.crr.recurrent_learning",
        entry_points="RCRRLearner(policy_network, critic_network, target_policy_network, target_critic_network, dataset, ...)",
        action_spaces={"continuous", "discrete", "any"},
        settings={"offline", "learner-only"},
        needs={"crr", "recurrent", "offline-rl"},
        examples="Recurrent Critic-Regularized Regression learner component",
        notes="Use for recurrent offline CRR learner adaptation.",
    ),
)


ALIASES = {
    "control": "control-suite",
    "dm-control": "control-suite",
    "launchpad": "distributed",
    "lp": "distributed",
    "demo": "demonstrations",
    "demonstration": "demonstrations",
    "demos": "demonstrations",
    "rnn": "recurrent",
    "lstm": "recurrent",
    "memory": "recurrent",
    "legal-actions": "openspiel",
    "legal-action": "openspiel",
    "open-spiel": "openspiel",
    "pixel": "pixels",
    "image": "pixels",
    "images": "pixels",
    "tf": "online",
}


def normalize(values: Iterable[str]) -> Set[str]:
    normalized: Set[str] = set()
    for value in values:
        for raw in value.replace(",", " ").split():
            key = raw.strip().lower().replace("_", "-")
            if key:
                normalized.add(ALIASES.get(key, key))
    return normalized


def score_candidate(candidate: Candidate, action_space: str, setting: str, signals: Set[str]) -> int:
    score = 0
    if action_space == "any" or action_space in candidate.action_spaces or "any" in candidate.action_spaces:
        score += 4
    elif action_space != "unknown":
        score -= 5
    if setting == "any" or setting in candidate.settings:
        score += 3
    elif setting != "unknown":
        score -= 3
    score += 2 * len(signals & candidate.needs)
    score += len(signals & candidate.settings)
    score += len(signals & candidate.action_spaces)
    return score


def select_candidates(action_space: str, setting: str, signals: Set[str], limit: int) -> List[tuple[int, Candidate]]:
    ranked = [
        (score_candidate(candidate, action_space, setting, signals), candidate)
        for candidate in CANDIDATES
    ]
    ranked.sort(key=lambda item: (-item[0], item[1].key))
    return [item for item in ranked if item[0] > 0][:limit]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Map task signals to candidate Acme TensorFlow/Sonnet agents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--action-space",
        choices=["continuous", "discrete", "any", "unknown"],
        default="unknown",
        help="Environment action-space type.",
    )
    parser.add_argument(
        "--setting",
        choices=[
            "online",
            "offline",
            "single",
            "distributed",
            "learner-only",
            "control-suite",
            "bsuite",
            "openspiel",
            "atari",
            "demonstrations",
            "any",
            "unknown",
        ],
        default="unknown",
        help="Primary run or example setting.",
    )
    parser.add_argument(
        "--needs",
        nargs="*",
        default=(),
        help=(
            "Extra signals, e.g. recurrent, distributional-critic, mpo-loss, "
            "pixels, legal-actions, behavior-cloning, demonstrations."
        ),
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum candidates to print.")
    parser.add_argument("--list-signals", action="store_true", help="Print known signals and exit.")
    return parser


def print_signals() -> None:
    signals = sorted(set().union(*(c.needs | c.settings | c.action_spaces for c in CANDIDATES), set(ALIASES)))
    for signal in signals:
        print(signal)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_signals:
        print_signals()
        return 0

    signals = normalize(args.needs)
    ranked = select_candidates(args.action_space, args.setting, signals, max(args.limit, 1))
    if not ranked:
        print("No strong TF candidate matched. Check whether this is a JAX-only Acme task or provide more signals.")
        return 1

    print("Candidate Acme TF agents:\n")
    for index, (score, candidate) in enumerate(ranked, start=1):
        print(f"{index}. {candidate.display}  [score={score}]")
        print(f"   module: {candidate.module}")
        print(f"   entry:  {candidate.entry_points}")
        print(f"   examples: {candidate.examples}")
        print(f"   notes: {candidate.notes}")
    print("\nNext: read references/agent-catalog.md and references/network-and-saver-workflows.md for wiring details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
