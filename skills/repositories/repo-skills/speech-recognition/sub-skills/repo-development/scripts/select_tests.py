#!/usr/bin/env python3
"""Suggest focused SpeechRecognition maintainer checks without executing them.

Example:
    # from this sub-skill directory
    python scripts/select_tests.py speech_recognition/audio.py tests/test_audio.py --workflow lint

The output is advisory. Run commands from a SpeechRecognition checkout after
installing the extras or host tools required by the changed surface.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    command: str
    reason: str
    prerequisites: tuple[str, ...] = ()
    gated: bool = False
    workflow: str | None = None


@dataclass
class Collector:
    suggestions: list[Suggestion] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, command: str, reason: str, *prerequisites: str, gated: bool = False, workflow: str | None = None) -> None:
        item = Suggestion(command, reason, tuple(p for p in prerequisites if p), gated, workflow)
        if item not in self.suggestions:
            self.suggestions.append(item)

    def note(self, text: str) -> None:
        if text not in self.notes:
            self.notes.append(text)


EXTRA_COMMANDS: dict[str, list[Suggestion]] = {
    "audio": [
        Suggestion(
            'python -c "from speech_recognition import Microphone; Microphone.get_pyaudio()"',
            "Verify the PyAudio-backed Microphone extra contract.",
            ("Install .[dev,audio] and platform PortAudio development libraries when needed.",),
            workflow="extra-contracts/audio",
        )
    ],
    "pocketsphinx": [
        Suggestion(
            "pytest -s -v tests/test_recognition.py tests/test_special_features.py",
            "Verify the PocketSphinx extra contract and special keyword behavior.",
            ("Install .[dev,pocketsphinx]; some assertions skip on Windows.",),
            workflow="extra-contracts/pocketsphinx",
        )
    ],
    "google-cloud": [
        Suggestion(
            "pytest -s -v tests/recognizers/test_google_cloud.py",
            "Verify Google Cloud recognizer client construction and parameter plumbing.",
            ("Install .[dev,google-cloud]; tests use mocks for credential path behavior.",),
            workflow="extra-contracts/google-cloud",
        )
    ],
    "whisper-local": [
        Suggestion(
            "pytest -s -v tests/recognizers/whisper_local/test_whisper.py",
            "Verify local OpenAI Whisper adapter behavior.",
            ("Install .[dev,whisper-local]; tests skip on Python 3.14 or later.",),
            workflow="extra-contracts/whisper-local",
        )
    ],
    "faster-whisper": [
        Suggestion(
            "pytest -s -v tests/recognizers/whisper_local/test_faster_whisper.py",
            "Verify faster-whisper adapter behavior.",
            ("Install .[dev,faster-whisper]; tests skip on Python 3.14 or later.",),
            workflow="extra-contracts/faster-whisper",
        )
    ],
    "openai": [
        Suggestion(
            "pytest -s -v tests/recognizers/whisper_api/test_openai.py tests/recognizers/whisper_api/test_openai_compatible.py",
            "Verify hosted and OpenAI-compatible transcription API request behavior.",
            ("Install .[dev,openai]; tests use mocked HTTP/fake endpoint behavior.",),
            workflow="extra-contracts/openai",
        )
    ],
    "groq": [
        Suggestion(
            "pytest -s -v tests/recognizers/whisper_api/test_groq.py",
            "Verify Groq Whisper API request behavior.",
            ("Install .[dev,groq]; tests use mocked HTTP behavior.",),
            workflow="extra-contracts/groq",
        )
    ],
    "cohere-api": [
        Suggestion(
            "pytest -s -v tests/recognizers/test_cohere_api.py",
            "Verify Cohere Transcribe API request behavior.",
            ("Install .[dev,cohere-api]; tests mock the Cohere client.",),
            workflow="extra-contracts/cohere-api",
        )
    ],
    "assemblyai": [
        Suggestion(
            'python -c "from speech_recognition import Recognizer; assert hasattr(Recognizer(), \'recognize_assemblyai\')"',
            "Verify the AssemblyAI extra exposes the public Recognizer method.",
            ("Install .[dev,assemblyai].",),
            workflow="extra-contracts/assemblyai",
        )
    ],
    "vosk": [
        Suggestion(
            "python -m speech_recognition.cli download vosk",
            "Prepare the default Vosk model used by the Vosk recognizer tests.",
            ("Install .[dev,vosk]; requires network/model download approval.",),
            workflow="extra-contracts/vosk",
        ),
        Suggestion(
            "pytest -s -v tests/recognizers/test_vosk.py",
            "Verify Vosk recognizer behavior after model setup.",
            ("Install .[dev,vosk] and prepare the Vosk model.",),
            workflow="extra-contracts/vosk",
        ),
    ],
    "audio-split": [
        Suggestion(
            "pytest -s -v tests/test_audio.py",
            "Verify AudioData split behavior, including silence-aware paths.",
            ("Install .[dev,audio-split] for silence-aware split coverage.",),
            workflow="extra-contracts/audio-split",
        )
    ],
}

WORKFLOW_ALIASES = {
    "unit": "unittests",
    "units": "unittests",
    "unittest": "unittests",
    "unittests.yml": "unittests",
    "base": "base",
    "all-extras": "all-extras",
    "extra-contracts": "extra-contracts",
    "extras": "extra-contracts",
    "lint.yml": "lint",
    "rstcheck.yml": "rstcheck",
    "typecheck.yml": "typecheck",
    "publish.yml": "publish",
    "release": "publish",
    "distribution": "distribute",
}


def normalize_path(raw: str) -> str:
    return str(PurePosixPath(raw.replace("\\", "/")))


def add_extra(collector: Collector, extra: str) -> None:
    for suggestion in EXTRA_COMMANDS[extra]:
        collector.add(
            suggestion.command,
            suggestion.reason,
            *suggestion.prerequisites,
            gated=suggestion.gated,
            workflow=suggestion.workflow,
        )


def classify_path(path: str, collector: Collector) -> None:
    p = normalize_path(path)
    lower = p.lower()

    if p.startswith("tests/") and lower.endswith(".py"):
        collector.add(f"pytest -s -v {p}", f"Run the changed test file {p}.")
        if p.startswith("tests/recognizers/whisper_api/test_openai"):
            add_extra(collector, "openai")
        elif p.startswith("tests/recognizers/whisper_api/test_groq"):
            add_extra(collector, "groq")
        elif p.startswith("tests/recognizers/whisper_local/test_whisper"):
            add_extra(collector, "whisper-local")
        elif p.startswith("tests/recognizers/whisper_local/test_faster_whisper"):
            add_extra(collector, "faster-whisper")
        elif p.startswith("tests/recognizers/test_google_cloud"):
            add_extra(collector, "google-cloud")
        elif p.startswith("tests/recognizers/test_cohere_api"):
            add_extra(collector, "cohere-api")
        elif p.startswith("tests/recognizers/test_vosk"):
            add_extra(collector, "vosk")
        elif p in {"tests/test_recognition.py", "tests/test_special_features.py"}:
            collector.add("pytest -s -v tests/test_recognition.py tests/test_special_features.py", "Run core recognition and special feature tests touched by the changed test file.", "Install .[dev,pocketsphinx] for full PocketSphinx coverage when required.")
        elif p == "tests/test_audio.py":
            add_extra(collector, "audio-split")
        return

    if p == "speech_recognition/__init__.py":
        collector.add("pytest -s -v tests/test_recognition.py tests/test_special_features.py", "Core Recognizer/AudioSource/Microphone/AudioFile or public method attachment changed.", "Install .[dev,pocketsphinx] for full PocketSphinx coverage when required.")
        collector.add("make typecheck", "Core public surface changes can affect recognizer and test typing.", "Install dev dependencies and required extras for the edited surface.")
        collector.add("python -m unittest discover --verbose", "Contributor-documented broad sanity check after core changes.")
        return

    if p == "speech_recognition/audio.py":
        collector.add("pytest -s -v tests/test_audio.py", "AudioData, file conversion, FLAC, or split logic changed.", "Install .[dev,audio-split] for silence-aware split paths when relevant.")
        collector.add("make typecheck", "Audio API changes can affect tests and recognizer helpers.", "Install dev dependencies.")
        return

    if p == "speech_recognition/cli.py":
        collector.add("python -m speech_recognition.cli --help", "Check CLI parser/help after sprc command edits.")
        add_extra(collector, "vosk")
        return

    if p == "speech_recognition/__main__.py":
        collector.add("python -m py_compile speech_recognition/__main__.py", "Demo script changed; use a syntax check before any interactive microphone run.")
        collector.add("python -m unittest discover --verbose", "Demo imports core microphone and recognizer objects.")
        collector.note("The demo uses microphone input and an online recognizer; do not require an interactive run for unrelated edits.")
        return

    if p.startswith("speech_recognition/recognizers/whisper_api/openai"):
        add_extra(collector, "openai")
        collector.add("make typecheck", "Whisper API recognizer typing may be affected.", "Install dev dependencies and openai extra.")
        return
    if p.startswith("speech_recognition/recognizers/whisper_api/groq"):
        add_extra(collector, "groq")
        collector.add("make typecheck", "Groq recognizer typing may be affected.", "Install dev dependencies and groq extra.")
        return
    if p.startswith("speech_recognition/recognizers/whisper_api/"):
        add_extra(collector, "openai")
        add_extra(collector, "groq")
        collector.add("make typecheck", "Shared Whisper API recognizer code changed.", "Install dev dependencies and affected API extras.")
        return
    if p.startswith("speech_recognition/recognizers/whisper_local/faster_whisper"):
        add_extra(collector, "faster-whisper")
        collector.add("make typecheck", "Faster Whisper adapter typing may be affected.", "Install dev dependencies and faster-whisper extra.")
        return
    if p.startswith("speech_recognition/recognizers/whisper_local/whisper"):
        add_extra(collector, "whisper-local")
        collector.add("make typecheck", "Local Whisper adapter typing may be affected.", "Install dev dependencies and whisper-local extra.")
        return
    if p.startswith("speech_recognition/recognizers/whisper_local/"):
        add_extra(collector, "whisper-local")
        add_extra(collector, "faster-whisper")
        collector.add("make typecheck", "Shared local Whisper code changed.", "Install dev dependencies and affected local Whisper extras.")
        return
    if p == "speech_recognition/recognizers/google.py":
        collector.add("pytest -s -v tests/recognizers/test_google.py", "Google legacy recognizer request builder/parser changed.")
        collector.add("make typecheck", "Recognizer module typing may be affected.", "Install dev dependencies.")
        return
    if p == "speech_recognition/recognizers/google_cloud.py":
        add_extra(collector, "google-cloud")
        collector.add("make typecheck", "Google Cloud recognizer typing may be affected.", "Install dev dependencies and google-cloud extra.")
        return
    if p == "speech_recognition/recognizers/cohere_api.py":
        add_extra(collector, "cohere-api")
        collector.add("make typecheck", "Cohere recognizer typing may be affected.", "Install dev dependencies and cohere-api extra.")
        return
    if p == "speech_recognition/recognizers/vosk.py":
        add_extra(collector, "vosk")
        collector.add("make typecheck", "Vosk recognizer typing may be affected.", "Install dev dependencies and vosk extra.")
        return
    if p == "speech_recognition/recognizers/pocketsphinx.py":
        add_extra(collector, "pocketsphinx")
        collector.add("make typecheck", "PocketSphinx recognizer typing may be affected.", "Install dev dependencies and pocketsphinx extra.")
        return
    if p.startswith("speech_recognition/recognizers/"):
        collector.add("pytest -s -v tests/recognizers/", "Recognizer module changed; run engine-specific tests and discover missing ownership.", "Install extras for the affected recognizer.")
        collector.add("make typecheck", "Recognizer modules are included in mypy coverage.", "Install dev dependencies and affected extras.")
        return

    if p.startswith("examples/") and lower.endswith(".py"):
        collector.add(f"python -m py_compile {p}", f"Check syntax for changed example {p}.")
        collector.add("pytest -s -v tests/", "Examples should stay aligned with public APIs covered by tests.")
        return

    if p in {"README.rst", "CONTRIBUTING.rst"} or p.startswith("reference/"):
        collector.add("make rstcheck", "RST documentation changed.", "Install pipx because the Makefile invokes rstcheck through pipx.")
        return

    if p in {"pyproject.toml", "setup.py", "MANIFEST.in"} or p.startswith("SpeechRecognition.egg-info/"):
        collector.add("make distribute", "Packaging metadata, extras, entry points, or package data changed.", "Install pipx because the Makefile invokes build and twine through pipx.")
        collector.add("python -m unittest discover --verbose", "Package metadata changes should not break base imports/tests.")
        return

    if p in {"LICENSE.txt", "LICENSE-FLAC.txt"} or p.startswith("third-party/") or p.startswith("speech_recognition/flac"):
        collector.add("pytest -s -v tests/test_audio.py", "FLAC provenance, binary, or audio conversion artifact changed.")
        collector.add("make distribute", "License and package-data changes should be checked in built distributions.", "Install pipx because the Makefile invokes build and twine through pipx.")
        collector.note("FLAC binary rebuilds require explicit provenance authorization; do not run Docker rebuild steps as default tests.")
        return

    if p.startswith(".github/workflows/"):
        name = PurePosixPath(p).name
        apply_workflow(name, collector)
        return

    if p == "Makefile" or p == "make-release.sh":
        collector.add("make lint", "Makefile or release helper changes can affect lint target behavior.", "Install pipx for Makefile tool targets.")
        collector.add("make rstcheck", "Makefile changes can affect docs validation target behavior.", "Install pipx for Makefile tool targets.")
        collector.add("make distribute", "Release helper or distribution target changed; safe build/check coverage is needed.", "Install pipx for build and twine checks.")
        collector.note("Upload, tag signing, and make-release.sh execution are gated release actions, not default tests.")
        return


def apply_workflow(name: str, collector: Collector) -> None:
    key = WORKFLOW_ALIASES.get(name, WORKFLOW_ALIASES.get(name.lower(), name.lower()))
    if key in EXTRA_COMMANDS:
        add_extra(collector, key)
        return
    if key == "lint":
        collector.add("make lint", "Reproduce the static-analysis workflow locally.", "Install pipx for Makefile tool targets.", workflow="lint")
    elif key == "rstcheck":
        collector.add("make rstcheck", "Reproduce the RST workflow locally.", "Install pipx for Makefile tool targets.", workflow="rstcheck")
    elif key == "typecheck":
        collector.add("make typecheck", "Reproduce the typecheck workflow locally.", "Install dev dependencies plus affected optional extras and host audio libraries.", workflow="typecheck")
    elif key == "base":
        collector.add("pytest -s -v tests/", "Reproduce the unit-tests base job.", "Install .[dev].", workflow="unittests/base")
    elif key == "all-extras":
        collector.add("pytest --doctest-modules -s -v speech_recognition/recognizers/ tests/", "Reproduce the all-extras unit test command after installing the matrix extras.", "Install selected extras, host audio libraries, FFmpeg for local Whisper, and Vosk model when required.", workflow="unittests/all-extras")
        collector.note("For Python 3.14, local Whisper and faster-whisper extras are intentionally omitted in CI.")
    elif key == "unittests":
        collector.add("pytest -s -v tests/", "Reproduce the base unit-tests job.", "Install .[dev].", workflow="unittests/base")
        collector.add("pytest --doctest-modules -s -v speech_recognition/recognizers/ tests/", "Reproduce the all-extras test command when optional dependency coverage is needed.", "Install selected extras and host prerequisites first.", workflow="unittests/all-extras")
    elif key == "extra-contracts":
        for extra in EXTRA_COMMANDS:
            add_extra(collector, extra)
    elif key in {"publish", "distribute"}:
        collector.add("make distribute", "Safe release-adjacent distribution build and Twine check.", "Install pipx for build and twine checks.", workflow="publish", gated=False)
        collector.add("make publish", "Uploads distributions; run only after explicit release authorization.", "Requires maintainer-approved package index authentication.", workflow="publish", gated=True)
        collector.add("./make-release.sh VERSION_GOES_HERE", "Builds, signs, and uploads a release wheel; run only after explicit release authorization.", "Requires confirmed version, signing setup, and upload authentication.", workflow="release", gated=True)
    else:
        collector.note(f"Unknown workflow '{name}'; no workflow-specific command was added.")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed repository-relative paths.")
    parser.add_argument("--workflow", "-w", action="append", default=[], help="CI workflow, job, or extra name to include. Can be repeated.")
    parser.add_argument("--stdin", action="store_true", help="Read additional changed paths from standard input, one per line.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown text.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    collector = Collector()
    paths = list(args.paths)
    if args.stdin:
        paths.extend(line.strip() for line in sys.stdin if line.strip())

    for path in paths:
        classify_path(path, collector)
    for workflow in args.workflow:
        apply_workflow(workflow, collector)

    if not collector.suggestions:
        collector.add("pytest -s -v tests/", "Default base test suggestion when no recognized path or workflow is provided.", "Install .[dev].")
        collector.add("make lint", "Default static-analysis suggestion for unclassified edits.", "Install pipx for Makefile tool targets.")
        collector.note("No changed path matched a specialized rule; inspect the edited surface manually.")

    safe = [s for s in collector.suggestions if not s.gated]
    gated = [s for s in collector.suggestions if s.gated]

    if args.json:
        print(json.dumps({
            "safe_suggestions": [s.__dict__ for s in safe],
            "gated_release_actions": [s.__dict__ for s in gated],
            "notes": collector.notes,
        }, indent=2, sort_keys=True))
        return 0

    print("# Suggested SpeechRecognition Checks")
    print("\nSafe suggestions:")
    for idx, s in enumerate(safe, 1):
        print(f"{idx}. `{s.command}`")
        print(f"   - Reason: {s.reason}")
        if s.workflow:
            print(f"   - Workflow: {s.workflow}")
        for prereq in s.prerequisites:
            print(f"   - Prerequisite: {prereq}")
    if gated:
        print("\nGated release/publish actions, not default tests:")
        for idx, s in enumerate(gated, 1):
            print(f"{idx}. `{s.command}`")
            print(f"   - Reason: {s.reason}")
            for prereq in s.prerequisites:
                print(f"   - Gate: {prereq}")
    if collector.notes:
        print("\nNotes:")
        for note in collector.notes:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
