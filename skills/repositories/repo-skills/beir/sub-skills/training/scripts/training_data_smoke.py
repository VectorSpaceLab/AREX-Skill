#!/usr/bin/env python3
"""No-download smoke test for BEIR training data mechanics.

This script validates BEIR TrainRetriever data preparation on tiny in-memory
fixtures. It intentionally avoids model downloads and does not call fit().
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path
from typing import Iterable


class ShimInputExample:
    """Minimal SentenceTransformers InputExample replacement for smoke checks."""

    def __init__(self, guid=None, texts=None, label=0):
        self.guid = guid
        self.texts = list(texts or [])
        self.label = label


class ShimSentenceEvaluator:
    pass


class ShimInformationRetrievalEvaluator(ShimSentenceEvaluator):
    def __init__(self, queries, corpus, relevant_docs, name=""):
        self.queries = queries
        self.corpus = corpus
        self.relevant_docs = relevant_docs
        self.name = name


class ShimSequentialEvaluator(ShimSentenceEvaluator):
    def __init__(self, evaluators, main_score_function=None):
        self.evaluators = evaluators
        self.main_score_function = main_score_function


class ShimDataLoader:
    def __init__(self, dataset, shuffle=False, batch_size=1):
        self.dataset = dataset
        self.shuffle = shuffle
        self.batch_size = batch_size

    def __iter__(self):
        return iter(self.dataset)

    def __len__(self):
        return len(self.dataset)


class ShimSentencesDataset(list):
    def __init__(self, examples, model=None):
        super().__init__(examples)
        self.model = model


class ShimNoDuplicatesDataLoader(ShimDataLoader):
    pass


def _allow_source_checkout_import() -> None:
    """Let the script run from a BEIR source checkout as well as an installed package."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() and (parent / "beir" / "retrieval" / "train.py").is_file():
            sys.path.insert(0, str(parent))
            return


def _install_sentence_transformers_shim() -> None:
    st_module = sys.modules.get("sentence_transformers") or types.ModuleType("sentence_transformers")
    datasets_module = types.ModuleType("sentence_transformers.datasets")
    readers_module = types.ModuleType("sentence_transformers.readers")
    evaluation_module = types.ModuleType("sentence_transformers.evaluation")

    datasets_module.NoDuplicatesDataLoader = ShimNoDuplicatesDataLoader
    readers_module.InputExample = ShimInputExample
    evaluation_module.InformationRetrievalEvaluator = ShimInformationRetrievalEvaluator
    evaluation_module.SentenceEvaluator = ShimSentenceEvaluator
    evaluation_module.SequentialEvaluator = ShimSequentialEvaluator

    st_module.SentencesDataset = getattr(st_module, "SentencesDataset", ShimSentencesDataset)
    st_module.SentenceTransformer = getattr(st_module, "SentenceTransformer", object)
    st_module.datasets = getattr(st_module, "datasets", datasets_module)

    sys.modules["sentence_transformers"] = st_module
    sys.modules["sentence_transformers.datasets"] = datasets_module
    sys.modules["sentence_transformers.readers"] = readers_module
    sys.modules["sentence_transformers.evaluation"] = evaluation_module


def _install_torch_shim_if_needed() -> None:
    try:
        import torch  # noqa: F401

        return
    except ModuleNotFoundError:
        pass

    torch_module = types.ModuleType("torch")
    nn_module = types.ModuleType("torch.nn")
    optim_module = types.ModuleType("torch.optim")
    utils_module = types.ModuleType("torch.utils")
    data_module = types.ModuleType("torch.utils.data")

    class Module:
        pass

    class Optimizer:
        pass

    nn_module.Module = Module
    optim_module.Optimizer = Optimizer
    data_module.DataLoader = ShimDataLoader
    utils_module.data = data_module
    torch_module.nn = nn_module
    torch_module.optim = optim_module
    torch_module.utils = utils_module

    sys.modules["torch"] = torch_module
    sys.modules["torch.nn"] = nn_module
    sys.modules["torch.optim"] = optim_module
    sys.modules["torch.utils"] = utils_module
    sys.modules["torch.utils.data"] = data_module


def _install_transformers_shim_or_patch() -> None:
    try:
        import transformers
    except ModuleNotFoundError:
        transformers = types.ModuleType("transformers")
        sys.modules["transformers"] = transformers

    if not hasattr(transformers, "AdamW"):
        class AdamW:
            pass

        transformers.AdamW = AdamW


def _install_tqdm_shim_if_needed() -> None:
    try:
        import tqdm.autonotebook  # noqa: F401

        return
    except ModuleNotFoundError:
        pass

    tqdm_module = types.ModuleType("tqdm")
    autonotebook_module = types.ModuleType("tqdm.autonotebook")

    def trange(*args, **kwargs):
        return range(*args)

    autonotebook_module.trange = trange
    tqdm_module.autonotebook = autonotebook_module
    sys.modules["tqdm"] = tqdm_module
    sys.modules["tqdm.autonotebook"] = autonotebook_module


def _install_training_dependency_shims() -> None:
    _install_sentence_transformers_shim()
    _install_torch_shim_if_needed()
    _install_transformers_shim_or_patch()
    _install_tqdm_shim_if_needed()


