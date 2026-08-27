#!/usr/bin/env python3
"""Static preflight checks for sentence-transformers training plans.

This script validates high-level routing choices without importing
sentence-transformers, downloading models, loading datasets, or running training.
It is meant to catch common model-type, data-shape, loss, evaluator, and sampler
mismatches before an agent writes a full training script.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Iterable


MODEL_TYPES = ("sentence-transformer", "cross-encoder", "sparse-encoder")
DATA_SHAPES = (
    "single-class",
    "pair-unlabeled",
    "pair-binary",
    "pair-class",
    "pair-score",
    "triplet-unlabeled",
    "ntuple-unlabeled",
    "listwise-scores",
    "teacher-embeddings",
    "teacher-margins",
    "teacher-distribution",
)


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


LOSS_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "sentence-transformer": {
        "single-class": ("BatchAllTripletLoss", "BatchHardTripletLoss", "BatchSemiHardTripletLoss", "BatchHardSoftMarginTripletLoss"),
        "pair-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss", "GISTEmbedLoss", "CachedGISTEmbedLoss"),
        "pair-binary": ("ContrastiveLoss", "OnlineContrastiveLoss"),
        "pair-class": ("SoftmaxLoss",),
        "pair-score": ("CoSENTLoss", "AnglELoss", "CosineSimilarityLoss"),
        "triplet-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss", "TripletLoss", "GISTEmbedLoss", "CachedGISTEmbedLoss"),
        "ntuple-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss", "GISTEmbedLoss", "CachedGISTEmbedLoss"),
        "teacher-embeddings": ("MSELoss", "EmbedDistillLoss"),
        "teacher-margins": ("MarginMSELoss",),
        "teacher-distribution": ("DistillKLDivLoss", "MarginMSELoss"),
    },
    "cross-encoder": {
        "pair-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss"),
        "pair-binary": ("BinaryCrossEntropyLoss",),
        "pair-class": ("CrossEntropyLoss",),
        "pair-score": ("BinaryCrossEntropyLoss", "MSELoss"),
        "triplet-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss"),
        "ntuple-unlabeled": ("MultipleNegativesRankingLoss", "CachedMultipleNegativesRankingLoss"),
        "listwise-scores": ("LambdaLoss", "PListMLELoss", "ListNetLoss", "RankNetLoss", "ListMLELoss", "ADRMSELoss"),
        "teacher-margins": ("MarginMSELoss",),
        "teacher-distribution": ("MarginMSELoss",),
    },
    "sparse-encoder": {
        "pair-unlabeled": ("SpladeLoss", "CachedSpladeLoss", "CSRLoss", "SparseMultipleNegativesRankingLoss"),
        "pair-score": ("SparseCoSENTLoss", "SparseAnglELoss", "SparseCosineSimilarityLoss"),
        "triplet-unlabeled": ("SpladeLoss", "CachedSpladeLoss", "SparseTripletLoss", "SparseMultipleNegativesRankingLoss"),
        "ntuple-unlabeled": ("SpladeLoss", "CachedSpladeLoss", "SparseMultipleNegativesRankingLoss"),
        "teacher-embeddings": ("SparseMSELoss",),
        "teacher-margins": ("SpladeLoss", "CachedSpladeLoss", "SparseMarginMSELoss"),
        "teacher-distribution": ("SpladeLoss", "CachedSpladeLoss", "SparseDistillKLDivLoss", "SparseMarginMSELoss"),
    },
}

EVALUATOR_HINTS: dict[str, tuple[str, ...]] = {
    "sentence-transformer": (
        "NanoBEIREvaluator",
        "InformationRetrievalEvaluator",
        "EmbeddingSimilarityEvaluator",
        "BinaryClassificationEvaluator",
        "TripletEvaluator",
        "RerankingEvaluator",
        "MSEEvaluator",
        "ParaphraseMiningEvaluator",
        "TranslationEvaluator",
        "LabelAccuracyEvaluator",
    ),
    "cross-encoder": (
        "CrossEncoderNanoBEIREvaluator",
        "CrossEncoderRerankingEvaluator",
        "CrossEncoderClassificationEvaluator",
        "CrossEncoderCorrelationEvaluator",
    ),
    "sparse-encoder": (
        "SparseNanoBEIREvaluator",
        "SparseInformationRetrievalEvaluator",
        "SparseEmbeddingSimilarityEvaluator",
        "SparseBinaryClassificationEvaluator",
        "SparseTripletEvaluator",
        "SparseRerankingEvaluator",
        "SparseMSEEvaluator",
        "SparseTranslationEvaluator",
        "ReciprocalRankFusionEvaluator",
    ),
}

CONTRASTIVE_LOSSES = {
    "MultipleNegativesRankingLoss",
    "CachedMultipleNegativesRankingLoss",
    "GISTEmbedLoss",
    "CachedGISTEmbedLoss",
    "SparseMultipleNegativesRankingLoss",
    "SpladeLoss",
    "CachedSpladeLoss",
}

TRIPLET_BATCH_LOSSES = {
    "BatchAllTripletLoss",
    "BatchHardTripletLoss",
    "BatchSemiHardTripletLoss",
    "BatchHardSoftMarginTripletLoss",
}

LISTWISE_OR_DISTILL_CE = {
    "LambdaLoss",
    "PListMLELoss",
    "ListNetLoss",
    "RankNetLoss",
    "ListMLELoss",
    "ADRMSELoss",
    "MSELoss",
    "MarginMSELoss",
}

SPARSE_WRAPPERS = {"SpladeLoss", "CachedSpladeLoss", "CSRLoss", "SparseMSELoss"}


def normalize_loss(loss: str) -> str:
    return loss.rsplit(".", 1)[-1].strip()


def contains_any(value: str | None, names: Iterable[str]) -> bool:
    if not value:
        return False
    return any(name.lower() in value.lower() for name in names)


def check_plan(args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    loss = normalize_loss(args.loss)
    allowed = LOSS_RULES.get(args.model_type, {}).get(args.data_shape, ())

    if not allowed:
        findings.append(
            Finding(
                "ERROR",
                f"No standard {args.model_type} loss route is defined for data shape {args.data_shape!r}; reshape data or choose another model type.",
            )
        )
    elif loss not in allowed:
        findings.append(
            Finding(
                "ERROR",
                f"{loss} is unusual for {args.model_type} with {args.data_shape}; expected one of: {', '.join(allowed)}.",
            )
        )
    else:
        findings.append(Finding("OK", f"Loss {loss} matches {args.model_type} / {args.data_shape}."))

    evaluator_choices = EVALUATOR_HINTS[args.model_type]
    if args.evaluator:
        evaluator = normalize_loss(args.evaluator)
        if evaluator not in evaluator_choices:
            findings.append(
                Finding(
                    "WARN",
                    f"Evaluator {evaluator} is not a typical {args.model_type} evaluator. Typical choices: {', '.join(evaluator_choices)}.",
                )
            )
        else:
            findings.append(Finding("OK", f"Evaluator {evaluator} matches {args.model_type}."))
    else:
        findings.append(Finding("WARN", "No evaluator provided; add one for baseline and best-checkpoint selection."))

    if loss in CONTRASTIVE_LOSSES and args.model_type in {"sentence-transformer", "sparse-encoder"}:
        if args.batch_sampler != "NO_DUPLICATES":
            findings.append(Finding("WARN", "Use batch_sampler=BatchSamplers.NO_DUPLICATES for in-batch-negative dense/sparse losses."))
        else:
            findings.append(Finding("OK", "NO_DUPLICATES sampler is set for in-batch negatives."))

    if loss in TRIPLET_BATCH_LOSSES:
        if args.batch_sampler != "GROUP_BY_LABEL":
            findings.append(Finding("WARN", "Batch triplet losses need batch_sampler=BatchSamplers.GROUP_BY_LABEL."))
        else:
            findings.append(Finding("OK", "GROUP_BY_LABEL sampler is set for batch triplet loss."))

    if args.model_type == "cross-encoder":
        if loss == "BinaryCrossEntropyLoss" and args.num_labels not in (None, 1):
            findings.append(Finding("ERROR", "BinaryCrossEntropyLoss expects CrossEncoder num_labels=1."))
        if loss == "CrossEntropyLoss" and (args.num_labels is None or args.num_labels < 2):
            findings.append(Finding("ERROR", "CrossEntropyLoss expects CrossEncoder num_labels>=2."))
        if loss in LISTWISE_OR_DISTILL_CE and loss != "BinaryCrossEntropyLoss" and args.activation != "identity":
            findings.append(Finding("WARN", "Listwise/pairwise/distillation CrossEncoder losses should use activation_fn=Identity() for raw ranking scores."))
        if args.data_shape == "pair-unlabeled":
            findings.append(Finding("WARN", "Pair positives without negatives usually need hard-negative mining before reranker training."))

    if args.model_type == "sparse-encoder":
        if loss == "SparseMultipleNegativesRankingLoss":
            findings.append(Finding("WARN", "For SPLADE training, wrap SparseMultipleNegativesRankingLoss in SpladeLoss or CachedSpladeLoss to add FLOPS regularization."))
        if loss in SPARSE_WRAPPERS and args.evaluator and not contains_any(args.evaluator, ("Sparse", "ReciprocalRankFusionEvaluator")):
            findings.append(Finding("WARN", "Sparse training should usually evaluate with sparse evaluators and active-dimension metrics."))
        if not args.monitor_active_dims:
            findings.append(Finding("WARN", "Sparse plans should monitor query_active_dims and document_active_dims."))

    if args.multi_dataset and args.multi_dataset_sampler == "unspecified":
        findings.append(Finding("WARN", "Multi-dataset training should set MultiDatasetBatchSamplers.PROPORTIONAL or ROUND_ROBIN deliberately."))

    if args.cached_loss and args.gradient_checkpointing:
        findings.append(Finding("ERROR", "Cached* losses are incompatible with gradient_checkpointing=True."))

    if args.eval_strategy != "no" and not (args.eval_dataset or args.evaluator):
        findings.append(Finding("WARN", "Step/epoch evaluation needs an eval_dataset or explicit evaluator; otherwise training can hang or skip useful eval."))

    if not args.baseline_eval:
        findings.append(Finding("WARN", "Run evaluator(model) before trainer.train() to capture a baseline."))

    if not args.smoke_test:
        findings.append(Finding("WARN", "Run a max_steps=1 smoke test on a tiny dataset slice before a long run."))

    if args.metric_for_best_model and not args.metric_for_best_model.startswith("eval_"):
        findings.append(Finding("WARN", "metric_for_best_model usually starts with 'eval_' plus evaluator.primary_metric."))

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a sentence-transformers training plan without importing the package or running training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model-type", choices=MODEL_TYPES, required=True, help="Training model family.")
    parser.add_argument("--data-shape", choices=DATA_SHAPES, required=True, help="Logical row shape after dataset cleanup.")
    parser.add_argument("--loss", required=True, help="Planned loss class name, with or without module prefix.")
    parser.add_argument("--evaluator", help="Planned evaluator class name, with or without module prefix.")
    parser.add_argument("--num-labels", type=int, help="CrossEncoder num_labels value, if applicable.")
    parser.add_argument(
        "--activation",
        choices=("default", "identity"),
        default="default",
        help="CrossEncoder activation route for one-output scoring models.",
    )
    parser.add_argument(
        "--batch-sampler",
        choices=("default", "NO_DUPLICATES", "NO_DUPLICATES_HASHED", "GROUP_BY_LABEL"),
        default="default",
        help="BatchSamplers enum value planned for training args.",
    )
    parser.add_argument(
        "--multi-dataset",
        action="store_true",
        help="Plan uses multiple train datasets or a DatasetDict/dict of datasets.",
    )
    parser.add_argument(
        "--multi-dataset-sampler",
        choices=("unspecified", "PROPORTIONAL", "ROUND_ROBIN"),
        default="unspecified",
        help="MultiDatasetBatchSamplers enum value if multi-dataset training is used.",
    )
    parser.add_argument("--cached-loss", action="store_true", help="Loss is a Cached* / GradCache-style loss.")
    parser.add_argument("--gradient-checkpointing", action="store_true", help="Training args enable gradient checkpointing.")
    parser.add_argument(
        "--eval-strategy",
        choices=("no", "steps", "epoch"),
        default="steps",
        help="Trainer evaluation strategy.",
    )
    parser.add_argument("--eval-dataset", action="store_true", help="A non-empty eval_dataset will be passed to the trainer.")
    parser.add_argument("--baseline-eval", action="store_true", help="Plan includes evaluator(model) before trainer.train().")
    parser.add_argument("--smoke-test", action="store_true", help="Plan includes max_steps=1 or equivalent tiny smoke test.")
    parser.add_argument("--metric-for-best-model", help="Planned metric_for_best_model key.")
    parser.add_argument(
        "--monitor-active-dims",
        action="store_true",
        help="Sparse plan monitors query_active_dims and document_active_dims.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    findings = check_plan(args)
    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARN"]

    for finding in findings:
        print(f"{finding.level}: {finding.message}")

    if errors:
        return 2
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
