import csv
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


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
    """Return suite-level pass/fail counts from Robot Framework output.xml."""
    root = ET.parse(output_xml).getroot()
    stats = root.find(".//statistics/total/stat")
    if stats is None:
        raise ValueError(f"Robot total statistics not found in {output_xml}")

    return {
        "total": int(stats.get("pass", 0)) + int(stats.get("fail", 0)),
        "passed": int(stats.get("pass", 0)),
        "failed": int(stats.get("fail", 0)),
        "status": stats.get("status"),
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
