"""Compatibility helpers for legacy Libra workflows."""
from __future__ import annotations

import warnings


def apply() -> None:
    """Patch modern pandas/warnings so legacy Libra imports work."""
    try:
        import pandas.core.common as common
        from pandas.errors import SettingWithCopyWarning
    except Exception:
        common = None
    else:
        if not hasattr(common, 'SettingWithCopyWarning'):
            common.SettingWithCopyWarning = SettingWithCopyWarning

    warnings.simplefilter('ignore', FutureWarning)
