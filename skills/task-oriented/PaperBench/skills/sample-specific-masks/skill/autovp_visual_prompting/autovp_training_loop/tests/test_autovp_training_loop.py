from autovp_training_loop import train_one_step

def test_prompt_changes_classifier_frozen():
    tr=train_one_step()
    assert tr['params_before'] != tr['params_after']
    assert tr['classifier_before'] == tr['classifier_after']
    assert tr['loss_after'] < tr['loss_before']
