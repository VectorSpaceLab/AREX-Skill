#!/usr/bin/env python3
"""Standalone MiroFish profile-format smoke test.

This script intentionally uses only the Python standard library. It mirrors the
current MiroFish profile file writers closely enough to validate the runtime file
shapes without importing the Flask app, contacting Zep, calling an LLM, or
starting OASIS.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TWITTER_HEADERS = ["user_id", "name", "username", "user_char", "description"]
REDDIT_REQUIRED_KEYS = [
    "user_id",
    "username",
    "name",
    "bio",
    "persona",
    "karma",
    "created_at",
    "age",
    "gender",
    "mbti",
    "country",
]
VALID_GENDERS = {"male", "female", "other"}


@dataclass
class SmokeProfile:
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    karma: int = 1000
    age: int | None = None
    gender: str | None = None
    mbti: str | None = None
    country: str | None = None
    profession: str | None = None
    interested_topics: list[str] = field(default_factory=list)
    created_at: str = "2025-12-01"


def normalize_gender(gender: str | None) -> str:
    if not gender:
        return "other"
    mapping = {
        "男": "male",
        "女": "female",
        "机构": "other",
        "其他": "other",
        "male": "male",
        "female": "female",
        "other": "other",
    }
    return mapping.get(str(gender).lower().strip(), "other")


def write_twitter_csv(profiles: list[SmokeProfile], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(TWITTER_HEADERS)
        for idx, profile in enumerate(profiles):
            user_char = profile.bio
            if profile.persona and profile.persona != profile.bio:
                user_char = f"{profile.bio} {profile.persona}"
            user_char = user_char.replace("\n", " ").replace("\r", " ")
            description = profile.bio.replace("\n", " ").replace("\r", " ")
            writer.writerow([idx, profile.name, profile.user_name, user_char, description])


def write_reddit_json(profiles: list[SmokeProfile], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for idx, profile in enumerate(profiles):
        item: dict[str, Any] = {
            "user_id": profile.user_id if profile.user_id is not None else idx,
            "username": profile.user_name,
            "name": profile.name,
            "bio": profile.bio[:150],
            "persona": profile.persona,
            "karma": profile.karma if profile.karma else 1000,
            "created_at": profile.created_at,
            "age": profile.age if profile.age else 30,
            "gender": normalize_gender(profile.gender),
            "mbti": profile.mbti if profile.mbti else "ISTJ",
            "country": profile.country if profile.country else "中国",
        }
        if profile.profession:
            item["profession"] = profile.profession
        if profile.interested_topics:
            item["interested_topics"] = profile.interested_topics
        rows.append(item)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def sample_profiles() -> list[SmokeProfile]:
    return [
        SmokeProfile(
            user_id=0,
            user_name="test_user_123",
            name="Test User",
            bio="A test user for validation",
            persona="Test User is an enthusiastic participant in social discussions.",
            karma=1500,
            age=25,
            gender="male",
            mbti="INTJ",
            country="China",
            profession="Student",
            interested_topics=["Technology", "Education"],
        ),
        SmokeProfile(
            user_id=1,
            user_name="org_official_456",
            name="Official Organization",
            bio="Official account for Organization\nwith a newline to normalize",
            persona="This institutional account communicates official positions.",
            karma=5000,
            gender="机构",
            profession="Organization",
            interested_topics=["Public Policy", "Announcements"],
        ),
    ]


def validate_twitter_csv(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if reader.fieldnames != TWITTER_HEADERS:
        errors.append(f"twitter header mismatch: {reader.fieldnames!r}")
    if len(rows) != 2:
        errors.append(f"expected 2 twitter rows, got {len(rows)}")
    for idx, row in enumerate(rows):
        if row.get("user_id") != str(idx):
            errors.append(f"twitter row {idx} user_id is not sequential: {row.get('user_id')!r}")
        for field_name in ("user_char", "description"):
            value = row.get(field_name, "")
            if "\n" in value or "\r" in value:
                errors.append(f"twitter row {idx} {field_name} contains a raw newline")
    return errors


def validate_reddit_json(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return ["reddit file is not a JSON list"]
    if len(data) != 2:
        errors.append(f"expected 2 reddit profiles, got {len(data)}")
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"reddit item {idx} is not an object")
            continue
        missing = [key for key in REDDIT_REQUIRED_KEYS if key not in item]
        if missing:
            errors.append(f"reddit item {idx} missing keys: {missing}")
        if item.get("user_id") != idx:
            errors.append(f"reddit item {idx} user_id is not sequential: {item.get('user_id')!r}")
        if item.get("gender") not in VALID_GENDERS:
            errors.append(f"reddit item {idx} invalid gender: {item.get('gender')!r}")
        if len(str(item.get("bio", ""))) > 150:
            errors.append(f"reddit item {idx} bio exceeds 150 characters")
    return errors


def run_self_test(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    twitter_path = out_dir / "twitter_profiles.csv"
    reddit_path = out_dir / "reddit_profiles.json"
    profiles = sample_profiles()

    write_twitter_csv(profiles, twitter_path)
    write_reddit_json(profiles, reddit_path)

    errors = validate_twitter_csv(twitter_path) + validate_reddit_json(reddit_path)
    summary = {
        "ok": not errors,
        "out_dir": str(out_dir),
        "twitter_file": str(twitter_path),
        "reddit_file": str(reddit_path),
        "twitter_headers": TWITTER_HEADERS,
        "reddit_required_keys": REDDIT_REQUIRED_KEYS,
        "errors": errors,
    }
    return summary


def print_examples() -> None:
    profiles = sample_profiles()
    twitter_example = {
        "headers": TWITTER_HEADERS,
        "first_row": [
            0,
            profiles[0].name,
            profiles[0].user_name,
            f"{profiles[0].bio} {profiles[0].persona}",
            profiles[0].bio,
        ],
    }
    reddit_item = {
        "user_id": profiles[0].user_id,
        "username": profiles[0].user_name,
        "name": profiles[0].name,
        "bio": profiles[0].bio[:150],
        "persona": profiles[0].persona,
        "karma": profiles[0].karma,
        "created_at": profiles[0].created_at,
        "age": profiles[0].age,
        "gender": normalize_gender(profiles[0].gender),
        "mbti": profiles[0].mbti,
        "country": profiles[0].country,
        "profession": profiles[0].profession,
        "interested_topics": profiles[0].interested_topics,
    }
    print(json.dumps({"twitter_csv": twitter_example, "reddit_json_item": reddit_item}, ensure_ascii=False, indent=2))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check current MiroFish saved profile formats with temp files. "
            "No MiroFish imports, no network calls, no OASIS runtime."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="write sample Twitter CSV and Reddit JSON files, validate them, and print a JSON summary",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="directory for generated smoke files; defaults to a temporary directory",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="preserve the temporary directory when --out-dir is not supplied",
    )
    parser.add_argument(
        "--print-examples",
        action="store_true",
        help="print compact example profile shapes and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.print_examples:
        print_examples()
        return 0

    # Default execution is a safe self-test.
    if args.out_dir:
        summary = run_self_test(args.out_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["ok"] else 1

    temp_dir = Path(tempfile.mkdtemp(prefix="mirofish-profile-smoke-"))
    try:
        summary = run_self_test(temp_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["ok"] else 1
    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
