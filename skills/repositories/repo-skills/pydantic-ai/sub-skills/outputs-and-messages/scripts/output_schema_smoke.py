#!/usr/bin/env python3
"""No-network smoke check for Pydantic AI structured output and message serialization.

Usage:
    python output_schema_smoke.py

The script is safe to run from any current working directory. It imports the
installed `pydantic_ai` package, uses `TestModel` only, performs no network
requests, and writes no files.
"""

from __future__ import annotations

from pydantic import BaseModel

from pydantic_ai import Agent, BinaryContent, ModelMessagesTypeAdapter, ToolOutput
from pydantic_ai.models.test import TestModel


class Extraction(BaseModel):
    title: str
    score: int


def main() -> None:
    model = TestModel(custom_output_args={'title': 'example', 'score': 7})
    agent = Agent(model, output_type=ToolOutput(Extraction, name='return_extraction'))

    result = agent.run_sync('Extract a title and score.')
    assert result.output == Extraction(title='example', score=7)

    schema = agent.output_json_schema()
    assert schema['type'] == 'object'
    assert set(schema['required']) == {'title', 'score'}

    messages = result.all_messages()
    serialized = ModelMessagesTypeAdapter.dump_json(messages)
    restored = ModelMessagesTypeAdapter.validate_json(serialized)
    assert len(restored) == len(messages)
    assert [message.kind for message in restored] == [message.kind for message in messages]
    assert any(message.kind == 'response' for message in restored)

    binary = BinaryContent(data=b'hello', media_type='text/plain')
    assert binary.base64 == 'aGVsbG8='
    assert binary.is_document

    print('pydantic-ai output/message smoke passed')


if __name__ == '__main__':
    main()
