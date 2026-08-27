#!/usr/bin/env python3
"""Offline FedML workflow DAG smoke.

This helper validates Job subclasses, Workflow.add_job dependencies, topological
metadata, and input/output handoff without calling Workflow.run(), because the
real runner updates backend workflow state.
"""

from __future__ import annotations

from fedml.workflow import Job, JobStatus, Workflow


class LocalJob(Job):
    def __init__(self, name: str, value: int) -> None:
        super().__init__(name=name)
        self.value = value
        self._status = JobStatus.PROVISIONING

    def run(self) -> None:
        self._status = JobStatus.RUNNING
        upstream_total = 0
        for upstream_outputs in self.input_data_dict.values():
            upstream_total += int(upstream_outputs.get("total", 0))
        self.output_data_dict = {"total": upstream_total + self.value, "job": self.name}
        self._status = JobStatus.FINISHED

    def status(self) -> JobStatus:
        return self._status

    def kill(self) -> None:
        self._status = JobStatus.FAILED


def run_local_workflow() -> dict[str, dict]:
    workflow = Workflow("local-smoke")
    extract = LocalJob("extract", 1)
    transform = LocalJob("transform", 10)
    load = LocalJob("load", 100)

    workflow.add_job(extract)
    workflow.add_job(transform, dependencies=[extract])
    workflow.add_job(load, dependencies=[transform])

    metadata = workflow._compute_workflow_metadata()  # private but offline; avoids backend calls in Workflow.run()
    execution_order: list[str] = []

    for node_group in metadata.topological_order:
        for node in sorted(node_group, key=lambda item: item.name):
            job = node.job
            dependencies = workflow.jobs[job.name].dependencies
            for dep in dependencies:
                job.append_input(dep.name, dep.get_outputs())
            job.run()
            assert job.status() == JobStatus.FINISHED, (job.name, job.status())
            execution_order.append(job.name)

    outputs = {name: workflow.jobs[name].job.get_outputs() for name in workflow.jobs}
    assert execution_order == ["extract", "transform", "load"], execution_order
    assert outputs["load"]["total"] == 111, outputs
    return {"execution_order": execution_order, "outputs": outputs}


def main() -> int:
    result = run_local_workflow()
    print("[PASS] FedML Workflow local DAG smoke")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
