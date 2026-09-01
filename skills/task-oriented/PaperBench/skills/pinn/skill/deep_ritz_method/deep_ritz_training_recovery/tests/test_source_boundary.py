import json
import tempfile
from pathlib import Path


def test_source_manifest_excludes_original_repo_paths():
    with tempfile.TemporaryDirectory() as tmp:
        manifest = Path(tmp) / "source_manifest.json"
        manifest.write_text(json.dumps({
            "allowed_sources_used": ["paper.pdf", "module_plan.json"],
            "original_repo_source": "unknown",
            "original_repo_paths_read": []
        }))
        data = json.loads(manifest.read_text())
        assert data["original_repo_paths_read"] == []
        assert not any("/repo" in item for item in data["allowed_sources_used"])


if __name__ == "__main__":
    test_source_manifest_excludes_original_repo_paths()
