# Repository Provenance

## Purpose

Read this before deciding whether this Sweetviz skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public API signatures, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:36:48Z",
  "repository": {
    "name": "sweetviz",
    "remote_url": "https://github.com/fbdesignpro/sweetviz",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.3.3",
    "commit": "4697e182c48cf2816a89fb0a8d402f9e4fe812fb",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "sweetviz",
      "version": "2.3.3",
      "import_names": ["sweetviz"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "MANIFEST.in"],
    "source_roots": ["sweetviz/"],
    "docs": ["README.md", "CHANGELOG.md"],
    "examples": ["docs/examples/SWEETVIZ_REPORT.html"],
    "tests": [],
    "configs": ["sweetviz/sweetviz_defaults.ini"],
    "runtime_assets": ["sweetviz/templates/", "sweetviz/mpl_styles/", "sweetviz/fonts/"],
    "excluded_source_artifacts": ["sweetviz/update_jquery.py"]
  },
  "verified_public_api": {
    "analyze": "analyze(source, target_feat=None, feat_cfg=None, pairwise_analysis='auto')",
    "compare": "compare(source, compare, target_feat=None, feat_cfg=None, pairwise_analysis='auto')",
    "compare_intra": "compare_intra(source_df, condition_series, names, target_feat=None, feat_cfg=None, pairwise_analysis='auto')",
    "FeatureConfig.__init__": "FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)",
    "DataframeReport.show_html": "show_html(filepath='SWEETVIZ_REPORT.html', open_browser=True, layout='widescreen', scale=None)",
    "DataframeReport.show_notebook": "show_notebook(w=None, h=None, scale=None, layout=None, filepath=None, file_layout=None, file_scale=None)"
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the stored commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot is clean, run `refresh-repo-skill` before relying on changed behavior.
- If package metadata, public entry points, public signatures, `sweetviz_defaults.ini`, or packaged asset layout changed, run `refresh-repo-skill` even on the same commit.
- If a future Sweetviz release adds a console CLI, changes `verbosity` handling on public constructors, or changes target/type inference rules, refresh this skill before using those newer facts.
