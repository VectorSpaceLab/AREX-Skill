import run_recovery


def test_harness_exports_main_and_loader():
    assert callable(run_recovery.main)
    assert callable(run_recovery.load_module)
