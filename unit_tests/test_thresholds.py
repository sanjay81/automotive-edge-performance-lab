from pathlib import Path
import yaml


def load_thresholds():
    config_file = (
        Path(__file__).parent.parent
        / "config"
        / "thresholds.yaml"
    )

    with open(config_file, "r") as file:
        return yaml.safe_load(file)


def test_threshold_file_loads():
    thresholds = load_thresholds()

    assert thresholds is not None
    assert isinstance(thresholds, dict)


def test_idle_thresholds_exist():
    thresholds = load_thresholds()

    assert "idle" in thresholds
    assert "max_cpu_avg" in thresholds["idle"]
    assert "max_memory_mb" in thresholds["idle"]


def test_load_thresholds_exist():
    thresholds = load_thresholds()

    assert "load" in thresholds
    assert "min_cpu_avg" in thresholds["load"]
    assert "max_cpu_avg" in thresholds["load"]
    assert "max_memory_mb" in thresholds["load"]


def test_threshold_values_are_positive():
    thresholds = load_thresholds()

    assert thresholds["idle"]["max_cpu_avg"] > 0
    assert thresholds["idle"]["max_memory_mb"] > 0

    assert thresholds["load"]["min_cpu_avg"] > 0
    assert thresholds["load"]["max_cpu_avg"] > 0