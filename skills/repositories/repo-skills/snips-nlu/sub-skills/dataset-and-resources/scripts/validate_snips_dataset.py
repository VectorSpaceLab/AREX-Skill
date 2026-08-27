#!/usr/bin/env python3
"""Validate a Snips NLU JSON dataset without training or downloads."""

import argparse
import json
import sys
from pathlib import Path

KNOWN_BUILTINS = {
    "snips/amountOfMoney",
    "snips/duration",
    "snips/number",
    "snips/ordinal",
    "snips/temperature",
    "snips/datetime",
    "snips/date",
    "snips/time",
    "snips/datePeriod",
    "snips/timePeriod",
    "snips/percentage",
    "snips/musicAlbum",
    "snips/musicArtist",
    "snips/musicTrack",
    "snips/city",
    "snips/country",
    "snips/region",
}

SCHEMA_EXPLANATION = """Snips NLU JSON dataset authoring schema:
  root object: language (str), intents (object), entities (object)
  intent: {"utterances": [{"data": [chunks...]}]}
  text chunk: {"text": "literal text"}
  slot chunk: {"text": "slot text", "entity": "entity_name", "slot_name": "slot_name"}
  custom entity: {
    "data": [{"value": "canonical", "synonyms": ["alias"]}],
    "use_synonyms": true,
    "automatically_extensible": true,
    "matching_strictness": 1.0
  }
  built-in entity: {"snips/datetime": {}} (same pattern for other snips/* built-ins)
This script calls snips_nlu.dataset.validate_and_format_dataset when Snips NLU is importable.
"""


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate a Snips NLU JSON dataset without training or downloads."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to a JSON dataset with language/intents/entities root keys.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print the expected schema and validation summary.",
    )
    return parser


def load_json(path):
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise OSError("dataset file does not exist")
    if dataset_path.is_dir():
        raise OSError("dataset path is a directory")
    with dataset_path.open("r", encoding="utf8") as stream:
        return json.load(stream)


def _expect_type(issues, value, expected_type, label):
    if not isinstance(value, expected_type):
        issues.append(
            "Invalid type for {label}: expected {expected}, found {found}".format(
                label=label,
                expected=expected_type.__name__,
                found=type(value).__name__,
            )
        )
        return False
    return True


