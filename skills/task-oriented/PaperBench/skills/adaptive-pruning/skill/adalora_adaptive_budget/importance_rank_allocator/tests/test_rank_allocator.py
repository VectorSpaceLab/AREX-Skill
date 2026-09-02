from rank_allocator import allocate

def test_allocator_keeps_high_importance_triplet():
    mats=[{'id':'m','A':[[1,0],[0.01,0]],'E':[1,1],'B':[[1,0.01]],'A_grad':[[5,0],[0.01,0]],'E_grad':[5,0.01],'B_grad':[[5,0.01]]}]
    res=allocate(mats,1,beta1=0.5,beta2=0.5)
    assert res['matrices'][0]['E_masked']==[1,0.0]
    assert res['rank_pattern']['m']==1

def test_zero_target_masks_all_triplets():
    mats=[{'id':'m','A':[[1],[2]],'E':[3,4],'B':[[1,2]],'A_grad':[[1],[1]],'E_grad':[1,1],'B_grad':[[1,1]]}]
    res=allocate(mats,0,beta1=0.5,beta2=0.5)
    assert res['matrices'][0]['E_masked']==[0.0,0.0]
    assert res['rank_pattern']['m']==0
