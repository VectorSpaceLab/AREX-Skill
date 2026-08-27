#!/usr/bin/env python3
"""Tiny no-download smoke check for NLTK grammar/parsing/semantics APIs.

The check uses only in-memory grammars, token/tag lists, dependency strings,
and logic/DRT expressions. It does not call nltk.download(), read NLTK data
resources, start Java/server wrappers, or invoke external prover binaries.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic no-download NLTK grammar/parse/semantics smoke "
            "check using only tiny in-memory fixtures."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a short text summary.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the text summary on success unless --json is also set.",
    )
    return parser


def _load_nltk_modules() -> dict[str, Any]:
    try:
        import nltk
        from nltk import CFG
        from nltk.chunk import RegexpParser
        from nltk.chunk.util import tree2conlltags
        from nltk.grammar import FeatureGrammar, PCFG
        from nltk.parse import (
            ChartParser,
            DependencyEvaluator,
            DependencyGraph,
            FeatureChartParser,
            RecursiveDescentParser,
            ShiftReduceParser,
            ViterbiParser,
        )
        from nltk.sem import Assignment, Model, Valuation
        from nltk.sem.drt import DrtExpression
        from nltk.sem.logic import Expression
        from nltk.tree import Tree
    except Exception as exc:  # pragma: no cover - depends on runtime install
        print(f"ERROR: could not import required NLTK modules: {exc}", file=sys.stderr)
        sys.exit(3)

    return {
        "nltk": nltk,
        "CFG": CFG,
        "PCFG": PCFG,
        "FeatureGrammar": FeatureGrammar,
        "ChartParser": ChartParser,
        "RecursiveDescentParser": RecursiveDescentParser,
        "ShiftReduceParser": ShiftReduceParser,
        "ViterbiParser": ViterbiParser,
        "FeatureChartParser": FeatureChartParser,
        "RegexpParser": RegexpParser,
        "tree2conlltags": tree2conlltags,
        "Tree": Tree,
        "DependencyGraph": DependencyGraph,
        "DependencyEvaluator": DependencyEvaluator,
        "Expression": Expression,
        "Valuation": Valuation,
        "Model": Model,
        "Assignment": Assignment,
        "DrtExpression": DrtExpression,
    }


def run_smoke() -> dict[str, Any]:
    m = _load_nltk_modules()

    nltk = m["nltk"]
    CFG = m["CFG"]
    PCFG = m["PCFG"]
    FeatureGrammar = m["FeatureGrammar"]
    ChartParser = m["ChartParser"]
    RecursiveDescentParser = m["RecursiveDescentParser"]
    ShiftReduceParser = m["ShiftReduceParser"]
    ViterbiParser = m["ViterbiParser"]
    FeatureChartParser = m["FeatureChartParser"]
    RegexpParser = m["RegexpParser"]
    tree2conlltags = m["tree2conlltags"]
    Tree = m["Tree"]
    DependencyGraph = m["DependencyGraph"]
    DependencyEvaluator = m["DependencyEvaluator"]
    Expression = m["Expression"]
    Valuation = m["Valuation"]
    Model = m["Model"]
    Assignment = m["Assignment"]
    DrtExpression = m["DrtExpression"]

    tokens = "I saw John".split()

    cfg = CFG.fromstring(
        """
        % start S
        S -> NP VP
        NP -> 'I' | 'John'
        VP -> V NP
        V -> 'saw'
        """
    )
    cfg.check_coverage(tokens)
    chart_trees = list(ChartParser(cfg).parse(tokens))
    rd_trees = list(RecursiveDescentParser(cfg).parse(tokens))
    sr_trees = list(ShiftReduceParser(cfg).parse(tokens))
    assert len(chart_trees) == 1
    assert len(rd_trees) == 1
    assert len(sr_trees) == 1
    assert chart_trees[0].leaves() == tokens

    coverage_error = False
    try:
        cfg.check_coverage(["I", "saw", "Mary"])
    except ValueError:
        coverage_error = True
    assert coverage_error

    ambiguous = CFG.fromstring("S -> S S | 'a'")
    ambiguous_count = len(list(ChartParser(ambiguous).parse(["a", "a", "a"])))
    assert ambiguous_count == 2

    pcfg = PCFG.fromstring(
        """
        S -> NP VP [1.0]
        NP -> 'I' [0.5] | 'John' [0.5]
        VP -> V NP [1.0]
        V -> 'saw' [1.0]
        """
    )
    viterbi_trees = list(ViterbiParser(pcfg).parse(tokens))
    assert len(viterbi_trees) == 1
    assert round(viterbi_trees[0].prob(), 6) == 0.25

    feature_grammar = FeatureGrammar.fromstring(
        "% start S\nS[SEM=<see(speaker,john)>] -> 'I' 'saw' 'John'"
    )
    feature_tree = next(FeatureChartParser(feature_grammar).parse(tokens))
    semrep = str(feature_tree.label()["SEM"])
    assert semrep == "see(speaker,john)"

    tagged = [("the", "DT"), ("quick", "JJ"), ("dog", "NN"), ("saw", "VBD"), ("John", "NNP")]
    chunk_tree = RegexpParser("NP: {<DT>?<JJ>*<NN.*>+}").parse(tagged)
    chunk_tags = tree2conlltags(chunk_tree)
    chunk_iobs = [iob for _, _, iob in chunk_tags]
    assert chunk_iobs == ["B-NP", "I-NP", "I-NP", "O", "B-NP"]

    tree = Tree.fromstring("(S (NP I) (VP (V saw) (NP John)))")
    assert tree.leaves() == tokens
    assert tree[1, 1].label() == "NP"
    assert str(tree.productions()[0]) == "S -> NP VP"

    dep_record = """I PRP 2 SBJ
