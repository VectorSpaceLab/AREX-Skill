#!/usr/bin/env python3
"""Print a read-only BasicTS install summary.

This helper is safe to run from any working directory. It reports the installed
package version, launcher signature, and a few core import paths so a future
agent can confirm the BasicTS runtime before opening deeper references.

Example:
    python scripts/check_basic_ts_install.py
"""

from __future__ import annotations

import inspect

from importlib.metadata import PackageNotFoundError, metadata, version


def main() -> int:
    try:
        import basicts
        from basicts import BasicTSLauncher
        from basicts.configs import BasicTSForecastingConfig, BasicTSClassificationConfig, BasicTSImputationConfig
        from basicts.data import BasicTSForecastingDataset, BasicTSImputationDataset, UEADataset, BLAST
        from basicts.metrics import ALL_METRICS
        from basicts.scaler import BasicTSScaler, ZScoreScaler, MinMaxScaler
    except Exception as exc:  # pragma: no cover - inspection helper
        print(f"import_error={type(exc).__name__}: {exc}")
        return 1

    try:
        dist_version = version("BasicTS")
        dist_name = metadata("BasicTS")["Name"]
    except PackageNotFoundError as exc:  # pragma: no cover - inspection helper
        print(f"metadata_error={type(exc).__name__}: {exc}")
        return 1

    print(f"distribution={dist_name}")
    print(f"version={dist_version}")
    print(f"package_version={basicts.__version__}")
    print(f"launcher_signature={inspect.signature(BasicTSLauncher.launch_training)}")
    print(f"evaluation_signature={inspect.signature(BasicTSLauncher.launch_evaluation)}")
    print(f"forecasting_cfg={inspect.signature(BasicTSForecastingConfig)}")
    print(f"classification_cfg={inspect.signature(BasicTSClassificationConfig)}")
    print(f"imputation_cfg={inspect.signature(BasicTSImputationConfig)}")
    print(f"forecasting_dataset={inspect.signature(BasicTSForecastingDataset.__init__)}")
    print(f"imputation_dataset={inspect.signature(BasicTSImputationDataset.__init__)}")
    print(f"uea_dataset={inspect.signature(UEADataset.__init__)}")
    print(f"blast_dataset={inspect.signature(BLAST.__init__)}")
    print(f"scaler_base={inspect.signature(BasicTSScaler.__init__)}")
    print(f"zscore_scaler={inspect.signature(ZScoreScaler.__init__)}")
    print(f"minmax_scaler={inspect.signature(MinMaxScaler.__init__)}")
    print(f"metric_count={len(ALL_METRICS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
