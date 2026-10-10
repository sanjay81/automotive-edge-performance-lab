import time
import csv
import docker
import requests
import matplotlib.pyplot as plt


class PerformanceLibrary:

    def __init__(self):
        self.client = docker.from_env()

    def get_container_memory_mb(self, container_name):
        container = self.client.containers.get(container_name)
        stats = container.stats(stream=False)

        memory_usage = stats["memory_stats"]["usage"]

        return round(memory_usage / 1024 / 1024, 2)

    def get_container_cpu_percent(self, container_name):
        container = self.client.containers.get(container_name)
        stats = container.stats(stream=False)

        cpu_stats = stats["cpu_stats"]
        precpu_stats = stats["precpu_stats"]

        cpu_delta = (
            cpu_stats["cpu_usage"]["total_usage"]
            - precpu_stats["cpu_usage"]["total_usage"]
        )

        system_delta = (
            cpu_stats["system_cpu_usage"]
            - precpu_stats["system_cpu_usage"]
        )

        online_cpus = cpu_stats.get("online_cpus")

        if online_cpus is None:
            per_cpu_usage = cpu_stats["cpu_usage"].get(
                "percpu_usage",
                []
            )
            online_cpus = len(per_cpu_usage) if per_cpu_usage else 1

        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (
                cpu_delta / system_delta
            ) * online_cpus * 100
            return round(min(100.0, max(0.0, cpu_percent)), 2)

        return 0.0

    def measure_container(
        self,
        container_name,
        duration=30,
        interval=1,
        csv_file="results/measurement.csv"
    ):

        duration = float(duration)
        interval = float(interval)

        cpu_samples = []
        memory_samples = []

        start_time = time.time()
        end_time = start_time + duration

        with open(csv_file, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "elapsed_seconds",
                "cpu_percent",
                "memory_mb"
            ])

            while time.time() < end_time:

                stats = self.get_container_stats(container_name)
                cpu = stats["cpu_percent"]
                memory = stats["memory_mb"]

                elapsed = round(
                    time.time() - start_time,
                    2
                )

                cpu_samples.append(cpu)
                memory_samples.append(memory)

                writer.writerow([
                    elapsed,
                    cpu,
                    memory
                ])

                print(
                    f"Time={elapsed}s "
                    f"CPU={cpu}% "
                    f"RAM={memory} MB"
                )

                time.sleep(interval)

        result = {
            "cpu_avg": round(
                sum(cpu_samples) / len(cpu_samples),
                2
            ),
            "cpu_max": round(
                max(cpu_samples),
                2
            ),
            "memory_avg": round(
                sum(memory_samples) / len(memory_samples),
                2
            ),
            "memory_max": round(
                max(memory_samples),
                2
            ),
            "samples": len(cpu_samples),
            "csv_file": csv_file
        }

        return result
    
    def generate_graphs(self, csv_file, output_prefix="results/performance"):

        times = []
        cpu_values = []
        memory_values = []

        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)

            for row in reader:
                times.append(
                    float(row["elapsed_seconds"])
                )

                cpu_values.append(
                    float(row["cpu_percent"])
                )

                memory_values.append(
                    float(row["memory_mb"])
                )

        # CPU graph
        plt.figure()

        plt.plot(
            times,
            cpu_values
        )

        plt.xlabel("Time (seconds)")
        plt.ylabel("CPU Usage (%)")
        plt.title("Container CPU Usage")

        plt.grid(True)

        cpu_file = f"{output_prefix}_cpu.png"

        plt.savefig(cpu_file)

        plt.close()

        # Memory graph
        plt.figure()

        plt.plot(
            times,
            memory_values
        )

        plt.xlabel("Time (seconds)")
        plt.ylabel("Memory Usage (MB)")
        plt.title("Container Memory Usage")

        plt.grid(True)

        memory_file = f"{output_prefix}_memory.png"

        plt.savefig(memory_file)

        plt.close()

        return {
            "cpu_graph": cpu_file,
            "memory_graph": memory_file
        }

    def wait_until_service_ready(
        self,
        url,
        timeout=15,
        interval=0.5
    ):
        timeout = float(timeout)
        interval = float(interval)

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    url,
                    timeout=2
                )

                if response.status_code == 200:
                    startup_time = time.time() - start_time
                    return round(startup_time, 2)

            except requests.RequestException:
                pass

            time.sleep(interval)

        raise RuntimeError(
            f"Service did not become ready within {timeout} seconds"
        )


    def measure_container_startup_time(
    self,
    container_name,
    health_url,
    timeout=15
):
        container = self.client.containers.get(container_name)

        if container.status == "running":
            container.stop(timeout=10)

        container.reload()

        if container.status != "exited":
            raise RuntimeError(
                f"Container {container_name} did not stop correctly"
            )

        start_time = time.monotonic()

        container.start()

        timeout = float(timeout)

        while time.monotonic() - start_time < timeout:
            try:
                response = requests.get(
                    health_url,
                    timeout=1
                )

                if response.status_code == 200:
                    return round(
                        time.monotonic() - start_time,
                        2
                    )

            except requests.RequestException:
                pass

            time.sleep(0.2)

        raise RuntimeError(
            f"{container_name} did not become ready within {timeout}s"
        )

    def get_container_stats(self, container_name):
        container = self.client.containers.get(container_name)
        stats = container.stats(stream=False)

        cpu_stats = stats["cpu_stats"]
        precpu_stats = stats["precpu_stats"]

        cpu_delta = (
            cpu_stats["cpu_usage"]["total_usage"]
            - precpu_stats["cpu_usage"]["total_usage"]
        )

        system_delta = (
            cpu_stats["system_cpu_usage"]
            - precpu_stats["system_cpu_usage"]
        )

        online_cpus = cpu_stats.get("online_cpus")

        if online_cpus is None:
            per_cpu_usage = cpu_stats["cpu_usage"].get(
                "percpu_usage",
                []
            )
            online_cpus = len(per_cpu_usage) if per_cpu_usage else 1

        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (
                cpu_delta / system_delta
            ) * online_cpus * 100
        else:
            cpu_percent = 0.0

        cpu_percent = round(min(100.0, max(0.0, cpu_percent)), 2)

        memory_usage = stats["memory_stats"]["usage"]
        memory_mb = memory_usage / 1024 / 1024

        return {
            "cpu_percent": cpu_percent,
            "memory_mb": round(memory_mb, 2)
        }
