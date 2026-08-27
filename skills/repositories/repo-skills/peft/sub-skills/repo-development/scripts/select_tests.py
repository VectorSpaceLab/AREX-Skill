#!/usr/bin/env python3
"""Suggest focused PEFT pytest selectors for changed paths or method names."""

import argparse
from pathlib import PurePosixPath


AI_WARNING = (
    "WARNING: PEFT AI-assisted PRs require a human who understands every changed line. "
    "Breaching PEFT's agent contribution guidelines can result in automatic banning. "
    "PRs must disclose AI assistance, link maintainer coordination/approval, and list tests run."
)

LORA_EXCLUSIONS = [
    "adalora",
    "randlora",
    "loha",
    "lokr",
    "lorafa",
    "loraplus",
    "monteclora",
    "bdlora",
    "velora",
    "tinylora",
    "delora",
]

METHOD_TEST_FILES = {
    "adamss": ["tests/test_adamss_asa.py"],
    "boft": ["tests/test_boft.py"],
    "cartridge": ["tests/test_cartridge.py"],
    "cpt": ["tests/test_cpt.py"],
    "frod": ["tests/test_frod.py"],
    "ia3": ["tests/test_custom_models.py"],
    "lora": [
        "tests/test_custom_models.py",
        "tests/test_lora_variants.py",
        "tests/test_lora_conversion.py",
        "tests/test_target_parameters.py",
    ],
    "osf": ["tests/test_osf.py"],
    "poly": ["tests/test_poly.py"],
    "pvera": ["tests/test_pvera.py"],
    "randlora": ["tests/test_randlora.py"],
    "shira": ["tests/test_shira.py"],
    "trainable_tokens": ["tests/test_trainable_tokens.py"],
    "vblora": ["tests/test_vblora.py"],
    "velora": ["tests/test_velora.py"],
    "vera": ["tests/test_vera.py"],
    "xlora": ["tests/test_xlora.py"],
}

CROSS_CUTTING = {
    "config": "pytest tests/test_config.py -v",
    "mapping": "pytest tests/test_mapping.py tests/test_auto.py -v",
    "save_load": "pytest tests/ -k 'save or load or state_dict or checkpoint' -v",
    "custom_models": "pytest tests/test_custom_models.py -v",
    "quality": "make quality",
    "style": "make style",
}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def method_expression(method: str) -> str:
    method = method.lower().replace("-", "_")
    if method == "lora":
        exclusions = " and ".join(f"not {name}" for name in LORA_EXCLUSIONS)
        return f"lora and {exclusions}"
    return method


def method_from_path(path: str) -> str | None:
    parts = PurePosixPath(normalize_path(path)).parts
    if len(parts) >= 4 and parts[0] == "src" and parts[1] == "peft" and parts[2] == "tuners":
        return parts[3]
    if len(parts) >= 2 and parts[0] == "tests":
        stem = PurePosixPath(parts[-1]).stem
        if stem in {"test_custom_models", "test_common_gpu", "test_gpu_examples", "test_config", "test_mapping", "test_auto"}:
            return None
        if stem.startswith("test_"):
            candidate = stem.removeprefix("test_")
            return candidate.replace("_variants", "").replace("_conversion", "")
    if len(parts) >= 3 and parts[0] == "docs" and parts[-2] == "package_reference":
        return PurePosixPath(parts[-1]).stem
    return None


def command_for_method(method: str, custom_only: bool = False) -> list[str]:
    normalized = method.lower().replace("-", "_")
    expression = method_expression(normalized)
    files = METHOD_TEST_FILES.get(normalized, ["tests/test_custom_models.py"])
    commands = []
    if custom_only:
        commands.append(f"pytest tests/test_custom_models.py -k \"{expression}\" -v")
    else:
        joined_files = " ".join(files)
        commands.append(f"pytest {joined_files} -k \"{expression}\" -v")
        if "tests/test_custom_models.py" not in files:
            commands.append(f"pytest tests/test_custom_models.py -k \"{expression}\" -v")
    return commands


def suggest_for_path(path: str) -> list[str]:
    normalized = normalize_path(path)
    commands: list[str] = []

    if normalized.startswith("src/peft/tuners/"):
        method = method_from_path(normalized)
        if method and method != "mixed":
            commands.extend(command_for_method(method))
        commands.append(CROSS_CUTTING["mapping"])

    if normalized in {
        "src/peft/utils/peft_types.py",
        "src/peft/tuners/__init__.py",
        "src/peft/__init__.py",
    }:
        commands.append(CROSS_CUTTING["mapping"])
        commands.append(CROSS_CUTTING["custom_models"])

    if normalized.startswith("src/peft/mapping") or normalized == "src/peft/auto.py":
        commands.append(CROSS_CUTTING["mapping"])
        commands.append("pytest tests/test_custom_models.py -k 'lora or ia3' -v")

    if normalized == "src/peft/utils/save_and_load.py" or "save" in normalized or "load" in normalized:
        commands.append(CROSS_CUTTING["save_load"])
        commands.append("pytest -s --regression tests/regression/")

    if normalized.startswith("tests/test_"):
        commands.append(f"pytest {normalized} -v")

    if normalized.startswith("docs/"):
        commands.append(CROSS_CUTTING["quality"])

    if normalized.startswith("examples/"):
        commands.append("pytest tests/test_gpu_examples.py -v  # if the example requires GPU behavior")
        commands.append(CROSS_CUTTING["quality"])

    return commands


def unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changed-path", action="append", default=[], help="Changed repository path; repeatable.")
    parser.add_argument("--method", action="append", default=[], help="PEFT method name such as lora, ia3, boft; repeatable.")
    parser.add_argument("--include-style", action="store_true", help="Also include make quality/style reminders.")
    args = parser.parse_args()

    commands: list[str] = []
    methods = [method.lower().replace("-", "_") for method in args.method]

    for path in args.changed_path:
        commands.extend(suggest_for_path(path))
        inferred = method_from_path(path)
        if inferred and inferred not in methods:
            methods.append(inferred)

    for method in methods:
        commands.extend(command_for_method(method))

    if args.include_style:
        commands.extend([CROSS_CUTTING["quality"], CROSS_CUTTING["style"]])

    commands = unique(commands)

    print(AI_WARNING)
    print()
    print("Suggested focused checks:")
    if commands:
        for command in commands:
            print(f"- {command}")
    else:
        print("- pytest tests/ -v")
        print("- make quality")

    print()
    print("Before a PEFT PR: verify maintainer coordination, avoid duplicate PRs, and ensure selected tests do not deselect everything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
