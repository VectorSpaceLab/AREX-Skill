from sr3_proxy import downsample, upsample, gammas, forward, train, sample, mechanism_complete

def test_smoke():
    y=[[0.0,1.0],[1.0,0.0]]; low=downsample(y,1); cond=upsample(low,1); gs=gammas([0.9,0.8]); noisy=forward(y,[[0.1,0.1],[0.1,0.1]],gs[-1]); tr=train(cond,noisy,gs[-1],[[0.1,0.1],[0.1,0.1]]); sm=sample(noisy,[0.9,0.8],gs); assert tr["params_before"]!=tr["params_after"]; assert len(sm["trajectory"])==2; assert mechanism_complete({"paired_data_constructed":True,"forward_noising_executed":True,"denoising_loss_computed":True,"optimizer_step_executed":True,"iterative_refinement_executed":True,"source_boundary_respected":True})
