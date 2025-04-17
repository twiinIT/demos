import time
import psutil
import subprocess
from multiprocessing import Process, Queue


def spin(duration: float):
    t0 = time.time()
    while time.time() < t0 + duration:
        pass


def run_spinners(cpu_count: int, duration: float):
    processes = [Process(target=spin, args=(duration,)) for _ in range(cpu_count)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()


pipeline = [(run_spinners, (8, 300)), (run_spinners, (1, 300)), (run_spinners, (8, 300))]


def get_cpu_info(queue: Queue):
    t0 = time.time()
    while time.time() - t0 < 900:
        usage = psutil.cpu_percent(interval=1)
        result = subprocess.run(["istats", "cpu", "--value-only"], capture_output=True, text=True)
        output = result.stdout.strip().replace("°C", "").strip()
        try:
            temp_val = float(output)
        except ValueError:
            temp_val = None
        # Get fan RPMs
        result_fan = subprocess.run(
            ["istats", "fan", "--value-only"], capture_output=True, text=True
        )
        fan_output_lines = result_fan.stdout.strip().splitlines()
        # Parse first valid fan RPM
        fan_rpms = []
        for line in fan_output_lines:
            try:
                val = int(line.replace("RPM", "").strip())
                fan_rpms.append(val)
            except ValueError:
                fan_rpms = None

        elapsed = round(time.time() - t0, 3)
        queue.put((elapsed, usage, temp_val, fan_rpms))

    queue.put("DONE")


def run_cpu_monitor(queue: Queue):
    process = Process(target=get_cpu_info, args=(queue,))
    process.start()
    return process


def run_pipeline(pipeline):
    for func, args in pipeline:
        func(*args)
