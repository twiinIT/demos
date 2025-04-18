from cosapp.drivers import NonLinearSolver

from cpu.systems import CPUSystem


def run_simulation(queue):
    """Run simulation at each time step collecting live CPU data."""
    cpu = CPUSystem("cpu")
    cpu.add_driver(NonLinearSolver("solver", max_iter=10, factor=1.0, tol=1e-6))
    cpu["exchanger.h_adder"] = 150
    cpu["cpu.heat_capacity"] = 100

    simulation_results = []
    i = 0
    simulated_T = 0.0
    while True:
        data = queue.get()
        if data == "DONE":
            break

        # prepare and run simu
        t, usage, measured_T, fan_rpms = data
        cpu["cpu.usage"] = usage
        cpu["T_cpu"] = simulated_T if i != 0 else measured_T
        cpu.run_drivers()
        # get results

        simulated_T = cpu["cpu.next_T"]
        cpu["cpu.T"] = simulated_T

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
