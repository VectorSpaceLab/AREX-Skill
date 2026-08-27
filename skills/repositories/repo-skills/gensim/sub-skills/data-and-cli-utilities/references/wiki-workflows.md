# Wikipedia Dump Workflows

## Segmenting article text

Use segmentation when you want JSON-lines records containing titles and article
sections. The package-level workflow accepts a compressed MediaWiki XML dump and
can write compressed output.

Planning checklist:

1. Verify the input is a MediaWiki XML dump, usually `.xml.bz2`.
2. Estimate dump size, disk space, worker count, and output compression.
3. Choose `min_article_character` and whether to include interlinks.
4. Run a tiny fixture first.
5. Only then run a full dump job.

Bundled tiny helper:

```bash
python scripts/segment_wiki_tiny.py --write-fixture tiny.xml.bz2
python scripts/segment_wiki_tiny.py --input tiny.xml.bz2 --output tiny.jsonl --min-article-character 10
```

## Building Wiki corpora

`make_wikicorpus` style workflows create several artifacts from a full dump:

- word-id dictionary text,
- BoW Matrix Market corpus and index,
- optional metadata/title files,
- TF-IDF corpus and model artifacts.

These outputs can be large. Create the output directory first, choose a prefix,
and confirm downstream consumers before launching.

## Online/hash dictionary variants

The online variants use `HashDictionary` and flags encoded by the module name.
They can reduce memory pressure but change the vocabulary/id behavior. Use them
only when hash-based ids are acceptable.

## What not to do

- Do not run full Wikipedia conversion as a package smoke test.
- Do not use network downloads implicitly inside a supposedly local workflow.
- Do not discard article-title metadata if the downstream task must map topics or
  similarity results back to pages.