def basic_schema_issues(dataset):
    """Return (issues, warnings) for obvious authoring-schema mistakes."""
    issues = []
    warnings = []

    if not isinstance(dataset, dict):
        return ["Invalid type for dataset: expected object"], warnings

    for key in ("language", "intents", "entities"):
        if key not in dataset:
            issues.append("Missing root key: '{}'".format(key))

    if "language" in dataset:
        _expect_type(issues, dataset["language"], str, "language")

    intents = dataset.get("intents")
    if isinstance(intents, dict):
        for intent_name, intent_data in sorted(intents.items()):
            label = "intent '{}'".format(intent_name)
            if not _expect_type(issues, intent_data, dict, label):
                continue
            if "utterances" not in intent_data:
                issues.append("{} is missing key: 'utterances'".format(label))
                continue
            if not _expect_type(issues, intent_data["utterances"], list, label + " utterances"):
                continue
            for utterance_index, utterance in enumerate(intent_data["utterances"]):
                u_label = "{} utterance {}".format(label, utterance_index)
                if not _expect_type(issues, utterance, dict, u_label):
                    continue
                if "data" not in utterance:
                    issues.append("{} is missing key: 'data'".format(u_label))
                    continue
                if not _expect_type(issues, utterance["data"], list, u_label + " data"):
                    continue
                for chunk_index, chunk in enumerate(utterance["data"]):
                    c_label = "{} chunk {}".format(u_label, chunk_index)
                    if not _expect_type(issues, chunk, dict, c_label):
                        continue
                    if "text" not in chunk:
                        issues.append("{} is missing key: 'text'".format(c_label))
                    has_entity = "entity" in chunk
                    has_slot = "slot_name" in chunk
                    if has_entity != has_slot:
                        issues.append(
                            "{} must include both 'entity' and 'slot_name' for slot chunks".format(c_label)
                        )
    elif "intents" in dataset:
        _expect_type(issues, intents, dict, "intents")

    entities = dataset.get("entities")
    already_validated = dataset.get("validated") is True
    if isinstance(entities, dict):
        for entity_name, entity_data in sorted(entities.items()):
            e_label = "entity '{}'".format(entity_name)
            if not _expect_type(issues, entity_data, dict, e_label):
                continue
            if entity_name in KNOWN_BUILTINS:
                if entity_data:
                    warnings.append(
                        "{} is a built-in; authoring datasets normally use an empty object".format(e_label)
                    )
                continue
            if entity_name.startswith("snips/"):
                warnings.append(
                    "{} starts with 'snips/' but is not in the known built-in list; check spelling".format(e_label)
                )
            if already_validated:
                continue
            for key in ("data", "use_synonyms", "automatically_extensible"):
                if key not in entity_data:
                    issues.append("{} is missing key: '{}'".format(e_label, key))
            if "matching_strictness" not in entity_data:
                warnings.append(
                    "{} is missing 'matching_strictness'; Snips NLU may default it to 1.0".format(e_label)
                )
            elif not isinstance(entity_data["matching_strictness"], (int, float)):
                issues.append("{} matching_strictness must be numeric".format(e_label))
            if "use_synonyms" in entity_data and not isinstance(entity_data["use_synonyms"], bool):
                issues.append("{} use_synonyms must be boolean".format(e_label))
            if "automatically_extensible" in entity_data and not isinstance(
                entity_data["automatically_extensible"], bool
            ):
                issues.append("{} automatically_extensible must be boolean".format(e_label))
            data = entity_data.get("data")
            if "data" in entity_data and _expect_type(issues, data, list, e_label + " data"):
                for entry_index, entry in enumerate(data):
                    entry_label = "{} data entry {}".format(e_label, entry_index)
                    if not _expect_type(issues, entry, dict, entry_label):
                        continue
                    if "value" not in entry:
                        issues.append("{} is missing key: 'value'".format(entry_label))
                    elif not isinstance(entry["value"], str):
                        issues.append("{} value must be a string".format(entry_label))
                    elif not entry["value"].strip():
                        warnings.append("{} has an empty value that validation will drop".format(entry_label))
                    if "synonyms" not in entry:
                        issues.append("{} is missing key: 'synonyms'".format(entry_label))
                    elif not isinstance(entry["synonyms"], list):
                        issues.append("{} synonyms must be a list".format(entry_label))
    elif "entities" in dataset:
        _expect_type(issues, entities, dict, "entities")

    return issues, warnings


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.explain:
        print(SCHEMA_EXPLANATION.rstrip())

    try:
        dataset = load_json(args.dataset)
    except json.JSONDecodeError as exc:
        print("invalid JSON: {}".format(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print("cannot read dataset: {}".format(exc), file=sys.stderr)
        return 1

    issues, warnings = basic_schema_issues(dataset)
    for warning in warnings:
        print("warning: {}".format(warning), file=sys.stderr)
    if issues:
        for issue in issues:
            print("invalid: {}".format(issue), file=sys.stderr)
        return 1

    try:
        from snips_nlu.dataset import validate_and_format_dataset
    except Exception as exc:  # pragma: no cover - environment dependent
        print(
            "Snips NLU API validator is unavailable: {}: {}".format(
                type(exc).__name__, exc
            ),
            file=sys.stderr,
        )
        print("structural checks passed, but full package validation did not run", file=sys.stderr)
        return 3

    try:
        validated = validate_and_format_dataset(dataset)
    except Exception as exc:
        print("invalid: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1

    language = dataset.get("language", "?")
    intent_count = len(dataset.get("intents", {}))
    entity_count = len(dataset.get("entities", {}))
    status = "validated" if isinstance(validated, dict) and validated.get("validated") else "accepted"
    print(
        "OK: {} Snips NLU dataset (language={}, intents={}, entities={})".format(
            status, language, intent_count, entity_count
        )
    )
    if args.explain:
        print(
            "Validation uses snips_nlu.dataset.validate_and_format_dataset; "
            "formatted output may differ from authoring JSON."
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
