#!/usr/bin/env python3
"""Generate a safe Argilla SDK dataset template without contacting a server.

The generated template is also dry-run by default. It only creates/logs a live
Argilla dataset when the user runs the generated file with --create and supplies
credentials.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_TEMPLATE = r'''#!/usr/bin/env python3
"""Argilla SDK dataset/settings/records template.

Safe default: running this file without --create prints the planned schema,
example records, and mapping. It does not contact an Argilla server unless
--create is supplied with credentials.
"""

from __future__ import annotations

import argparse
import os
from pprint import pprint


DEFAULT_DATASET_NAME = __DATASET_NAME__
DEFAULT_WORKSPACE = __WORKSPACE__
DEFAULT_FIELD_NAME = __FIELD_NAME__
DEFAULT_QUESTION_NAME = __QUESTION_NAME__
DEFAULT_VECTOR_NAME = __VECTOR_NAME__
DEFAULT_VECTOR_DIMENSIONS = __VECTOR_DIMENSIONS__


def build_source_rows():
    """Return example source rows before Argilla mapping."""
    return [
        {
            "row_id": "example-1",
            "text": "Argilla makes dataset feedback workflows explicit.",
            "predicted_label": "positive",
            "prediction_score": 0.92,
            "prediction_agent": "baseline-template",
            "split": "train",
            "embedding": [0.10, 0.20, 0.30][:DEFAULT_VECTOR_DIMENSIONS],
        },
        {
            "row_id": "example-2",
            "text": "This sample needs human review.",
            "predicted_label": "negative",
            "prediction_score": 0.67,
            "prediction_agent": "baseline-template",
            "split": "validation",
            "embedding": [0.30, 0.10, 0.20][:DEFAULT_VECTOR_DIMENSIONS],
        },
    ]


def build_mapping():
    """Map source columns into Argilla fields, suggestions, metadata, vectors, and id."""
    return {
        "row_id": "id",
        "text": DEFAULT_FIELD_NAME,
        "predicted_label": f"{DEFAULT_QUESTION_NAME}.suggestion.value",
        "prediction_score": f"{DEFAULT_QUESTION_NAME}.suggestion.score",
        "prediction_agent": f"{DEFAULT_QUESTION_NAME}.suggestion.agent",
        "split": "split",
        "embedding": DEFAULT_VECTOR_NAME,
    }


def build_settings(rg):
    """Build Argilla settings. Requires an initialized rg.Argilla client/default."""
    return rg.Settings(
        guidelines="Review the text and choose the most appropriate label.",
        fields=[rg.TextField(name=DEFAULT_FIELD_NAME, title="Text", use_markdown=False)],
        questions=[
            rg.LabelQuestion(
                name=DEFAULT_QUESTION_NAME,
                labels=["positive", "negative"],
                title="Predicted sentiment",
            )
        ],
        metadata=[rg.TermsMetadataProperty(name="split", options=["train", "validation", "test"])],
        vectors=[rg.VectorField(name=DEFAULT_VECTOR_NAME, dimensions=DEFAULT_VECTOR_DIMENSIONS)],
        distribution=rg.TaskDistribution(min_submitted=1),
    )


def build_client(args):
    """Create a live Argilla client only when --create is used."""
    import argilla as rg

    http_client_args = {}
    if args.hf_token:
        http_client_args["headers"] = {"Authorization": f"Bearer {args.hf_token}"}

    return rg, rg.Argilla(
        api_url=args.api_url,
        api_key=args.api_key,
        timeout=args.timeout,
        retries=args.retries,
        **http_client_args,
    )


def create_dataset(args):
    rg, client = build_client(args)
    settings = build_settings(rg)

    existing = client.datasets(name=args.dataset_name, workspace=args.workspace)
    if existing is not None and not args.allow_existing:
        raise RuntimeError(
            f"Dataset {args.dataset_name!r} already exists in workspace {args.workspace!r}; "
            "choose another name or pass --allow-existing to log into it."
        )

    if existing is None:
        dataset = rg.Dataset(
            name=args.dataset_name,
            workspace=args.workspace,
            settings=settings,
            client=client,
        ).create()
    else:
        dataset = existing

    dataset.records.log(
        build_source_rows(),
        mapping=build_mapping(),
        user_id=client.me.id,
        batch_size=args.batch_size,
    )
    return dataset


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dry-run-safe Argilla dataset template. Add --create to contact a live server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE)
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://localhost:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY"))
    parser.add_argument("--hf-token", default=os.getenv("HF_TOKEN"), help="Optional HF token for private Spaces header")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--allow-existing", action="store_true", help="Log records into an existing dataset with the same name")
    parser.add_argument("--create", action="store_true", help="Create/log against a live Argilla server")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.create:
        print("Dry run only. No Argilla client was created and no server was contacted.")
        print("\nSettings summary:")
        pprint(
            {
                "dataset_name": args.dataset_name,
                "workspace": args.workspace,
                "field": DEFAULT_FIELD_NAME,
                "question": DEFAULT_QUESTION_NAME,
                "metadata": ["split"],
                "vector": {DEFAULT_VECTOR_NAME: DEFAULT_VECTOR_DIMENSIONS},
            }
        )
        print("\nExample source rows:")
        pprint(build_source_rows())
        print("\nMapping:")
        pprint(build_mapping())
        print("\nRun with --create and credentials when you intentionally want live server mutation.")
        return 0

    if not args.api_key:
        raise SystemExit("--create requires --api-key or ARGILLA_API_KEY")

    dataset = create_dataset(args)
    print(f"Created or updated dataset: {dataset.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def render_template(args: argparse.Namespace) -> str:
    vector_dimensions = args.vector_dimensions
    if vector_dimensions < 1:
        raise ValueError("--vector-dimensions must be >= 1")
    if vector_dimensions > 3:
        raise ValueError("This minimal template ships 3 example vector values; choose <= 3 or edit the generated rows")

    return (
        _TEMPLATE
        .replace("__DATASET_NAME__", repr(args.dataset_name))
        .replace("__WORKSPACE__", repr(args.workspace))
        .replace("__FIELD_NAME__", repr(args.field_name))
        .replace("__QUESTION_NAME__", repr(args.question_name))
        .replace("__VECTOR_NAME__", repr(args.vector_name))
        .replace("__VECTOR_DIMENSIONS__", str(vector_dimensions))
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print or write a dry-run-safe Argilla dataset/settings/records Python template.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-name", default="example_argilla_dataset", help="Default dataset name in the generated template")
    parser.add_argument("--workspace", default="argilla", help="Default workspace in the generated template")
    parser.add_argument("--field-name", default="text", help="Text field name")
    parser.add_argument("--question-name", default="label", help="Label question name")
    parser.add_argument("--vector-name", default="embedding", help="Vector field name")
    parser.add_argument("--vector-dimensions", type=int, default=3, help="Vector dimensions for the minimal example")
    parser.add_argument("--output", type=Path, help="Optional file to write instead of printing to stdout")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    content = render_template(args)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(f"Wrote Argilla dataset template to {args.output}", file=sys.stderr)
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
