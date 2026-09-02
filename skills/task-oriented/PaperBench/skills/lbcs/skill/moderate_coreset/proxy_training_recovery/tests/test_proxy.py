from pathlib import Path
import tempfile, json, shutil
from run_proxy_recovery import synthetic_records, loss, train_step

def test_train_step_changes_params_and_loss():
    records=synthetic_records()[:6]
    params={'w0':0.0,'w1':0.0,'b':0.0}
    before=loss(records, params)
    after_params, grad=train_step(records, params)
    after=loss(records, after_params)
    assert after_params != params
    assert after < before
