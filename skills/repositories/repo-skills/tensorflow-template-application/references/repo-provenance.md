# Repository Provenance

This snapshot tells future agents whether the generated skill still matches the repository checkout that was used to create it.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:14:37Z",
  "repository": {
    "name": "tensorflow-template-application",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a2be179bf5e2624cdc3c0ed3cf8b5f7eff87777d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "trainer",
      "version": "1.0",
      "import_names": ["trainer"]
    }
  ],
  "evidence": {
    "source_roots": [
      "trainer/",
      "dense_classifier.py",
      "sparse_classifier.py",
      "model.py",
      "sparse_model.py",
      "util.py"
    ],
    "docs": [
      "README.md",
      "data/README.md",
      "python_predict_client/README.md",
      "minimal_model/README.md",
      "http_service/README.md",
      "java_predict_client/README.md",
      "golang_predict_client/README.md",
      "cpp_predict_client/README.md",
      "ios_client/README.md",
      "distributed/README.md"
    ],
    "examples": [
      "data/cancer/generate_tfrecords_from_csv.py",
      "data/a8a/generate_tfrecords_from_libsvm.py",
      "data/iris/download_iris.py",
      "python_predict_client/predict_client.py",
      "python_predict_client/sparse_predict_client.py",
      "minimal_model/train.py",
      "tensorboard_tools/read_event_files.py"
    ],
    "tests": [
      "http_service/cancer_predict/tests.py",
      "android_client/app/src/test/java/com/tobe/androidclient/ExampleUnitTest.java",
      "android_client/app/src/androidTest/java/com/tobe/androidclient/ExampleInstrumentedTest.java"
    ],
    "configs": [
      "setup.py",
      "requirements.txt",
      "python_predict_client/requirements.txt",
      "java_predict_client/pom.xml",
      "android_client/app/build.gradle",
      "ios_client/Podfile"
    ]
  }
}
```

## Refresh note

If the repository commit, package version, or evidence paths change materially, refresh this skill instead of assuming it is still current.
