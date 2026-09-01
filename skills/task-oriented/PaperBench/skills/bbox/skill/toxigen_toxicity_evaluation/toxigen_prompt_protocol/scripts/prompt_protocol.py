#!/usr/bin/env python3
"""Construct and validate ToxiGen-style demonstration prompts."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path


DEFAULT_ALIASES = {
    "black": ["black", "african american", "african-american"],
    "asian": ["asian"],
    "native_american": ["native american", "native", "indigenous"],
    "latino": ["latino", "latina", "latinx"],
    "jewish": ["jewish", "jews"],
    "muslim": ["muslim", "muslims"],
    "chinese": ["chinese"],
    "mexican": ["mexican"],
    "middle_eastern": ["middle eastern", "middle-east"],
    "lgbtq": ["lgbtq", "gay", "lesbian", "trans", "queer"],
    "women": ["women", "woman", "female"],
    "mental_disability": ["mental", "disabled", "disability"],
    "physical_disability": ["physical", "disabled", "disability"],
}

DEFAULT_FORBIDDEN = {
    "slur",
    "profanity",
}


def normalize_label(label: str) -> str:
    value = str(label).strip().lower().replace("-", "_")
    if value in {"hate", "hateful", "toxic", "toxicity"}:
        return "toxic"
    if value in {"neutral", "non_toxic", "nontoxic", "benign"}:
        return "benign"
    raise ValueError(f"unsupported label: {label!r}")


def normalize_group(group: str) -> str:
    value = str(group).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def group_aliases(group: str, aliases: dict[str, list[str]] | None = None) -> list[str]:
    group_id = normalize_group(group)
    alias_map = dict(DEFAULT_ALIASES)
    if aliases:
        alias_map.update({normalize_group(k): v for k, v in aliases.items()})
    return alias_map.get(group_id, [group_id.replace("_", " ")])


def mentions_group(text: str, group: str, aliases: dict[str, list[str]] | None = None) -> bool:
    lowered = text.lower()
    return any(alias.lower() in lowered for alias in group_aliases(group, aliases))


def contains_forbidden(text: str, forbidden_terms: set[str] | None = None) -> list[str]:
    terms = forbidden_terms if forbidden_terms is not None else DEFAULT_FORBIDDEN
    lowered = text.lower()
    hits = []
    for term in sorted(terms):
        if re.search(rf"\b{re.escape(term.lower())}\b", lowered):
            hits.append(term)
    return hits


def load_records(path: str | Path) -> list[dict]:
    p = Path(path)
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def stable_prompt_id(group: str, label: str, demonstrations: list[str]) -> str:
    payload = json.dumps([group, label, demonstrations], sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def format_prompt(demonstrations: list[str]) -> str:
    lines = [f"- {demo.strip().replace(chr(10), ' ')}" for demo in demonstrations]
    lines.append("-")
    return "\n".join(lines)


def build_prompts(
    records: list[dict],
    demonstrations_per_prompt: int = 5,
    prompts_per_bucket: int = 1,
    seed: int = 0,
    forbidden_terms: set[str] | None = None,
    aliases: dict[str, list[str]] | None = None,
) -> dict:
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        group = normalize_group(record["group"])
        label = normalize_label(record["label"])
        buckets[(group, label)].append(
            {
                "text": str(record["text"]).strip(),
                "group": group,
                "label": label,
                "source": str(record.get("source", "")),
            }
        )

    rng = random.Random(seed)
    prompts = []
    short_buckets = []
    explicit_violations = []
    identity_misses = []
    for key in sorted(buckets):
        group, label = key
        bucket = list(buckets[key])
        if len(bucket) < demonstrations_per_prompt:
            short_buckets.append({"group": group, "label": label, "available": len(bucket)})
        sample_size = min(demonstrations_per_prompt, len(bucket))
        for index in range(prompts_per_bucket):
            sampled = rng.sample(bucket, sample_size) if sample_size else []
            demos = [item["text"] for item in sampled]
            source_files = sorted({item["source"] for item in sampled if item.get("source")})
            prompt = format_prompt(demos)
            prompt_id = stable_prompt_id(group, label, demos)
            identity_ok = all(mentions_group(text, group, aliases) for text in demos) if demos else False
            forbidden = sorted({hit for text in demos for hit in contains_forbidden(text, forbidden_terms)})
            if not identity_ok:
                identity_misses.append(prompt_id)
            if forbidden:
                explicit_violations.append({"prompt_id": prompt_id, "terms": forbidden})
            prompts.append(
                {
                    "prompt_id": prompt_id,
                    "group": group,
                    "label": label,
                    "index": index,
                    "demonstrations": demos,
                    "prompt": prompt,
                    "source_files": source_files,
                    "identity_mention_ok": identity_ok,
                    "forbidden_terms": forbidden,
                }
            )

    counts = defaultdict(int)
    for item in prompts:
        counts[f"{item['group']}::{item['label']}"] += 1
    label_counts = defaultdict(int)
    for item in prompts:
        label_counts[item["label"]] += 1
    balance_ok = bool(label_counts) and len(set(label_counts.values())) == 1
    return {
        "schema_version": 1,
        "prompts": prompts,
        "summary": {
            "prompt_count": len(prompts),
            "counts_by_group_label": dict(sorted(counts.items())),
            "counts_by_label": dict(sorted(label_counts.items())),
            "balance_ok": balance_ok,
            "identity_coverage": 0.0 if not prompts else sum(1 for item in prompts if item["identity_mention_ok"]) / len(prompts),
            "short_buckets": short_buckets,
            "explicit_violations": explicit_violations,
            "identity_misses": identity_misses,
        },
    }


def run_self_test() -> None:
    records = [
        {"text": "Black artists changed American music.", "group": "black", "label": "benign", "source": "fixture"},
        {"text": "Black families deserve fair housing.", "group": "black", "label": "neutral", "source": "fixture"},
        {"text": "Black people are unfairly stereotyped in this toxic claim.", "group": "black", "label": "hate", "source": "fixture"},
        {"text": "Asian communities include many cultures.", "group": "asian", "label": "benign", "source": "fixture"},
        {"text": "Asian people are targeted by a toxic stereotype.", "group": "asian", "label": "toxic", "source": "fixture"},
    ]
    result = build_prompts(records, demonstrations_per_prompt=1, seed=3, forbidden_terms={"slur"})
    assert result["summary"]["prompt_count"] == 4
    assert result["summary"]["balance_ok"] is True
    assert result["summary"]["identity_coverage"] == 1.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--demonstrations-per-prompt", type=int, default=5)
    parser.add_argument("--prompts-per-bucket", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--forbidden-term", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        print(json.dumps({"ok": True, "test": "prompt_protocol"}))
        return 0
    if not args.input_jsonl or not args.output_json:
        parser.error("--input-jsonl and --output-json are required unless --self-test is used")
    forbidden = set(args.forbidden_term) if args.forbidden_term else None
    result = build_prompts(
        load_records(args.input_jsonl),
        demonstrations_per_prompt=args.demonstrations_per_prompt,
        prompts_per_bucket=args.prompts_per_bucket,
        seed=args.seed,
        forbidden_terms=forbidden,
    )
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
