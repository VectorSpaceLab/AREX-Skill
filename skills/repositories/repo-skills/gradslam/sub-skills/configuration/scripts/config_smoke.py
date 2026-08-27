#!/usr/bin/env python3
"""Run deterministic, local CfgNode construction and merge checks.

The check uses only in-memory YAML plus temporary YAML/Python files. It does
not download data, require a GPU, or depend on the current working directory.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from gradslam.config import CfgNode as CN


def make_base() -> CN:
    """Create a small strict schema with one explicit extension boundary."""
    cfg = CN(
        {
            "MODEL": {"NAME": "tiny", "LAYERS": (1, 2)},
            "TRAIN": {"LR": 0.1},
        }
    )
    cfg.EXTRA = CN(new_allowed=True)
    cfg.EXTRA.SEED = 7
    cfg.EXTRA.NESTED = CN()
    return cfg


def run_checks() -> None:
    """Assert the supported loading, merging, diagnostics, and copy behavior."""
    cfg = make_base()

    # YAML text is loaded as a node; list-to-tuple coercion preserves the schema.
    yaml_overlay = CN.load_cfg(
        "MODEL:\n  LAYERS: [3, 4]\nTRAIN:\n  LR: 0.05\n"
    )
    cfg.merge_from_other_cfg(yaml_overlay)
    assert cfg.MODEL.LAYERS == (3, 4)
    assert cfg.TRAIN.LR == 0.05

    # A later CLI-style layer wins and decodes literals.
    cfg.merge_from_list(
        ["TRAIN.LR", "0.01", "MODEL.NAME", "tiny-cli", "MODEL.LAYERS", "[5, 6]"]
    )
    assert cfg.TRAIN.LR == 0.01
    assert cfg.MODEL.NAME == "tiny-cli"
    assert cfg.MODEL.LAYERS == (5, 6)

    # Supported path-based YAML loading and Python cfg export loading.
    with tempfile.TemporaryDirectory(prefix="gradslam-config-") as tmp:
        tmp_path = Path(tmp)
        yaml_path = tmp_path / "overlay.yaml"
        yaml_path.write_text("EXTRA:\n  FILE_VALUE: 11\n", encoding="utf-8")
        cfg.merge_from_file(str(yaml_path))
        assert cfg.EXTRA.FILE_VALUE == 11

        py_path = tmp_path / "overlay.py"
        py_path.write_text(
            "cfg = {'MODEL': {'NAME': 'tiny-python'}}\n", encoding="utf-8"
        )
        cfg.merge_from_file(str(py_path))
        assert cfg.MODEL.NAME == "tiny-python"

    # new_allowed is local: the extension node admits a new field, its child does not.
    cfg.merge_from_other_cfg(CN({"EXTRA": {"PLUGIN": {"ENABLED": True}}}))
    assert cfg.EXTRA.PLUGIN.ENABLED is True
    try:
        cfg.merge_from_other_cfg(CN({"EXTRA": {"NESTED": {"NEW": 1}}}))
    except KeyError as exc:
        assert "EXTRA.NESTED.NEW" in str(exc)
    else:
        raise AssertionError("strict nested new-key boundary was not enforced")

    # Deprecated keys are ignored; renamed keys identify the replacement.
    cfg.register_deprecated_key("OLD.VALUE")
    cfg.merge_from_list(["OLD.VALUE", "1"])
    assert "OLD" not in cfg
    cfg.register_renamed_key("MODEL.OLD_NAME", "MODEL.NAME", "use MODEL.NAME")
    try:
        cfg.merge_from_list(["MODEL.OLD_NAME", "old"])
    except KeyError as exc:
        assert "MODEL.NAME" in str(exc)
    else:
        raise AssertionError("renamed key did not raise")

    # Freeze propagates to children; clone/defrost is the safe variant workflow.
    cfg.freeze()
    assert cfg.is_frozen() and cfg.MODEL.is_frozen()
    try:
        cfg.MODEL.NAME = "blocked"
    except AttributeError:
        pass
    else:
        raise AssertionError("frozen attribute assignment did not fail")
    variant = cfg.clone()
    variant.defrost()
    variant.MODEL.NAME = "variant"
    variant.merge_from_list(["TRAIN.LR", "0.02"])
    assert variant.MODEL.NAME == "variant" and variant.TRAIN.LR == 0.02
    assert cfg.MODEL.NAME == "tiny-python"

    # dump is YAML; str/repr are distinct diagnostics.
    dumped = cfg.dump()
    assert "MODEL:" in dumped and "CfgNode(" not in dumped
    assert "MODEL:" in str(cfg)
    assert "CfgNode(" in repr(cfg)
    loaded = CN.load_cfg(dumped)
    assert loaded.MODEL.NAME == cfg.MODEL.NAME


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local deterministic gradSLAM CfgNode smoke checks."
    )
    parser.parse_args()
    run_checks()
    print("configuration smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
