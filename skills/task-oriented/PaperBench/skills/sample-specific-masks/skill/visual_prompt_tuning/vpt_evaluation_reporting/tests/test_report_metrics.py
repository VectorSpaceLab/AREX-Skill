from report_metrics import *
def test_accuracy_and_storage():
    r=build_report([1,0,1],[1,1,1],100,2)
    assert abs(r['accuracy']-2/3)<1e-9
    assert abs(r['storage_multiplier']-1.02)<1e-9

def test_all_correct_accuracy():
    assert accuracy([0,1,1],[0,1,1])==1.0
