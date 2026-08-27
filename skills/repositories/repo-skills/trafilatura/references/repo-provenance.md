# Repo provenance

Schema: `disco.repo-provenance.v1`

This Trafilatura repo skill was generated from a clean public Git checkout.

## Source snapshot

| Field | Value |
| --- | --- |
| Package | Trafilatura |
| Canonical skill id | `trafilatura` |
| Distribution/import version | `trafilatura==2.2.0` |
| Source commit | `a397f890f75bd3f1df216915617839523010fae8` |
| Branch | `master` |
| Exact tag | none detected at generation time |
| Working tree state | clean |
| Remote URL | `https://github.com/adbar/trafilatura.git` |
| Python support from package metadata | `>=3.10` |
| Console script | `trafilatura = trafilatura.cli:main` |

## Evidence paths used

Primary package and metadata evidence:

- `pyproject.toml`
- `README.md`
- `trafilatura/__init__.py`
- `trafilatura/core.py`
- `trafilatura/baseline.py`
- `trafilatura/metadata.py`
- `trafilatura/settings.py`
- `trafilatura/settings.cfg`
- `trafilatura/cli.py`
- `trafilatura/cli_utils.py`
- `trafilatura/downloads.py`
- `trafilatura/feeds.py`
- `trafilatura/sitemaps.py`
- `trafilatura/spider.py`
- `trafilatura/deduplication.py`
- `trafilatura/xml.py`
- `trafilatura/utils.py`

Documentation evidence distilled into runtime references:

- `docs/installation.rst`
- `docs/quickstart.rst`
- `docs/usage-python.rst`
- `docs/corefunctions.rst`
- `docs/usage-cli.rst`
- `docs/downloads.rst`
- `docs/crawls.rst`
- `docs/url-management.rst`
- `docs/sources.rst`
- `docs/deduplication.rst`
- `docs/corpus-data.rst`
- `docs/settings.rst`
- `docs/evaluation.rst`
- `docs/tests.rst`
- `docs/troubleshooting.rst`
- `docs/tutorial0.rst`
- `docs/tutorial1.rst`
- `docs/tutorial2.rst`

Native behavior evidence used for candidate mapping and selected verification:

- `tests/unit_tests.py`
- `tests/baseline_tests.py`
- `tests/metadata_tests.py`
- `tests/json_metadata_tests.py`
- `tests/filters_tests.py`
- `tests/cli_tests.py`
- `tests/downloads_tests.py`
- `tests/feeds_tests.py`
- `tests/sitemaps_tests.py`
- `tests/spider_tests.py`
- `tests/deduplication_tests.py`
- `tests/xml_tei_tests.py`
- `tests/eval_common_tests.py`
- `tests/eval_gate_tests.py`
- `tests/README.rst`

## Extraction decisions

Included runtime skill coverage:

- Python extraction APIs and output serialization.
- CLI and local/batch processing.
- Download, feed, sitemap, and focused-crawl discovery workflows.
- Deduplication, fingerprints, structured output, TEI/XML validation, and benchmark/evaluation context.

Excluded or reference-only evidence:

- VCS/build/cache/media artifacts.
- Large benchmark HTML corpus files under evaluation fixtures.
- Documentation build workflow and CI internals.
- Broad development extras except the minimal test runner needed for selected native verification.
- Network, benchmark-scale, and optional-extra checks not safe for a no-network minimum verification pass.

## Refresh guidance

Refresh this skill when:

- The source commit changes materially in public API signatures, CLI flags, output formats, optional extras, settings, or downloader/crawler behavior.
- Trafilatura changes its supported Python versions or dependency/extras names.
- New docs/tests add user-facing workflows such as new output formats, discovery modes, or corpus-quality checks.
- A downstream task reports a mismatch between this skill's routes and installed Trafilatura behavior.

When refreshing, preserve self-containment: copy or distill updated source evidence into this skill's own references/scripts rather than linking future agents back to the source checkout.
