#!/usr/bin/env python3
"""Print a compact snapshot of the public DeTikZify API surface."""

from importlib.metadata import version
from inspect import signature

from detikzify.infer import DetikzifyPipeline, TikzDocument
from detikzify.mcts.montecarlo import MonteCarlo
from detikzify.mcts.node import Node
from detikzify.model import DetikzifyProcessor, load, load_adapter
from detikzify.model.adapter import AdapterProcessor


def main() -> None:
    print(f"detikzify={version('detikzify')}")
    for label, obj in [
        ("load", load),
        ("load_adapter", load_adapter),
        ("DetikzifyPipeline.__init__", DetikzifyPipeline.__init__),
        ("DetikzifyPipeline.sample", DetikzifyPipeline.sample),
        ("DetikzifyPipeline.simulate", DetikzifyPipeline.simulate),
        ("TikzDocument.__init__", TikzDocument.__init__),
        ("TikzDocument.compile", TikzDocument.compile),
        ("TikzDocument.rasterize", TikzDocument.rasterize),
        ("TikzDocument.save", TikzDocument.save),
        ("DetikzifyProcessor.__call__", DetikzifyProcessor.__call__),
        ("AdapterProcessor.__call__", AdapterProcessor.__call__),
        ("Node.__init__", Node.__init__),
        ("MonteCarlo.__init__", MonteCarlo.__init__),
        ("MonteCarlo.simulate", MonteCarlo.simulate),
    ]:
        print(f"{label}: {signature(obj)}")


if __name__ == "__main__":
    main()
