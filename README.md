# Automotive Edge Performance & Stability Lab

[![Performance Lab CI](https://github.com/sanjay81/automotive-edge-performance-lab/actions/workflows/performance-lab.yml/badge.svg)](https://github.com/sanjay81/automotive-edge-performance-lab/actions/workflows/performance-lab.yml)

A clean-room **embedded/automotive performance-testing POC** built with Robot Framework, Python, Docker and GitHub Actions. It demonstrates how a repeatable test framework can measure ECU-service resource behaviour while idle, under synthetic load, during recovery, and across startup/restart cycles.

> **Portfolio focus:** Embedded test automation · performance validation · CI/CD · containerized test environments · measurable pass/fail thresholds

## What this project demonstrates

- Automated CPU and memory measurement for an ECU-style service.
- Synthetic rogue/background load generation.
- Recovery checks after load is removed.
- Startup-time measurement and repeated restart stability checks.
- Centralized thresholds in YAML for deterministic pass/fail decisions.
- Robot Framework reports plus CSV measurement artifacts.
- Automatically generated CPU/memory graphs.
- Repeatable execution in GitHub Actions.
- Per-run result directories so measurements remain traceable.

This is intentionally a **small, reproducible laboratory**, not a claim to reproduce a production HIL/vehicle environment. The service and load are synthetic so the performance-test framework can be demonstrated publicly without proprietary code or data.

## Test flow

```text
GitHub Actions / Local Runner
            |
            v
     Robot Framework
            |
            v
 Python measurement libraries
            |
            v
 Docker test environment
     |               |
 ECU-style service   Rogue load
     |
     v
 CSV + graphs + Robot reports
```

## Scenarios

| Scenario | Purpose |
|---|---|
| Idle performance | Measure CPU and memory while the ECU-style service is idle |
| Rogue load | Observe resource behaviour while synthetic background load is active |
| Recovery | Verify resource usage settles after the load is removed |
| Startup | Measure service startup time |
| Restart stability | Repeat startup measurement across multiple restart cycles |

Shared pass/fail limits live in `config/thresholds.yaml`.

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2 available as `docker compose`
- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the complete suite

```bash
./scripts/run_suite.sh
```

Each run creates a timestamped directory in `results/` containing:

- `report.html`
- `log.html`
- `output.xml`
- scenario CSV measurements such as `idle.csv`, `load.csv`, and `recovery.csv`
- generated CPU and memory graphs

To execute a single Robot Framework scenario:

```bash
robot tests/idle_state/idle_performance.robot
```

## Continuous integration

GitHub Actions executes the test suite on pushes to `main`, pull requests, and manual dispatches. CI uploads Robot Framework results, CSV measurements, and graphs as workflow artifacts.

## Test isolation and cleanup

Each suite prepares the ECU-style service and removes any existing rogue load before its scenario. The load suite also removes the synthetic load during test/suite teardown.

To stop and remove the lab containers manually:

```bash
docker compose down
```

## Engineering intent

This POC is designed to show the **testing framework itself**: repeatable setup, measurement, threshold evaluation, reporting, and CI execution. A production automotive implementation would replace the synthetic service/load with real target services, HIL/rig interfaces, device diagnostics, vehicle-network traffic, and project-specific performance requirements.

## Next extensions

Useful next steps include:

1. Explicit CPU/RAM container quota tests.
2. Long-duration idle and load stability runs.
3. Reboot/power-cycle orchestration.
4. Network-load scenarios such as replayed traffic.
5. More diagnostic/log assertions alongside resource measurements.
6. Trend comparison between CI runs.

---

**Primary technologies:** Python · Robot Framework · Docker · Linux · GitHub Actions · Performance Testing · Embedded Test Automation
