#!/usr/bin/env python3
from haystack import Pipeline, component, Document


@component
class Echo:
    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": text.upper()}


def main() -> int:
    doc = Document(content="haystack", meta={"source": "smoke"})
    pipe = Pipeline()
    pipe.add_component("echo", Echo())
    result = pipe.run({"echo": {"text": doc.content}})
    assert result["echo"]["text"] == "HAYSTACK"
    print({"ok": True, "document_meta": doc.meta, "pipeline_output": result["echo"]["text"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
