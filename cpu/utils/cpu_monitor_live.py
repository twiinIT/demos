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


def run_pipeline(pipeline):
    """Run each step of pipeline."""
    for func, args in pipeline:
        func(*args)


def get_mac_temperature():
    result = subprocess.run(["istats", "cpu", "--value-only"], capture_output=True, text=True)
    output = result.stdout.strip().replace("°C", "").strip()
    return float(output)


def get_linux_temperature():
    temps = psutil.sensors_temperatures()
    return temps["coretemp"][0].current


def get_mac_fan_speed():
    result_fan = subprocess.run(["istats", "fan", "--value-only"], capture_output=True, text=True)
    fan_output_lines = result_fan.stdout.strip().splitlines()
    fan_rpms = int(fan_output_lines[1].replace("RPM", "").strip())
    return fan_rpms


def get_linux_fan_speed():
    return psutil.sensors_fans().popitem()[1][0].current


def get_cpu_info(queue: Queue, duration: float):
    """Assess the platform and collect parameters from running CPU processors."""
    is_mac = platform.system() == "Darwin"
    is_linux = platform.system() == "Linux"

    t0 = time.time()
    while time.time() < t0 + duration:
        # get usage info
        usage = psutil.cpu_percent(interval=1)

        # get temperature info
        try:
            if is_mac:
                temp_val = get_mac_temperature()
            elif is_linux:
                temp_val = get_linux_temperature()
        except Exception:
            temp_val = None

        # get fan info
        try:
            if is_mac:
                fan_rpms = get_mac_fan_speed()
            elif is_linux:
                fan_rpms = get_linux_fan_speed()
        except Exception:
            fan_rpms = None

        elapsed = round(time.time() - t0, 3)
        queue.put((elapsed, usage, temp_val, fan_rpms))


def run_cpu_monitor(queue: Queue, duration: float):
    """Run CPU info collection process."""
    process = Process(target=get_cpu_info, args=(queue, duration))
    process.start()
    return process


def get_pipeline(sequence):
    pipeline = []
    total_duration = 0.0
    for step in sequence.values():
        nprocs = step["nprocs"]
        duration = step["duration"]
        pipeline.append((run_spinners, (nprocs, duration)))
        total_duration += duration
    return pipeline, total_duration
