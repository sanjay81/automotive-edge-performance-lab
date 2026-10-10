# Embedded Performance Load Lab

[![Embedded Performance Load Lab CI](https://github.com/sanjay81/embedded-performance-load-lab/actions/workflows/performance-lab.yml/badge.svg)](https://github.com/sanjay81/embedded-performance-load-lab/actions/workflows/performance-lab.yml)

A clean-room **embedded performance-testing POC** built with Robot Framework, Python, Docker and GitHub Actions. It demonstrates how a repeatable test framework can measure an ECU-style service's resource behaviour while idle, under synthetic load, during recovery, and across startup/restart cycles.

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
- Optional AI-assisted analysis of run summaries and validation results.

This is intentionally a **small, reproducible laboratory**, not a claim to reproduce a production HIL/vehicle environment. The service and load are synthetic so the performance-test framework can be demonstrated publicly without proprietary code or data.

## Test flow

```text
GitHub Actions / Local Runner
            |
            v
 Robot Framework scenarios
       |                 \
       v                  v
Python measurement    Docker Compose lifecycle
library                    |
       |                   v
       +<---------- Docker test environment
                    |                  |
             ECU-style service    Rogue load
       |
       v
CSV + graphs + Robot reports (HTML/XML)
       |
       | Optional, manually run analysis
       v
run_summary.json
       |
       v
AI analyzer (requires OPENAI_API_KEY)
       |
       v
ai_analysis.json (findings + next-test recommendation)
```

The Robot Framework suite and its configured thresholds determine test
pass/fail. The AI analyzer is an optional follow-up: it interprets a generated
run summary and does not replace or change the deterministic test results.

## Scenarios

| Scenario | Purpose |
|---|---|
| Idle performance | Measure CPU and memory while the ECU-style service is idle |
| Rogue load | Observe resource behaviour while synthetic background load is active |
| Recovery | Apply and measure high load, stop the load, then verify resource usage settles |
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

## Run unit tests

The unit tests verify the performance library's calculations and CSV output,
and check that all configured thresholds are present and valid. They use
mocks, so they do not require Docker:

```bash
.venv/bin/pytest -q unit_tests
```

## Run the complete suite

```bash
./scripts/run_suite.sh
```

The rogue-load scenario supports three configurable concurrency profiles. The
default is `medium`; select another profile by passing it to the runner:

```bash
./scripts/run_suite.sh low
./scripts/run_suite.sh medium
./scripts/run_suite.sh high
```

Profile worker counts and minimum CPU expectations are in
`config/load_profiles.yaml`. The defaults are 1, 2, and 4 concurrent request
workers for low, medium, and high. The load scenario records the selected
profile in the Robot log and saves profile-specific measurements and graphs
such as `load-low.csv` and `load-low_cpu.png`.

Each run creates a timestamped directory in `results/` containing:

- `report.html`
- `log.html`
- `output.xml`
- scenario CSV measurements such as `idle.csv`, `load.csv`, and `recovery.csv`
- generated CPU and memory graphs

## Optional AI analysis

After a test run, build a machine-readable summary from its measurements and
Robot results:

```bash
python ai_agent/build_run_summary.py results/run-<timestamp>
```

The resulting `run_summary.json` contains the scenario measurements and, when
`output.xml` is present, Robot's total, passed, failed, skipped, and overall
status, individual test outcomes and failure messages, plus measured startup
times and restart-cycle results. This gives the analyzer the actual Robot
startup/restart decisions alongside the CSV metrics. Analyze it with the
optional AI helper:

```bash
python ai_agent/analyze_run.py results/run-<timestamp>/run_summary.json
```

The analyzer sends the summary and configured thresholds to the model API,
validates its JSON response, and saves the findings and recommendation as
`ai_analysis.json` beside the summary. Set `OPENAI_API_KEY` in the project-root
`.env` file or export it in your shell before running the analyzer. Keep the key
private; do not commit it. For example, analyze the committed reference summary
with:

```bash
python ai_agent/analyze_run.py ai_agent/examples/reference_run_summary.json
```

Run the evaluation cases from the project root with:

```bash
python -m ai_agent.evaluate_agent
```

The evaluation command also calls the model API and requires `OPENAI_API_KEY`.
Without a provider API key, a clone can inspect the evaluation cases and their
reference labels but cannot reproduce model evaluation or generate an AI
analysis. The OpenAI client dependency is installed through `requirements.txt`.

### AI evaluation cases

The evaluation set contains seven synthetic JSON cases. Each case has
human-authored expected `status` and `recommended_next_test` labels. A case
counts as a match only when the model output matches **both** labels.

| Case | Expected status | Expected next test |
|---|---|---|
| `high_cpu` | Anomaly | Recovery |
| `idle_cpu_over_limit` | Anomaly | None |
| `healthy_high_load` | Normal | None |
| `load_below_minimum` | Warning | Load medium |
| `normal_run` | Normal | None |
| `recovery_failure` | Anomaly | Restart stability |
| `recovery_success` | Normal | None |

These fixtures check behavior against a small labeled example set; they are
not a statistical benchmark or a guarantee of model performance. Results can
vary with model/API changes. The evaluation script writes its latest result to
`ai_agent/evaluation_results.json` (ignored by Git); no pass-rate claim should
be interpreted without the corresponding recorded evaluation run.

### Sample output

[`ai_agent/examples/reference_run_summary.json`](ai_agent/examples/reference_run_summary.json)
is a committed summary generated from a passing local Robot run and its CSV
measurements. It lets readers inspect the machine-readable input without
running the suite. There is no committed `ai_analysis.json`: that file is
generated by a live model call, requires an API key, and may vary between runs.

To execute a single Robot Framework scenario:

```bash
robot tests/idle_state/idle_performance.robot
```

## Continuous integration

GitHub Actions runs the unit tests first, then the Docker-backed Robot Framework
suite on pushes to `main`, pull requests, and manual dispatches. CI uploads the
Robot reports, CSV measurements, and graphs as workflow artifacts. The optional
summary-building and AI-analysis steps are not part of CI and do not gate the
workflow. One historical run at `results/run-20261007-125142/` is retained in
Git as a run-artifact snapshot; it predates the current measurement changes and
is not a current performance baseline. New generated output under `results/`,
including summaries and AI analyses, is ignored by Git.

## Test isolation and cleanup

Each suite prepares the ECU-style service and removes any existing rogue load before its scenario. The load suite also removes the synthetic load during test/suite teardown.

To stop and remove the lab containers manually:

```bash
docker compose down
```

## Engineering intent

This POC is designed to show the **testing framework itself**: repeatable setup, measurement, threshold evaluation, reporting, and CI execution. A production automotive implementation would replace the synthetic service/load with real target services, HIL/rig interfaces, device diagnostics, vehicle-network traffic, and project-specific performance requirements.

## Known limitations

- CPU and memory readings are container-level measurements and can vary with
  host load, scheduling, and Docker/runtime configuration. They do not
  represent target ECU measurements or prove real-time behavior.
- The current suite does not measure request latency, jitter, or missed
  deadlines, and therefore cannot validate timing guarantees.
- The service and generated load are synthetic; there is no HIL, physical ECU,
  or vehicle-network integration.
- Long-duration soak testing and automated trend comparison across CI runs are
  not implemented.
- AI analysis and its evaluation are manual, require an external model API key,
  and are not part of CI. Model output and evaluation scores may change across
  model/API versions.

## Future extensions

Potential next steps include:

1. Measure request latency, jitter, and deadline misses in the synthetic service.
2. Add explicit CPU/RAM container quota tests.
3. Add long-duration idle and load stability runs.
4. Add reboot/power-cycle orchestration and network-load replay.
5. Add diagnostic/log assertions and CI trend comparison.

---

**Primary technologies:** Python · Robot Framework · Docker · Linux · GitHub Actions · Performance Testing · Embedded Test Automation
