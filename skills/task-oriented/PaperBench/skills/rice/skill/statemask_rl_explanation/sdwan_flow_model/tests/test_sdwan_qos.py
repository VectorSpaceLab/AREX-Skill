import json, tempfile
from sdwan_qos import validate_scenario, estimate_sabe, fixed_allocation, local_search_allocation, evaluate_sla, run_reduced_experiment

def scenario():
    return {"links":[{"id":"mpls","capacity":6.0},{"id":"internet","capacity":5.0}],"measurements":{"mpls":{"delay":0.0022,"loss":0.0,"controlled_traffic":1.0},"internet":{"delay":0.0025,"loss":0.0,"controlled_traffic":1.0}},"delta":0.5,"flows":[{"id":"critical","priority":"critical","demand":4.0,"allowed_links":["mpls","internet"],"delay_sla":0.04,"loss_sla":0.001,"base_delay":0.03,"base_loss":0.0,"delay_penalty":0.08,"loss_penalty":0.02},{"id":"voip","priority":"voip","demand":3.0,"allowed_links":["mpls","internet"],"delay_sla":0.06,"loss_sla":0.02,"base_delay":0.035,"base_loss":0.001,"delay_penalty":0.04,"loss_penalty":0.01},{"id":"office","priority":"office","demand":20.0,"allowed_links":["mpls","internet"],"delay_sla":0.25,"loss_sla":0.05,"base_delay":0.05,"base_loss":0.005,"delay_penalty":0.3,"loss_penalty":0.08}]}

def test_validate_and_sabe_estimate():
    s=scenario(); validate_scenario(s)
    low=estimate_sabe(s["links"][0], {"delay":0.02,"loss":0.0,"controlled_traffic":1.0})
    high=estimate_sabe(s["links"][0], {"delay":0.2,"loss":0.01,"controlled_traffic":1.0})
    assert high["available_mbps"] <= low["available_mbps"]

def test_local_search_improves_critical_sla():
    result=run_reduced_experiment(scenario())
    assert result["critical_sla_satisfaction_improvement_pp"] > 0
    assert result["optimized"]["trace"]
