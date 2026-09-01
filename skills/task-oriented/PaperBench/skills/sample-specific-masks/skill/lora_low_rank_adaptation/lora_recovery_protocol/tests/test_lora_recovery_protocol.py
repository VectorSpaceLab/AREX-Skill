import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

def test_skill_smoke():
    from protocol import proxy_acceptance
    r=proxy_acceptance(10.0,2.0,0.0); assert r['accepted']; assert r['loss_reduction_fraction']==0.8


def test_source_boundary_helper_rejects_repo_path():
    from protocol import source_boundary_ok
    assert source_boundary_ok(['paper_profile.md','environment/runtime_handoff.json'], '/repo')
    assert not source_boundary_ok(['/tmp/paper/repo/loralib.py'], '/repo')
