# Repository provenance

This generated skill was built from the following source snapshot.

| Field | Value |
| --- | --- |
| VCS | git |
| Source repository | `google-gemini/genai-processors` |
| Public repository URL | `https://github.com/google-gemini/genai-processors` |
| Commit | `11d2f9cc480dccc700958bce635d2adb50ca9b6d` |
| Branch | `main` |
| Exact tag | none detected |
| Package version | `2.0.3` |
| Dirty state | dirty at generation time; untracked `skills/` directory present |

## Evidence paths used

- `pyproject.toml`
- `README.md`
- `README.pypi.md`
- `llms.txt`
- `CONTRIBUTING.md`
- `documentation/docs/`
- `examples/`
- `genai_processors/`
- `genai_processors/tests/`
- `notebooks/`

## Refresh guidance

Refresh this skill when any of the following change:

- `genai_processors/content_api.py`, `processor.py`, `streams.py`, `switch.py`,
  or cache/tracing modules.
- Model wrapper modules under `genai_processors/core/` or `genai_processors/contrib/`.
- Multimodal I/O modules such as `audio_io.py`, `video.py`, `speech_to_text.py`,
  `text_to_speech.py`, `pdf.py`, `web.py`, `drive.py`, or `github.py`.
- Example workflow files under `examples/` or their documentation under
  `documentation/docs/examples/`.
- Package dependencies, extras, or Python support in `pyproject.toml`.

The source checkout had local skill-generation artifacts when this skill was
created. Treat the commit plus the dirty-state note as the refresh baseline.
