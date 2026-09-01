import pathlib

def test_harness_declares_source_boundary():
    text=(pathlib.Path(__file__).parents[1]/'SKILL.md').read_text()
    assert 'never read the original repository' in text
    assert 'reduced/proxy' in text

def test_harness_script_does_not_embed_original_repo_path():
    script=(pathlib.Path(__file__).parents[1]/'scripts'/'proxy_harness.py').read_text()
    assert 'QingruZhang/AdaLoRA' not in script
    assert 'paper2skills_workspace/paper/adalora_adaptive_budget/repo' not in script
