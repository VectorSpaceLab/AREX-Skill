#!/usr/bin/env python3
"""Inspect CAMEL FunctionTool schema generation without calling a model.

This script is adapted from CAMEL's function-tool example into a safe local
schema diagnostic. It wraps two local Python helpers, validates their generated
OpenAI tool schemas, and prints compact JSON for review.
"""

import argparse
import json
import sys
from typing import Any

try:
    from pydantic import BaseModel, Field

    from camel.toolkits import FunctionTool
except Exception as exc:  # pragma: no cover - diagnostic path
    print(
        "Unable to import CAMEL FunctionTool dependencies. Install the package "
        "with `pip install camel-ai` or `pip install 'camel-ai[tools]'` in "
        f"your active environment. Original error: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(2)


class Traveler(BaseModel):
    """Nested argument model used to demonstrate Pydantic schema handling."""

    name: str = Field(description="Traveler name")
    age: int = Field(ge=0, description="Traveler age in years")


def calculate_bmi(weight: float, height: float) -> dict[str, Any]:
    """Calculate BMI and return the rounded value with a status label.

    Args:
        weight: Weight in kilograms.
        height: Height in meters.
    """
    bmi = weight / (height * height)
    if bmi < 18.5:
        status = "underweight"
    elif bmi < 24.9:
        status = "normal"
    elif bmi < 29.9:
        status = "overweight"
    else:
        status = "obese"
    return {"bmi": round(bmi, 2), "status": status}


def make_itinerary(traveler: Traveler, city: str, nights: int = 2) -> dict[str, Any]:
    """Create a tiny itinerary payload for a traveler.

    Args:
        traveler: Traveler profile with name and age.
        city: Destination city.
        nights: Number of nights to plan.
    """
    return {
        "traveler": traveler.model_dump(),
        "city": city,
        "nights": nights,
    }


def inspect(function: Any) -> dict[str, Any]:
    """Return validated schema metadata for one function."""
    tool = FunctionTool(function)
    schema = tool.get_openai_tool_schema()
    FunctionTool.validate_openai_tool_schema(schema)
    return {
        "name": tool.get_function_name(),
        "description": tool.get_function_description(),
        "schema": schema,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect CAMEL FunctionTool schemas without model calls, network "
            "access, or agent execution."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format for the schema report.",
    )
    args = parser.parse_args()

    reports = [inspect(calculate_bmi), inspect(make_itinerary)]
    if args.format == "json":
        print(json.dumps(reports, indent=2, sort_keys=True))
        return 0

    for report in reports:
        properties = report["schema"]["function"]["parameters"].get(
            "properties", {}
        )
        print(f"{report['name']}: {report['description']}")
        print("  parameters:", ", ".join(sorted(properties)) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