saw VBD 0 ROOT
John NNP 2 OBJ
"""
    dep_graph = DependencyGraph(dep_record)
    assert str(dep_graph.tree()) == "(saw I John)"
    las, uas = DependencyEvaluator([dep_graph], [dep_graph]).eval()
    assert (las, uas) == (1.0, 1.0)

    val = Valuation([("fido", "d1"), ("dog", {"d1"}), ("bark", {"d1"})])
    model = Model(val.domain, val)
    assignment = Assignment(val.domain)
    expr = Expression.fromstring("exists x.(dog(x) & bark(x))")
    truth = model.evaluate(str(expr), assignment)
    assert truth is True
    satisfiers = sorted(model.satisfiers(Expression.fromstring("dog(x)"), "x", assignment))
    assert satisfiers == ["d1"]

    drs = DrtExpression.fromstring("([x],[dog(x), bark(x)])")
    drs_fol = str(drs.fol())
    assert drs_fol == "exists x.(dog(x) & bark(x))"

    return {
        "status": "ok",
        "python": platform.python_version(),
        "executable": sys.executable,
        "nltk_version": getattr(nltk, "__version__", "unknown"),
        "nltk_file": getattr(nltk, "__file__", "unknown"),
        "cfg_chart_parses": len(chart_trees),
        "cfg_recursive_descent_parses": len(rd_trees),
        "cfg_shift_reduce_parses": len(sr_trees),
        "coverage_error_checked": coverage_error,
        "ambiguous_chart_parses_for_three_a": ambiguous_count,
        "viterbi_best_prob": viterbi_trees[0].prob(),
        "feature_semrep": semrep,
        "chunk_iobs": chunk_iobs,
        "tree_first_production": str(tree.productions()[0]),
        "dependency_tree": str(dep_graph.tree()),
        "dependency_las_uas": [las, uas],
        "logic_truth": truth,
        "logic_satisfiers": satisfiers,
        "drt_fol": drs_fol,
        "external_wrappers_invoked": False,
        "downloads_invoked": False,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif not args.quiet:
        print("OK: grammar-parse-semantics smoke passed")
        for key in [
            "nltk_version",
            "cfg_chart_parses",
            "ambiguous_chart_parses_for_three_a",
            "viterbi_best_prob",
            "feature_semrep",
            "dependency_las_uas",
            "logic_truth",
            "drt_fol",
        ]:
            print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
