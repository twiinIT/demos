from multiprocessing import Queue

import pandas as pd
from cosapp.drivers import NonLinearSolver

from cpu.systems import CPUSystem
from cpu.utils.cpu_monitor_live import get_pipeline, run_cpu_monitor, run_pipeline
from cpu.utils.monitor_simulation import run_cpu_simulation


def test_cpu_monitoring():
    # set CPU system
    cpu = CPUSystem("cpu")
    cpu.add_driver(NonLinearSolver("solver", max_iter=10, factor=1.0, tol=1e-6))
    cpu["exchanger.h_adder"] = 150
    cpu["cpu.heat_capacity"] = 100

    # set process pipeline
    queue = Queue()
    sequence = {
        "step1": {"nprocs": 8, "duration": 10},
        "step2": {"nprocs": 1, "duration": 10},
    }
    pipeline, duration = get_pipeline(sequence)

    # run pipeline
    sim_process = run_cpu_simulation(queue, cpu, duration)
    monitor_process = run_cpu_monitor(queue, duration)
    run_pipeline(pipeline)
    monitor_process.join()
    sim_process.join()

    # collect data
    assert queue.empty() == False
    results = pd.DataFrame(queue.get())
    assert results.empty == False
