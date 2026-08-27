# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Agriculture_KnowledgeGraph checkout. If the current commit, dirty state, source layout, dependency surface, or major evidence paths differ from this snapshot, refresh the skill before relying on detailed workflow guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:13:13Z",
  "repository": {
    "name": "Agriculture_KnowledgeGraph",
    "remote_url": "https://github.com/qq547276542/Agriculture_KnowledgeGraph.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ccda905b03cacc659ad3a3a65fbc08019bf08ea2",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "demo",
        "Model",
        "toolkit",
        "KNN_predict modules",
        "MyCrawler",
        "wikidataCrawler",
        "wikidataRelation",
        "wikientities",
        "relationExtraction.algorithm"
      ],
      "note": "Repository has no pyproject.toml, setup.py, setup.cfg, or package metadata; this is a source application/research checkout."
    }
  ],
  "evidence": {
    "source_roots": [
      "demo/Model",
      "demo/demo",
      "demo/toolkit",
      "KNN_predict",
      "MyCrawler/MyCrawler",
      "dfs_tree_crawler",
      "wikidataSpider",
      "relationExtraction"
    ],
    "docs": [
      "README.md",
      "KNN_predict/README.md",
      "predict label/README.md",
      "wikidataSpider/readme.md",
      "wikidataSpider/TrainDataBaseOnWiki/readme.md",
      "wikidataSpider/weatherData/readme.md",
      "relationExtraction/readme.md",
      "relationExtraction/data/readme.md"
    ],
    "examples": [],
    "tests": [],
    "configs": [
      "requirement.txt",
      "demo/demo/settings.py",
      "MyCrawler/scrapy.cfg",
      "wikidataSpider/wikidataRelation/scrapy.cfg",
      "wikidataSpider/wikientities/scrapy.cfg",
      "relationExtraction/algorithm/config.py"
    ],
    "data_schema_samples": [
      "hudong_pedia.csv",
      "hudong_pedia2.csv",
      "attributes.csv",
      "labels.txt",
      "predict_labels.txt",
      "wikidataSpider/wikidataProcessing/new_node.csv",
      "wikidataSpider/wikidataProcessing/wikidata_relation.csv",
      "wikidataSpider/wikidataProcessing/wikidata_relation2.csv",
      "wikidataSpider/weatherData/static_weather_list.csv",
      "wikidataSpider/weatherData/weather_plant.csv",
      "wikidataSpider/weatherData/city_weather.csv",
      "wikidataSpider/TrainDataBaseOnWiki/finalData/train_data.txt"
    ],
    "excluded_large_or_generated": [
      "large crawled CSV/JSON/corpus/vector artifacts",
      "demo/static vendored assets",
      "notebooks",
      "PPT/PDF presentation and paper files",
      "skills/tests verification artifacts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the current checkout has changed Django routes, graph schemas, crawler outputs, relation-extraction config, dependency declarations, or major data file headers, refresh the skill even when the commit is similar.
- If a future checkout adds package metadata, tests, or a maintained installation path, refresh the environment and verification notes.
- Generated skill files are not part of the source baseline; compare source/application changes rather than the presence of this skill directory.
