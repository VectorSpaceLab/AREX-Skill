#!/usr/bin/env python3
"""List Simple Transformers args dataclass fields for quick configuration inspection."""
import argparse
from dataclasses import MISSING, fields, is_dataclass

from simpletransformers.config import model_args

DEFAULT_CLASSES = [
    "ModelArgs",
    "ClassificationArgs",
    "MultiLabelClassificationArgs",
    "NERArgs",
    "QuestionAnsweringArgs",
    "LanguageModelingArgs",
    "Seq2SeqArgs",
    "T5Args",
    "RetrievalArgs",
    "LanguageGenerationArgs",
    "ConvAIArgs",
    "MultiModalClassificationArgs",
]


def main(argv=None):
    p = argparse.ArgumentParser(description="Print fields for Simple Transformers args dataclasses.")
    p.add_argument("classes", nargs="*", default=DEFAULT_CLASSES)
    args = p.parse_args(argv)
    for name in args.classes:
        cls = getattr(model_args, name, None)
        if cls is None or not is_dataclass(cls):
            print(f"{name}: not found or not a dataclass")
            continue
        print(f"## {name}")
        for f in fields(cls):
            if f.default_factory is not MISSING:
                default = "<factory>"
            elif f.default is not MISSING:
                default = f.default
            else:
                default = "<required>"
            print(f"- {f.name}: {f.type} default={default!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
