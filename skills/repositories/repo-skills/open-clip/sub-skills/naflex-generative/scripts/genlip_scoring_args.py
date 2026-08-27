#!/usr/bin/env python3
"""Plan GenLIP generative scoring arguments without loading datasets or checkpoints.

This safe helper is adapted from the argument/reporting shape of open_clip's
GenLIP zero-shot research probe. It does not import open_clip, read ImageNet,
load checkpoints, or construct models. It estimates candidate-caption scoring
cost and warns about settings that are likely expensive or semantically wrong.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass


TEMPLATE_COUNTS = {
    "single": 1,
    "simple": 7,
    "openai": 80,
}


@dataclass(frozen=True)
class ScoringPlan:
    model: str
    num_classes: int
    templates: str
    templates_per_class: int
    candidate_captions: int
    score_batch: int
    forwards_per_image: int
    num_images: int
    total_conditioned_forwards: int
    pmi: bool
    unconditional_forwards: int
    total_forwards_with_overhead: int
    seq_len: int
    patch_size: int
    image_batch: int
    precision: str
    device: str
    checkpoint_required_for_meaningful_accuracy: bool


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def resolve_template_count(args: argparse.Namespace) -> int:
    if args.template_count is not None:
        return args.template_count
    return TEMPLATE_COUNTS[args.templates]


def build_plan(args: argparse.Namespace) -> ScoringPlan:
    templates_per_class = resolve_template_count(args)
    candidate_captions = args.num_classes * templates_per_class
    forwards_per_image = math.ceil(candidate_captions / args.score_batch)
    conditioned = args.num_images * forwards_per_image
    unconditional = forwards_per_image if args.pmi else 0
    return ScoringPlan(
        model=args.model,
        num_classes=args.num_classes,
        templates=args.templates if args.template_count is None else "custom",
        templates_per_class=templates_per_class,
        candidate_captions=candidate_captions,
        score_batch=args.score_batch,
        forwards_per_image=forwards_per_image,
        num_images=args.num_images,
        total_conditioned_forwards=conditioned,
        pmi=args.pmi,
        unconditional_forwards=unconditional,
        total_forwards_with_overhead=conditioned + unconditional,
        seq_len=args.seq_len,
        patch_size=args.patch_size,
        image_batch=args.image_batch,
        precision=args.precision,
        device=args.device,
        checkpoint_required_for_meaningful_accuracy=not bool(args.checkpoint),
    )


def warnings_for(plan: ScoringPlan, args: argparse.Namespace) -> list[str]:
    warnings: list[str] = []
    lowered = plan.model.lower()
    if "genlip" not in lowered:
        warnings.append("Model name does not contain 'genlip'; generative caption scoring is intended for GenLIP.")
    if args.want_cosine:
        warnings.append("Do not use CLIP cosine zero-shot for GenLIP; score log P(caption | image) or train a probe.")
    if plan.checkpoint_required_for_meaningful_accuracy:
        warnings.append("No checkpoint path supplied; a real scoring run would use random weights and chance accuracy.")
    if plan.templates_per_class >= 80 and plan.num_images > 1000:
        warnings.append("OpenAI-sized template sets over many images are expensive without a KV cache.")
    if plan.total_forwards_with_overhead > args.warn_forwards:
        warnings.append(
            f"Estimated {plan.total_forwards_with_overhead:,} forwards exceeds warning threshold "
            f"{args.warn_forwards:,}; reduce --num-images, --templates, or increase --score-batch if memory allows."
        )
    if plan.score_batch > plan.candidate_captions:
        warnings.append("score_batch exceeds candidate captions; this is safe but does not reduce forwards below one per image.")
    if plan.seq_len <= 0 or plan.patch_size <= 0:
        warnings.append("seq_len and patch_size must be positive for a real NaFlex eval transform.")
    if plan.precision.startswith("amp") and plan.device == "cpu":
        warnings.append("AMP precision settings are usually CUDA-oriented; use fp32 for CPU smoke checks.")
    return warnings


def print_text(plan: ScoringPlan, warnings: list[str]) -> None:
    print("GenLIP scoring plan (no data/model loaded):")
    print(f"  model: {plan.model}")
    print(f"  classes: {plan.num_classes:,}")
    print(f"  templates: {plan.templates} ({plan.templates_per_class}/class)")
    print(f"  candidate captions: {plan.candidate_captions:,}")
    print(f"  score batch: {plan.score_batch:,}")
    print(f"  forwards/image: {plan.forwards_per_image:,}")
    print(f"  images: {plan.num_images:,}")
    print(f"  conditioned forwards: {plan.total_conditioned_forwards:,}")
    if plan.pmi:
        print(f"  PMI unconditional forwards: {plan.unconditional_forwards:,}")
    print(f"  total forwards estimate: {plan.total_forwards_with_overhead:,}")
    print(f"  NaFlex eval: seq_len={plan.seq_len} patch_size={plan.patch_size}")
    print(f"  runtime knobs: image_batch={plan.image_batch} precision={plan.precision} device={plan.device}")
    print("\nSemantics:")
    print("  GenLIP classification probe scores length-normalized log P(template(class) | image).")
    print("  Caption token j is read from logits at image_seq_len - 1 + j in the teacher-forced sequence.")
    print("  This is not contrastive image/text cosine zero-shot.")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="naflexgenlip_b16", help="GenLIP model/config name for planning.")
    parser.add_argument("--checkpoint", default=None, help="Optional checkpoint path; only used to warn if absent.")
    parser.add_argument("--num-classes", type=positive_int, default=1000, help="Number of candidate classes.")
    parser.add_argument("--templates", choices=tuple(TEMPLATE_COUNTS), default="simple", help="Template set name.")
    parser.add_argument("--template-count", type=positive_int, default=None, help="Override templates per class for custom planning.")
    parser.add_argument("--num-images", type=positive_int, default=2000, help="Number of images to score.")
    parser.add_argument("--score-batch", type=positive_int, default=1024, help="Candidate captions per model forward.")
    parser.add_argument("--image-batch", type=positive_int, default=16, help="Dataloader image batch in the real script.")
    parser.add_argument("--seq-len", type=positive_int, default=256, help="NaFlex image patch-token eval bucket.")
    parser.add_argument("--patch-size", type=positive_int, default=16, help="NaFlex image patch size.")
    parser.add_argument("--pmi", action="store_true", help="Account for one unconditional null-image baseline pass.")
    parser.add_argument("--device", default="cuda", choices=("cuda", "cpu"), help="Planned device for a real run.")
    parser.add_argument("--precision", choices=("fp32", "amp_bf16", "amp"), default="amp_bf16")
    parser.add_argument("--want-cosine", action="store_true", help="Emit a warning for CLIP cosine requests.")
    parser.add_argument("--warn-forwards", type=positive_int, default=100_000, help="Warn above this estimated forward count.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    plan = build_plan(args)
    warnings = warnings_for(plan, args)
    if args.json:
        print(json.dumps({"ok": True, "plan": asdict(plan), "warnings": warnings}, indent=2, sort_keys=True))
    else:
        print_text(plan, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
