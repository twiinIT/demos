import time
from multiprocessing import Process


def run_cpu_simulation(queue, cpu, duration):
    """Run global simulation as process."""
    process = Process(target=run_simulation, args=(queue, cpu, duration))
    process.start()
    return process


def run_simulation(queue, cpu, duration):
    """Run simulation at each time step collecting live CPU data."""

    simulation_results = []
    i = 0
    simulated_T = 0.0
    t0 = time.time()
    while time.time() < t0 + duration:
        data = queue.get()

        # prepare and run simu
        t, usage, measured_T, fan_rpms = data
        cpu["cpu.usage"] = usage
        cpu["T_cpu"] = simulated_T if i != 0 else measured_T
        cpu.run_drivers()
        # get results

        simulated_T = cpu["cpu.next_T"]
        cpu["cpu.T"] = simulated_T
        i += 1

        print(
            f"[SIM] t={t:.1f}s | \
              usage={usage}% | \
              T_sim={simulated_T:.2f}°C | \
              T_meas={measured_T} | \
              Fan_rpm={fan_rpms}"
        )

        simulation_results.append(
            {
                "time": t,
                "cpu.usage": usage,
                "T_cpu_simulated": simulated_T,
                "T_cpu_measured": measured_T,
                "Fan_rpm_1": fan_rpms,
            }
        )

    queue.put(simulation_results)
