#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
NEGATIVE_SCRIPT = THIS.parents[2] / "pope_negative_sampling" / "scripts"
if NEGATIVE_SCRIPT.exists():
    sys.path.insert(0, str(NEGATIVE_SCRIPT))

from pope_negative_sampling import normalize_objects, normalize_records, select_negative


def format_question(template, obj):
    article_template = template
    if obj[:1].lower() in {"a", "e", "i", "o", "u"}:
        article_template = template.replace(" a {}", " an {}")
    return article_template.format(obj)


def build_pope_questions(records, sample_num=3, strategy="random", template="Is there a {} in the image?", seed=0):
    normalized = normalize_records(records)
    retained = [record for record in normalized if len(record["objects"]) >= sample_num]
    questions = []
    question_id = 1
    rng = random.Random(seed)
    for image_index, record in enumerate(retained):
        positives = list(record["objects"][:sample_num])
        history = []
        for positive in positives:
            history.append(positive)
            questions.append({
                "question_id": question_id,
                "image": record["image"],
                "text": format_question(template, positive),
                "object": positive,
                "label": "yes",
                "strategy": strategy,
            })
            question_id += 1
            negative = select_negative(normalized, record["objects"], history, strategy=strategy, anchor=positive, seed=rng.randint(0, 10**9))
            history.append(negative)
            questions.append({
                "question_id": question_id,
                "image": record["image"],
                "text": format_question(template, negative),
                "object": negative,
                "label": "no",
                "strategy": strategy,
            })
            question_id += 1
    return questions


def write_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records")
    parser.add_argument("--output")
    parser.add_argument("--sample-num", type=int, default=3)
    parser.add_argument("--strategy", default="random")
    parser.add_argument("--template", default="Is there a {} in the image?")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        records = [
            {"image": "i1", "objects": ["cat", "sofa", "lamp"]},
            {"image": "i2", "objects": ["dog", "ball", "tree"]},
        ]
        questions = build_pope_questions(records, sample_num=2, strategy="popular")
        assert len(questions) == 8
        assert {q["label"] for q in questions} == {"yes", "no"}
        print(json.dumps({"ok": True, "questions": len(questions)}))
        return
    records = json.loads(Path(args.records).read_text(encoding="utf-8"))
    questions = build_pope_questions(records, args.sample_num, args.strategy, args.template, args.seed)
    if args.output:
        write_jsonl(questions, args.output)
    print(json.dumps({"ok": True, "question_count": len(questions)}, indent=2))


if __name__ == "__main__":
    main()
