#!/usr/bin/env python3
"""Run a trivial Monte Carlo tree-search expansion on dummy string states."""

from detikzify.mcts.montecarlo import MonteCarlo
from detikzify.mcts.node import Node


def child_finder(node, montecarlo):
    del montecarlo
    node.add_child(Node(f"{node.state} -> child"))


def node_evaluator(node, montecarlo):
    del montecarlo
    return 1 if str(node.state).endswith("child") else None


def main() -> None:
    root = Node("root")
    montecarlo = MonteCarlo(root)
    montecarlo.child_finder = child_finder
    montecarlo.node_evaluator = node_evaluator
    montecarlo.simulate(1)
    chosen = montecarlo.make_choice()
    print(f"expansions={montecarlo.stats_expansion_count}")
    print(f"failed_expansions={montecarlo.stats_failed_expansion_count}")
    print(f"root_visits={root.visits}")
    print(f"chosen={chosen.state}")
    if not root.children or chosen.state != root.children[0].state:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
