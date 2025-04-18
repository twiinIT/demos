import platform
import subprocess
import time
from multiprocessing import Process, Queue

import psutil


def spin(duration: float):
    """Spin CPU."""
    t0 = time.time()
    while time.time() < t0 + duration:
        pass


def run_spinners(cpu_count: int, duration: float):
    """Apply spin process for each selected CPU processor."""
    processes = [Process(target=spin, args=(duration,)) for _ in range(cpu_count)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()


pipeline = [(run_spinners, (8, 30)), (run_spinners, (1, 30))]


def get_cpu_info(queue: Queue):
    """Assess the platform and collect parameters from running CPU processors."""
    is_mac = platform.system() == "Darwin"
    is_linux = platform.system() == "Linux"

    t0 = time.time()
    while time.time() - t0 < 90:
        usage = psutil.cpu_percent(interval=1)

        if is_mac:
            # Temperature via istats
            try:
                result = subprocess.run(
                    ["istats", "cpu", "--value-only"], capture_output=True, text=True
                )
                output = result.stdout.strip().replace("°C", "").strip()
                temp_val = float(output)
            except ValueError:
                temp_val = None

            # Get fan RPMs via istats
            try:
                result_fan = subprocess.run(
                    ["istats", "fan", "--value-only"], capture_output=True, text=True
                )
                fan_output_lines = result_fan.stdout.strip().splitlines()
                fan_rpms = int(fan_output_lines[1].replace("RPM", "").strip())
            except ValueError:
                fan_rpms = None

        elif is_linux:
            # Temperature via ps_utils
            try:
                temps = psutil.sensors_temperatures()
                temp_val = temps["coretemp"][0].current
            except Exception:
                temp_val = None

            # Fan RPMs via ps_utils
            try:
                fan_rpms = psutil.sensors_fans().popitem()[1][0].current
            except Exception:
                fan_rpms = None

        elapsed = round(time.time() - t0, 3)
        queue.put((elapsed, usage, temp_val, fan_rpms))

    queue.put("DONE")


def run_cpu_monitor(queue: Queue):
    """Run CPU info collection process."""
    process = Process(target=get_cpu_info, args=(queue,))
    process.start()
    return process


def run_pipeline(pipeline):
    """Run each step of pipeline."""
    for func, args in pipeline:
        func(*args)
