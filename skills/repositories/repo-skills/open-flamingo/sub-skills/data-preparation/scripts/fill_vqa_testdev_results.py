#!/usr/bin/env python3
"""Fill OpenFlamingo VQAv2/VizWiz test result JSON files.

The input is a prediction subset list with question_id/answer records. The output
contains one entry for every question in the provided full test questions JSON,
using a normalized prediction when available and an empty answer otherwise.

This standalone script performs no repository-local imports. The answer
normalizer is adapted from the VQA evaluation helper used by OpenFlamingo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CONTRACTIONS = {
    "aint": "ain't",
    "arent": "aren't",
    "cant": "can't",
    "couldve": "could've",
    "couldnt": "couldn't",
    "couldn'tve": "couldn't've",
    "couldnt've": "couldn't've",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "dont": "don't",
    "hadnt": "hadn't",
    "hadnt've": "hadn't've",
    "hadn'tve": "hadn't've",
    "hasnt": "hasn't",
    "havent": "haven't",
    "hed": "he'd",
    "hed've": "he'd've",
    "he'dve": "he'd've",
    "hes": "he's",
    "howd": "how'd",
    "howll": "how'll",
    "hows": "how's",
    "Id've": "I'd've",
    "I'dve": "I'd've",
    "Im": "I'm",
    "Ive": "I've",
    "isnt": "isn't",
    "itd": "it'd",
    "itd've": "it'd've",
    "it'dve": "it'd've",
    "itll": "it'll",
    "let's": "let's",
    "maam": "ma'am",
    "mightnt": "mightn't",
    "mightnt've": "mightn't've",
    "mightn'tve": "mightn't've",
    "mightve": "might've",
    "mustnt": "mustn't",
    "mustve": "must've",
    "neednt": "needn't",
    "notve": "not've",
    "oclock": "o'clock",
    "oughtnt": "oughtn't",
    "ow's'at": "'ow's'at",
    "'ows'at": "'ow's'at",
    "'ow'sat": "'ow's'at",
    "shant": "shan't",
    "shed've": "she'd've",
    "she'dve": "she'd've",
    "she's": "she's",
    "shouldve": "should've",
    "shouldnt": "shouldn't",
    "shouldnt've": "shouldn't've",
    "shouldn'tve": "shouldn't've",
    "somebody'd": "somebodyd",
    "somebodyd've": "somebody'd've",
    "somebody'dve": "somebody'd've",
    "somebodyll": "somebody'll",
    "somebodys": "somebody's",
    "someoned": "someone'd",
    "someoned've": "someone'd've",
    "someone'dve": "someone'd've",
    "someonell": "someone'll",
    "someones": "someone's",
    "somethingd": "something'd",
    "somethingd've": "something'd've",
    "something'dve": "something'd've",
    "somethingll": "something'll",
    "thats": "that's",
    "thered": "there'd",
    "thered've": "there'd've",
    "there'dve": "there'd've",
    "therere": "there're",
    "theres": "there's",
    "theyd": "they'd",
    "theyd've": "they'd've",
    "they'dve": "they'd've",
    "theyll": "they'll",
    "theyre": "they're",
    "theyve": "they've",
    "twas": "'twas",
    "wasnt": "wasn't",
    "wed've": "we'd've",
    "we'dve": "we'd've",
    "weve": "we've",
    "werent": "weren't",
    "whatll": "what'll",
    "whatre": "what're",
    "whats": "what's",
    "whatve": "what've",
    "whens": "when's",
    "whered": "where'd",
    "wheres": "where's",
    "whereve": "where've",
    "whod": "who'd",
    "whod've": "who'd've",
    "who'dve": "who'd've",
    "wholl": "who'll",
    "whos": "who's",
    "whove": "who've",
    "whyll": "why'll",
    "whyre": "why're",
    "whys": "why's",
    "wont": "won't",
    "wouldve": "would've",
    "wouldnt": "wouldn't",
    "wouldnt've": "wouldn't've",
    "wouldn'tve": "wouldn't've",
    "yall": "y'all",
    "yall'll": "y'all'll",
    "y'allll": "y'all'll",
    "yall'd've": "y'all'd've",
    "y'alld've": "y'all'd've",
    "y'all'dve": "y'all'd've",
    "youd": "you'd",
    "youd've": "you'd've",
    "you'dve": "you'd've",
    "youll": "you'll",
    "youre": "you're",
    "youve": "you've",
}

MANUAL_MAP = {
    "none": "0",
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}

ARTICLES = {"a", "an", "the"}
PERIOD_STRIP = re.compile(r"(?!<=\d)(\.)(?!\d)")
COMMA_STRIP = re.compile(r"(\d)(\,)(\d)")
PUNCTUATION = [
    ";",
    r"/",
    "[",
    "]",
    '"',
    "{",
    "}",
    "(",
    ")",
    "=",
    "+",
    "\\",
    "_",
    "-",
    ">",
    "<",
    "@",
    "`",
    ",",
    "?",
    "!",
]


class FillError(Exception):
    """Raised for invalid input data."""


def process_punctuation(text: str) -> str:
    out_text = text
    for punct in PUNCTUATION:
        if (punct + " " in text or " " + punct in text) or (re.search(COMMA_STRIP, text) is not None):
            out_text = out_text.replace(punct, "")
        else:
            out_text = out_text.replace(punct, " ")
    return PERIOD_STRIP.sub("", out_text)


def process_digit_article(text: str) -> str:
    out_words: List[str] = []
    for word in text.lower().split():
        word = MANUAL_MAP.get(word, word)
        if word not in ARTICLES:
            out_words.append(word)
    for idx, word in enumerate(out_words):
        if word in CONTRACTIONS:
            out_words[idx] = CONTRACTIONS[word]
    return " ".join(out_words)


def normalize_answer(answer: str) -> str:
    answer = answer.replace("\n", " ").replace("\t", " ").strip()
    answer = process_punctuation(answer)
    answer = process_digit_article(answer)
    return answer


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        raise FillError(f"failed to read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FillError(f"invalid JSON in {path}: {exc}") from exc


def load_predictions(path: Path) -> Dict[str, str]:
    data = _load_json(path)
    if not isinstance(data, list):
        raise FillError(f"prediction input must be a JSON list, got {type(data).__name__}")
    predictions: Dict[str, str] = {}
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise FillError(f"prediction record {idx}: expected object, got {type(item).__name__}")
        if "question_id" not in item:
            raise FillError(f"prediction record {idx}: missing 'question_id'")
        if "answer" not in item:
            raise FillError(f"prediction record {idx}: missing 'answer'")
        if not isinstance(item["answer"], str):
            raise FillError(f"prediction record {idx}: answer must be a string, got {type(item['answer']).__name__}")
        qid = str(item["question_id"])
        if qid in predictions:
            raise FillError(f"duplicate prediction for question_id {item['question_id']!r}")
        predictions[qid] = normalize_answer(item["answer"])
    return predictions


def load_questions(path: Path) -> List[Dict[str, Any]]:
    data = _load_json(path)
    if not isinstance(data, dict) or "questions" not in data:
        raise FillError("test questions JSON must be an object with a top-level 'questions' list")
    questions = data["questions"]
    if not isinstance(questions, list):
        raise FillError("test questions JSON field 'questions' must be a list")
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            raise FillError(f"question record {idx}: expected object, got {type(q).__name__}")
        if "question_id" not in q:
            raise FillError(f"question record {idx}: missing 'question_id'")
        if "image_id" not in q:
            raise FillError(f"question record {idx}: missing 'image_id'")
    return questions


def fill_vqav2_test_json(input_path: str, output_path: str, vqa_test_questions_json_path: str) -> Dict[str, int]:
    predictions = load_predictions(Path(input_path))
    questions = load_questions(Path(vqa_test_questions_json_path))
    output: List[Dict[str, Any]] = []
    used_ids = set()
    missing = 0
    for q in questions:
        qid_key = str(q["question_id"])
        answer = predictions.get(qid_key, "")
        if answer == "":
            missing += 1
        else:
            used_ids.add(qid_key)
        output.append({"question_id": q["question_id"], "answer": answer})
    _write_output(Path(output_path), output)
    return {
        "questions": len(questions),
        "predictions": len(predictions),
        "used_predictions": len(used_ids),
        "missing_filled_empty": missing,
        "extra_predictions": len(set(predictions) - {str(q["question_id"]) for q in questions}),
    }


def fill_vizwiz_test_json(input_path: str, output_path: str, vqa_test_questions_json_path: str) -> Dict[str, int]:
    predictions = load_predictions(Path(input_path))
    questions = load_questions(Path(vqa_test_questions_json_path))
    output: List[Dict[str, Any]] = []
    used_ids = set()
    missing = 0
    for q in questions:
        qid_key = str(q["question_id"])
        answer = predictions.get(qid_key, "")
        if answer == "":
            missing += 1
        else:
            used_ids.add(qid_key)
        output.append({"image": q["image_id"], "answer": answer})
    _write_output(Path(output_path), output)
    return {
        "questions": len(questions),
        "predictions": len(predictions),
        "used_predictions": len(used_ids),
        "missing_filled_empty": missing,
        "extra_predictions": len(set(predictions) - {str(q["question_id"]) for q in questions}),
    }


def _write_output(path: Path, output: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(list(output), f, ensure_ascii=False)
    except OSError as exc:
        raise FillError(f"failed to write {path}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fill missing VQAv2/VizWiz test answers with empty strings for complete submission JSON."
    )
    parser.add_argument("--dataset", required=True, choices=["vqav2", "vizwiz"], help="Target output format.")
    parser.add_argument(
        "--input_path",
        required=True,
        help="Path to JSON list with prediction subset records: {'question_id': ..., 'answer': ...}.",
    )
    parser.add_argument(
        "--vqa_test_questions_json_path",
        required=True,
        help="Path to full test questions JSON object with top-level 'questions'.",
    )
    parser.add_argument("--output_path", required=True, help="Path where the filled JSON list will be written.")
    parser.add_argument(
        "--fail-on-extra-predictions",
        action="store_true",
        help="Exit with an error if input predictions contain IDs absent from the test questions file.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.dataset == "vqav2":
            summary = fill_vqav2_test_json(
                args.input_path,
                args.output_path,
                args.vqa_test_questions_json_path,
            )
        else:
            summary = fill_vizwiz_test_json(
                args.input_path,
                args.output_path,
                args.vqa_test_questions_json_path,
            )
        if summary["extra_predictions"]:
            message = f"warning: ignored {summary['extra_predictions']} prediction(s) whose question_id was absent from the test questions file"
            if args.fail_on_extra_predictions:
                raise FillError(message.replace("warning: ", ""))
            print(message, file=sys.stderr)
        print(json.dumps(summary, indent=2, sort_keys=True), file=sys.stderr)
        return 0
    except FillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
