# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DataSciencePython. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:12:56Z",
  "repository": {
    "name": "DataSciencePython",
    "remote_url": "https://github.com/ujjwalkarn/DataSciencePython.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "524af797a786c12120b47970e2b654ff06efc350",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md"
    ],
    "examples": [
      "basic_commands.py",
      "svm_sklearn.py",
      "Logistic Regression with StatsModels/logistic.py",
      "Logistic Regression with StatsModels/train.csv",
      "Logistic Regression with StatsModels/test.csv",
      "Logistic-Regression/citreo.py",
      "Logistic-Regression/citreo_code_v2.py",
      "Logistic-Regression/classifier_corrected.py",
      "Logistic-Regression/logistic_regression_updated.py",
      "Twitter-Data-Analysis/extract_twitter_data.py",
      "Twitter-Data-Analysis/json2tweets.R"
    ],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the working tree contains source changes outside generated `skills/` outputs, refresh before trusting workflow details.
- If DataSciencePython later gains package metadata, tests, new runnable examples, or changed dependencies, refresh this skill so the route map and bundled helpers stay aligned.

## Notes

- This snapshot intentionally records no local checkout path, environment path, Python executable, cache location, or private setup command.
- The source repository has no installable package distribution at this commit; third-party dependency versions belong in private verification artifacts, not this public provenance file.
