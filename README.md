# Automotive Edge Performance & Stability Lab

Robot Framework tests for measuring the ECU service while idle, under rogue
load, during recovery, and across startup and restart cycles.

## Prerequisites

- Docker Desktop or Docker Engine is running.
- Docker Compose v2 is available as `docker compose`.
- Python 3.10 or newer is installed.

## Install Python dependencies

Run these commands from this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the full suite

From this directory, run:

```bash
./scripts/run_suite.sh
```

The script runs all suites in `tests/` and creates a timestamped directory in
`results/` containing Robot Framework's `report.html`, `log.html`, and
`output.xml`, along with the scenario measurements (`idle.csv`, `load.csv`,
`recovery.csv`) and CPU/memory graphs. Each run is kept in its own directory.

To run a single scenario directly, activate `.venv` and pass its test file to
Robot Framework, for example:

```bash
robot tests/idle_state/idle_performance.robot
```

## Scenarios and thresholds

- `idle_state/idle_performance.robot` measures CPU and memory while idle.
- `load/rogue_load.robot` measures ECU CPU and memory under generated load.
- `recovery/recovery.robot` checks resource use after stopping rogue load.
- `startup/startup_time.robot` checks one startup time.
- `stability/restart_stability.robot` checks repeated startup times.

Shared limits are in `config/thresholds.yaml`. Update values there to change
the pass/fail limits used by the suites.

## Continuous integration

GitHub Actions runs the full suite on pushes to `main`, pull requests, and
manual dispatches. Each run uploads its Robot report, CSV measurements, and
graphs as a downloadable workflow artifact.

Each suite starts `ecu-service` and stops any existing rogue load before its
scenario. The load scenario also stops rogue load during test and suite
teardown. To stop and remove the lab containers after a run, use:

```bash
docker compose down
```
