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


def load_profiles():
    config_file = (
        Path(__file__).parent.parent
        / "config"
        / "load_profiles.yaml"
    )

    with open(config_file, "r") as file:
        return yaml.safe_load(file)["load_profiles"]


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
    assert "max_cpu_avg" in thresholds["load"]
    assert "max_memory_mb" in thresholds["load"]
    assert "min_cpu_avg" not in thresholds["load"]
    assert thresholds["load"]["max_cpu_avg"] == 100


def test_recovery_thresholds_exist():
    thresholds = load_thresholds()

    assert "recovery" in thresholds
    assert "max_cpu_avg" in thresholds["recovery"]
    assert "max_memory_mb" in thresholds["recovery"]


def test_startup_thresholds_exist():
    thresholds = load_thresholds()

    assert "startup" in thresholds
    assert "max_seconds" in thresholds["startup"]


def test_threshold_values_are_positive():
    thresholds = load_thresholds()

    for scenario, limits in thresholds.items():
        assert isinstance(limits, dict), scenario
        for name, value in limits.items():
            assert isinstance(value, (int, float)), f"{scenario}.{name} must be numeric"
            assert value > 0, f"{scenario}.{name} must be positive"


def test_cpu_threshold_ranges_are_ordered():
    thresholds = load_thresholds()

    assert thresholds["idle"]["max_cpu_avg"] <= thresholds["idle"]["max_cpu_peak"]
    assert thresholds["load"]["max_cpu_avg"] == 100


def test_load_profiles_are_configured():
    profiles = load_profiles()

    assert set(profiles) == {"low", "medium", "high"}
    assert [profiles[name]["workers"] for name in ("low", "medium", "high")] == [1, 2, 4]
    for name, profile in profiles.items():
        assert profile["workers"] > 0, name
        assert profile["min_cpu_avg"] > 0, name
