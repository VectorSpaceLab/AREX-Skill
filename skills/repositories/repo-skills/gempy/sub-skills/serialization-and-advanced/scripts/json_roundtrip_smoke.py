#!/usr/bin/env python3
"""Deterministic core GemPy JSON and .gempy round-trip smoke test.

This helper generates a tiny model in memory and uses only temporary output.
It deliberately does not read repository examples, checkout data, or URLs.
It reports missing prerequisites instead of installing packages or pretending an
optional integration is a core failure.
"""

from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path


def main() -> int:
    try:
        import numpy as np
        import gempy as gp
        from gempy.modules.json_io import JsonIO
    except ImportError as exc:
        print(f"core prerequisite unavailable: {exc}", file=sys.stderr)
        return 2

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = gp.create_geomodel(
                project_name="serialization_smoke",
                extent=[0.0, 10.0, 0.0, 10.0, -10.0, 0.0],
                resolution=[4, 4, 4],
                structural_frame=gp.data.StructuralFrame.initialize_default_structure(),
            )
            gp.add_surface_points(
                model,
                x=[2.0, 5.0, 8.0],
                y=[2.0, 5.0, 8.0],
                z=[-2.0, -2.0, -2.0],
                elements_names=["surface1"] * 3,
            )
            gp.add_orientations(
                model,
                x=[5.0],
                y=[5.0],
                z=[-2.0],
                elements_names=["surface1"],
                pole_vector=[[0.0, 0.0, 1.0]],
            )
            model.validate()

            original_sp = np.array(model.surface_points_copy.data, copy=True)
            original_ori = np.array(model.orientations_copy.data, copy=True)

            with tempfile.TemporaryDirectory(prefix="gempy-serialization-smoke-") as tmp:
                root = Path(tmp)
                binary_path = gp.save_model(
                    model, str(root / "tiny-model"), validate_serialization=True
                )
                restored = gp.load_model(binary_path)
                np.testing.assert_array_equal(restored.surface_points_copy.data, original_sp)
                np.testing.assert_array_equal(restored.orientations_copy.data, original_ori)
                restored.validate()

                json_path = root / "tiny-model.json"
                JsonIO.save_model_to_json(model, str(json_path))
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                assert {"surface_points", "orientations", "grid_settings"} <= payload.keys()
                json_model = JsonIO.load_model_from_json(str(json_path))
                np.testing.assert_array_equal(json_model.surface_points_copy.data, original_sp)
                np.testing.assert_array_equal(json_model.orientations_copy.data, original_ori)
                json_model.validate()

                print(
                    "ok: binary={} json={} points={} orientations={}".format(
                        Path(binary_path).name,
                        json_path.name,
                        len(original_sp),
                        len(original_ori),
                    )
                )
        return 0
    except Exception as exc:  # make a smoke helper useful in minimal CI
        print(f"smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
