import tempfile
from pathlib import Path
import json
from run_recovery import run


def test_harness_function_exists_without_running_full_attempt():
    assert callable(run)