def _load_train_retriever():
    _allow_source_checkout_import()
    try:
        from beir.retrieval.train import TrainRetriever

        return TrainRetriever
    except (ImportError, ModuleNotFoundError):
        _install_training_dependency_shims()
        sys.modules.pop("beir.retrieval.train", None)
        from beir.retrieval.train import TrainRetriever

        return TrainRetriever


TrainRetriever = _load_train_retriever()

Corpus = dict[str, dict[str, str]]
Queries = dict[str, str]
Qrels = dict[str, dict[str, int]]
Triplet = tuple[str, str, str]


def positive_qrel_doc_ids(qrels: Qrels) -> set[str]:
    return {doc_id for doc_scores in qrels.values() for doc_id, score in doc_scores.items() if score >= 1}


def assert_training_qrels_resolve(corpus: Corpus, queries: Queries, qrels: Qrels) -> None:
    """Raise clear errors before BEIR silently skips missing training positives."""

    missing_query_ids = sorted(set(qrels) - set(queries))
    missing_positive_doc_ids = sorted(positive_qrel_doc_ids(qrels) - set(corpus))
    errors = []
    if missing_query_ids:
        errors.append(f"qrels reference missing query ids: {missing_query_ids}")
    if missing_positive_doc_ids:
        errors.append(f"positive qrels reference missing corpus ids: {missing_positive_doc_ids}")
    if errors:
        raise AssertionError("; ".join(errors))


def assert_triplets_are_text_triples(triplets: Iterable[object]) -> None:
    for index, triplet in enumerate(triplets):
        if not isinstance(triplet, tuple) or len(triplet) != 3:
            raise AssertionError(f"triplet {index} must be a 3-tuple of strings, got {triplet!r}")
        if not all(isinstance(part, str) and part for part in triplet):
            raise AssertionError(f"triplet {index} must contain three non-empty strings, got {triplet!r}")


def expect_error(expected: str, func, *args, **kwargs) -> str:
    try:
        func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - smoke helper reports exact BEIR failure text.
        message = str(exc)
        if expected not in message:
            raise AssertionError(f"expected error containing {expected!r}, got {type(exc).__name__}: {message}") from exc
        return message
    raise AssertionError(f"expected an error containing {expected!r}")


def build_toy_data() -> tuple[Corpus, Queries, Qrels]:
    corpus = {
        "d1": {"title": "Alpha", "text": "relevant passage about neural retrieval"},
        "d2": {"title": "Beta", "text": "non-relevant distractor"},
        "d3": {"title": "Gamma", "text": "another relevant passage"},
    }
    queries = {
        "q1": "neural retrieval question",
        "q2": "second training question",
    }
    qrels = {
        "q1": {"d1": 1, "d2": 0},
        "q2": {"d3": 2},
    }
    return corpus, queries, qrels


def run_smoke(exercise_max_corpus_error: bool) -> None:
    corpus, queries, qrels = build_toy_data()
    assert_training_qrels_resolve(corpus, queries, qrels)

    retriever = TrainRetriever(model=object(), batch_size=2)

    pair_samples = retriever.load_train(corpus, queries, qrels)
    assert len(pair_samples) == 2, pair_samples
    assert list(pair_samples[0].texts) == ["neural retrieval question", "Alpha relevant passage about neural retrieval"]
    assert pair_samples[0].label == 1
    assert list(pair_samples[1].texts) == ["second training question", "Gamma another relevant passage"]

    bad_qrels = {"q1": {"d-missing": 1}}
    missing_message = expect_error("missing corpus ids", assert_training_qrels_resolve, corpus, queries, bad_qrels)
    assert "d-missing" in missing_message

    triplets: list[Triplet] = [
        ("query text", "positive passage text", "hard negative passage text"),
        ("second query", "second positive", "second negative"),
    ]
    assert_triplets_are_text_triples(triplets)
    triplet_samples = retriever.load_train_triplets(triplets)
    assert len(triplet_samples) == 2
    assert list(triplet_samples[0].texts) == list(triplets[0])

    shape_message = expect_error(
        "3-tuple",
        assert_triplets_are_text_triples,
        [("query text", "positive only")],
    )
    assert "triplet 0" in shape_message

    evaluator = retriever.load_ir_evaluator(corpus, queries, qrels, max_corpus_size=3, name="toy-dev")
    assert evaluator is not None

    empty_message = expect_error("Dev Set Empty", retriever.load_ir_evaluator, corpus, {}, {}, name="empty-dev")
    assert "Cannot evaluate" in empty_message

    if exercise_max_corpus_error:
        max_size_message = expect_error(
            "maximum corpus size",
            retriever.load_ir_evaluator,
            corpus,
            queries,
            qrels,
            max_corpus_size=1,
            name="too-small",
        )
        assert "2 corpus ids" in max_size_message

    print("BEIR training smoke passed: pairs, triplets, evaluator guards, and preflight errors verified.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-download BEIR training data smoke checks.")
    parser.add_argument(
        "--exercise-max-corpus-error",
        action="store_true",
        help="Also assert BEIR's load_ir_evaluator max_corpus_size guard.",
    )
    args = parser.parse_args()
    run_smoke(exercise_max_corpus_error=args.exercise_max_corpus_error)


if __name__ == "__main__":
    main()
