from __future__ import annotations

import argparse, json, math

HIGH_PRIORITIES = {"critical", "voip"}

def validate_scenario(scenario):
    links = {link["id"]: link for link in scenario["links"]}
    assert links, "at least one link is required"
    for link in links.values():
        assert link["capacity"] > 0, "link capacity must be positive"
    for flow in scenario["flows"]:
        assert flow["demand"] >= 0, "flow demand must be non-negative"
        assert flow["allowed_links"], "flow needs allowed links"
        for link_id in flow["allowed_links"]:
            assert link_id in links, f"unknown link {link_id}"
    return scenario

def mm1k_loss(rho, queue_size):
    if abs(rho - 1.0) < 1e-9:
        return 1.0 / (queue_size + 1.0)
    return ((1.0-rho) * (rho ** queue_size)) / (1.0 - rho ** (queue_size + 1.0))

def mm1k_delay(rho, queue_size, service_rate_pps):
    if rho <= 0:
        return 1.0 / service_rate_pps
    if abs(rho - 1.0) < 1e-9:
        packets = queue_size / 2.0
    else:
        packets = rho/(1-rho) - ((queue_size+1)*(rho**(queue_size+1)))/(1-rho**(queue_size+1))
    arrival = max(rho * service_rate_pps, 1e-9)
    effective = arrival * (1.0 - mm1k_loss(rho, queue_size))
    return packets / max(effective, 1e-9)

def estimate_sabe(link, measurement, packet_size_bits=12000, queue_size=100, theta=0.914):
    service_rate = max(link["capacity"] * 1_000_000 / packet_size_bits, 1e-9)
    observed_loss = max(measurement.get("loss", 0.0), 0.0)
    observed_delay = max(measurement.get("delay", 0.0), 0.0)
    candidates = [i/1000 for i in range(1, 999)]
    if observed_loss > 0:
        rho = min(candidates, key=lambda r: abs(mm1k_loss(r, queue_size) - observed_loss))
        signal = "loss"
    else:
        rho = min(candidates, key=lambda r: abs(mm1k_delay(r, queue_size, service_rate) - observed_delay))
        signal = "delay"
    total_mbps = rho * link["capacity"]
    cross_mbps = max(0.0, total_mbps - measurement.get("controlled_traffic", 0.0))
    available = max(0.0, theta * link["capacity"] - cross_mbps)
    return {"rho": rho, "estimated_total_mbps": total_mbps, "cross_traffic_mbps": cross_mbps, "available_mbps": available, "signal": signal}

def fixed_allocation(scenario):
    validate_scenario(scenario)
    alloc = {flow["id"]: {} for flow in scenario["flows"]}
    for link in scenario["links"]:
        users = [f for f in scenario["flows"] if link["id"] in f["allowed_links"]]
        total = sum(f["demand"] for f in users) or 1.0
        for flow in users:
            alloc[flow["id"]][link["id"]] = link["capacity"] * flow["demand"] / total
    return alloc

def local_search_allocation(scenario, estimates, delta=0.25):
    validate_scenario(scenario)
    remaining = {l["id"]: estimates.get(l["id"], {}).get("available_mbps", l["capacity"]) for l in scenario["links"]}
    alloc = {flow["id"]: {link: 0.0 for link in flow["allowed_links"]} for flow in scenario["flows"]}
    trace=[]
    for flow in scenario["flows"]:
        if flow["priority"].lower() in HIGH_PRIORITIES:
            need = flow["demand"]
            for link_id in flow["allowed_links"]:
                take = min(need, remaining[link_id])
                alloc[flow["id"]][link_id] += take; remaining[link_id] -= take; need -= take
                trace.append({"phase":"high_priority", "flow":flow["id"], "link":link_id, "rate":take})
                if need <= 1e-9: break
    while True:
        best=None
        for flow in scenario["flows"]:
            if flow["priority"].lower() in HIGH_PRIORITIES: continue
            allocated=sum(alloc[flow["id"]].values())
            unmet=flow["demand"]-allocated
            if unmet <= 1e-9: continue
            for link_id in flow["allowed_links"]:
                if remaining[link_id] > 1e-9:
                    score=unmet/max(flow["delay_sla"],1e-9)
                    if best is None or score > best[0]: best=(score, flow, link_id, unmet)
        if best is None: break
        _, flow, link_id, unmet = best
        step=min(delta, unmet, remaining[link_id])
        alloc[flow["id"]][link_id]+=step; remaining[link_id]-=step
        trace.append({"phase":"low_priority_search", "flow":flow["id"], "link":link_id, "rate":step})
    return {"allocation": alloc, "remaining_capacity": remaining, "trace": trace}

def evaluate_sla(scenario, allocation):
    validate_scenario(scenario)
    rows=[]; critical_total=0; critical_ok=0
    for flow in scenario["flows"]:
        allocated=sum(allocation.get(flow["id"], {}).values())
        ratio=allocated/max(flow["demand"],1e-9)
        delay=flow["base_delay"] + max(0.0, 1-ratio)*flow["delay_penalty"]
        loss=flow["base_loss"] + max(0.0, 1-ratio)*flow["loss_penalty"]
        ok=delay <= flow["delay_sla"] and loss <= flow["loss_sla"]
        rows.append({"flow":flow["id"], "priority":flow["priority"], "allocated":allocated, "delay":delay, "loss":loss, "sla_ok":ok})
        if flow["priority"].lower() in HIGH_PRIORITIES:
            critical_total += 1; critical_ok += int(ok)
    return {"rows": rows, "critical_sla_satisfaction": 100.0*critical_ok/max(critical_total,1), "overall_sla_satisfaction": 100.0*sum(r["sla_ok"] for r in rows)/max(len(rows),1)}

def run_reduced_experiment(scenario):
    estimates={link["id"]: estimate_sabe(link, scenario["measurements"][link["id"]]) for link in scenario["links"]}
    baseline=fixed_allocation(scenario)
    optimized=local_search_allocation(scenario, estimates, delta=scenario.get("delta",0.25))
    base_eval=evaluate_sla(scenario, baseline)
    opt_eval=evaluate_sla(scenario, optimized["allocation"])
    improvement=opt_eval["critical_sla_satisfaction"]-base_eval["critical_sla_satisfaction"]
    return {"estimates": estimates, "baseline_allocation": baseline, "optimized": optimized, "baseline_eval": base_eval, "optimized_eval": opt_eval, "critical_sla_satisfaction_improvement_pp": improvement}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("scenario"); ap.add_argument("--output", required=True)
    ns=ap.parse_args(); scenario=json.load(open(ns.scenario))
    result=run_reduced_experiment(scenario)
    json.dump(result, open(ns.output,"w"), indent=2)
    print(json.dumps({"ok": True, "improvement": result["critical_sla_satisfaction_improvement_pp"]}))
if __name__ == "__main__": main()
