import csv
from unittest.mock import MagicMock, patch

from libraries.PerformanceLibrary import PerformanceLibrary


def test_get_container_stats_returns_cpu_and_memory():
    mock_container = MagicMock()

    mock_container.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 2000
            },
            "system_cpu_usage": 10000,
            "online_cpus": 2
        },
        "precpu_stats": {
            "cpu_usage": {
                "total_usage": 1000
            },
            "system_cpu_usage": 8000
        },
        "memory_stats": {
            "usage": 104857600
        }
    }

    mock_client = MagicMock()
    mock_client.containers.get.return_value = mock_container

    with patch("libraries.PerformanceLibrary.docker.from_env", return_value=mock_client):
        library = PerformanceLibrary()
        result = library.get_container_stats("ecu-service")

    assert result["cpu_percent"] == 100.0
    assert result["memory_mb"] == 100.0


@patch("libraries.PerformanceLibrary.docker.from_env")
def test_get_container_stats_zero_system_delta(mock_from_env):
    mock_client = MagicMock()
    mock_container = MagicMock()

    mock_from_env.return_value = mock_client
    mock_client.containers.get.return_value = mock_container

    mock_container.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 2000
            },
            "system_cpu_usage": 8000,
            "online_cpus": 2
        },
        "precpu_stats": {
            "cpu_usage": {
                "total_usage": 1000
            },
            "system_cpu_usage": 8000
        },
        "memory_stats": {
            "usage": 52428800
        }
    }

    library = PerformanceLibrary()

    result = library.get_container_stats("ecu-service")

    assert result["cpu_percent"] == 0.0
    assert result["memory_mb"] == 50.0


@patch("libraries.PerformanceLibrary.docker.from_env")
def test_get_container_stats_without_online_cpus(mock_from_env):
    mock_client = MagicMock()
    mock_container = MagicMock()

    mock_from_env.return_value = mock_client
    mock_client.containers.get.return_value = mock_container

    mock_container.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 3000,
                "percpu_usage": [1000, 1000]
            },
            "system_cpu_usage": 12000
        },
        "precpu_stats": {
            "cpu_usage": {
                "total_usage": 1000
            },
            "system_cpu_usage": 8000
        },
        "memory_stats": {
            "usage": 104857600
        }
    }

    library = PerformanceLibrary()

    result = library.get_container_stats("ecu-service")

    assert result["cpu_percent"] == 100.0
    assert result["memory_mb"] == 100.0


@patch("libraries.PerformanceLibrary.docker.from_env")
def test_measure_container_generates_summary_and_csv(
    mock_from_env,
    tmp_path
):
    mock_client = MagicMock()
    mock_from_env.return_value = mock_client
    library = PerformanceLibrary()

    library.get_container_stats = MagicMock(
        side_effect=[
            {"cpu_percent": 10.0, "memory_mb": 30.0},
            {"cpu_percent": 20.0, "memory_mb": 32.0},
            {"cpu_percent": 30.0, "memory_mb": 34.0},
        ]
    )

    clock = {"now": 0.0}
    csv_file = tmp_path / "measurement.csv"

    def fake_time():
        return clock["now"]

    def fake_sleep(seconds):
        clock["now"] += seconds

    with patch("libraries.PerformanceLibrary.time.time", side_effect=fake_time):
        with patch("libraries.PerformanceLibrary.time.sleep", side_effect=fake_sleep):
            result = library.measure_container(
                "ecu-service",
                duration=3,
                interval=1,
                csv_file=str(csv_file),
            )

    assert result == {
        "cpu_avg": 20.0,
        "cpu_max": 30.0,
        "memory_avg": 32.0,
        "memory_max": 34.0,
        "samples": 3,
        "csv_file": str(csv_file),
    }
    assert library.get_container_stats.call_count == 3

    with csv_file.open(newline="") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {"elapsed_seconds": "0.0", "cpu_percent": "10.0", "memory_mb": "30.0"},
        {"elapsed_seconds": "1.0", "cpu_percent": "20.0", "memory_mb": "32.0"},
        {"elapsed_seconds": "2.0", "cpu_percent": "30.0", "memory_mb": "34.0"},
    ]
