# Prompt and Timestamp Format

## What AI Clip parses

`funclip/utils/trans_utils.py::extract_timestamps` reads only bracketed SRT
ranges of the form:

```text
[HH:MM:SS,mmm-HH:MM:SS,mmm]
```

or, more loosely, with whitespace around the dash:

```text
[HH:MM:SS,50 - HH:MM:SS,500]
```

The leading line number is ignored by the parser. Text after the closing bracket
is also ignored by the parser, but it remains useful for humans and for the clip
workflow.

The parser accepts 2- or 3-digit millisecond fields, so both `,50` and `,500`
are valid. Decimal seconds such as `12.5` are not valid input for
`extract_timestamps`.

## Default transcript-route prompt

The built-in prompt in `demo_prompt.py` and the launcher asks the model to:

- pick up to four meaningful highlight segments;
- merge adjacent sentences that belong together;
- keep the timestamps aligned with the transcript;
- output one segment per line in the exact `1. [start-end] text` form.

For transcript-based providers, the launcher concatenates `user_content + "\n" + srt_text` before sending the prompt.

## Pegasus normalization

TwelveLabs Pegasus returns decimal-second ranges such as `12.5` and `120`.
`funclip/llm/twelvelabs_api.py` normalizes them to SRT timestamps before the
result reaches AI Clip.

Examples:

- `12.5` -> `00:00:12,500`
- `120` -> `00:02:00,000`
- existing SRT output stays unchanged

The normalizer leaves invalid or reversed ranges unchanged and logs a warning,
so the downstream parser still rejects them.

## Parseable examples

```text
1. [00:00:12,500-00:00:15,000] opening shot
2. [00:02:00,000 - 00:02:15,000] second highlight
3. [00:03:10,250-00:03:20,750] closing beat
```

`extract_timestamps(...)` returns:

```text
[[12500, 15000], [120000, 135000], [190250, 200750]]
```

## Unparseable examples

```text
1. [12.5-15.0] decimal seconds
2. [15-12.5] reversed range
3. 00:00:12,500-00:00:15,000 missing brackets
4. [00:00:12.500-00:00:15.000] dot milliseconds
5. [00:00:12,500-00:00:15,000 extra text
```

These are not recognized by `extract_timestamps` and therefore will not feed
AI Clip correctly.

## AI Clip path context

The LLM result flows into the `LLM Clipper Result` textbox, then into the AI
Clip buttons, which convert the bracketed ranges into millisecond pairs and pass
those pairs to the clip-workflows sub-skill. If this parser cannot read the
ranges, the clip stage has nothing usable to trim.
