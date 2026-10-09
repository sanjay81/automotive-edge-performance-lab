import csv
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


STARTUP_TIME_PATTERNS = (
    re.compile(r"ECU startup time:\s*([\d.]+)\s*seconds", re.IGNORECASE),
    re.compile(r"Startup time cycle\s+\d+:\s*([\d.]+)\s*seconds", re.IGNORECASE),
)


def read_measurement(csv_file):
    rows = []

    with open(csv_file, newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append({
                "elapsed_seconds": float(row["elapsed_seconds"]),
                "cpu_percent": float(row["cpu_percent"]),
                "memory_mb": float(row["memory_mb"]),
            })

    if not rows:
        return None

    cpu_values = [row["cpu_percent"] for row in rows]
    memory_values = [row["memory_mb"] for row in rows]

    return {
        "samples": len(rows),

        "cpu": {
            "average": round(
                sum(cpu_values) / len(cpu_values),
                2
            ),
            "maximum": round(max(cpu_values), 2),
            "minimum": round(min(cpu_values), 2),
        },

        "memory": {
            "average_mb": round(
                sum(memory_values) / len(memory_values),
                2
            ),
            "maximum_mb": round(max(memory_values), 2),
            "minimum_mb": round(min(memory_values), 2),
        },

        "duration_seconds": round(
            rows[-1]["elapsed_seconds"],
            2
        ),
    }


def read_robot_results(output_xml):
    """Return test outcomes and startup measurements from Robot output.xml."""
    root = ET.parse(output_xml).getroot()
    stats = root.find(".//statistics/total/stat")
    if stats is None:
        raise ValueError(f"Robot total statistics not found in {output_xml}")

    passed = int(stats.get("pass", 0))
    failed = int(stats.get("fail", 0))
    skipped = int(stats.get("skip", 0))
    suite_status = root.find("./suite/status")
    test_outcomes = []
    startup_results = []
    restart_results = []

    for test in root.findall(".//test"):
        status_element = test.find("status")
        if status_element is None:
            continue

        name = test.get("name", "")
        outcome = {
            "name": name,
            "status": status_element.get("status"),
            "elapsed_seconds": round(float(status_element.get("elapsed", 0)), 3),
        }
        failure_messages = [
            (message.text or "").strip()
            for message in test.iter("msg")
            if message.get("level") == "FAIL" and (message.text or "").strip()
        ]
        if failure_messages:
            outcome["failure_messages"] = failure_messages
        test_outcomes.append(outcome)

        measurements = []
        for message in test.iter("msg"):
            text = message.text or ""
            for pattern in STARTUP_TIME_PATTERNS:
                measurements.extend(float(match) for match in pattern.findall(text))

        name_lower = name.lower()
        if "startup" in name_lower:
            startup_results.append({
                **outcome,
                "measured_startup_seconds": measurements,
            })
        if "restart" in name_lower:
            restart_results.append({
                **outcome,
                "measured_startup_seconds": measurements,
                "restart_cycles": len(measurements),
            })

    return {
        "total": passed + failed + skipped,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "status": (
            suite_status.get("status")
            if suite_status is not None
            else ("FAIL" if failed else "PASS" if passed else "SKIP")
        ),
        "tests": test_outcomes,
        "startup_results": startup_results,
        "restart_stability_results": restart_results,
    }


def build_summary(results_dir):
    results_path = Path(results_dir)

    summary = {
        "run_id": results_path.name,
        "scenarios": {}
    }

    output_xml = results_path / "output.xml"
    if output_xml.exists():
        summary["robot_results"] = read_robot_results(output_xml)

    for csv_file in results_path.glob("*.csv"):

        scenario_name = csv_file.stem

        measurement = read_measurement(csv_file)

        if measurement:
            summary["scenarios"][scenario_name] = measurement

    output_file = results_path / "run_summary.json"

    with open(output_file, "w") as file:
        json.dump(
            summary,
            file,
            indent=2
        )

    print(f"Created: {output_file}")

    return output_file


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python ai_agent/build_run_summary.py "
            "<results-directory>"
        )
        sys.exit(1)

    build_summary(sys.argv[1])
