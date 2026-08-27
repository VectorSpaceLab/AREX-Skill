# Notebook, Spin, and Deployer Bridge Notes

## Notebook APIs

Metaflow exports `NBRunner`, `NBDeployer`, and `NBDeployer`-related objects in supported Python versions. Use them when a notebook session needs similar behavior to `Runner`/`Deployer` without treating the notebook itself as a simple command-line flow file. Keep notebook kernels and UI display concerns outside headless smoke scripts.

## Spin

Spin-related APIs let a task from a previous run be spun up locally through a flow script's `spin` command or programmatic runner surface. Spin support has its own metadata/datastore mode and allowed decorator list. Use it for focused task replay, not as a substitute for ordinary `resume` or production deployment.

## Deployer bridge

`Deployer(flow_file, ...)` mirrors the top-level flow-script options and injects provider methods from available deployer implementations. In this version, provider bridge surfaces include Argo Workflows and AWS Step Functions object types. Real deployment requires provider configuration, credentials, datastore roots, and service availability; read `deployment-orchestration` before creating or triggering production workflows.
