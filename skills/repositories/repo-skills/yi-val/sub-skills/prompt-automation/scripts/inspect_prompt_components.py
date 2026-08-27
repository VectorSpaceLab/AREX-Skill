#!/usr/bin/env python3
"""Print YiVal prompt/data generator ids and default configs."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

# Import built-in generator modules for registration.
import yival.data_generators.document_data_generator  # noqa: F401
import yival.data_generators.openai_prompt_data_generator  # noqa: F401
import yival.variation_generators.chain_of_density_prompt  # noqa: F401
import yival.variation_generators.openai_prompt_based_variation_generator  # noqa: F401
import yival.variation_generators.self_exemplar  # noqa: F401
from yival.data_generators.base_data_generator import BaseDataGenerator
from yival.variation_generators.base_variation_generator import BaseVariationGenerator


def to_data(value: Any) -> Any:
    if hasattr(value, "asdict"):
        return value.asdict()
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return {k: to_data(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_data(v) for v in value]
    return value


def summarize(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "class": info.get("class").__name__ if info.get("class") else None,
            "config_cls": info.get("config_cls").__name__ if info.get("config_cls") else None,
            "default_config": to_data(info.get("default_config")),
        }
        for name, info in sorted(registry.items())
    }


def main() -> int:
    print(json.dumps({
        "data_generators": summarize(BaseDataGenerator._registry),
        "variation_generators": summarize(BaseVariationGenerator._registry),
    }, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
