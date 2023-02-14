from cosapp.systems import System

from twiinit_demos.cpu.ports.fluid import Fluid


class HeatExchanger(System):
    """
    Compute heatflow extracted by air flow
    """

    def setup(self):
        # inputs
        self.add_input(Fluid, "fl_in")
        self.add_inward("T_cpu", 0.0, unit="degC", desc="CPU temperature")
        self.add_inward("surface", 0.01, unit="m**2", desc="Exchanger surface")
        self.add_inward(
            "cp", 1004.0, unit="J/K/kg", desc="Heat capacity of air at constant pressure"
        )
        self.add_inward("h_natural", 110.0, unit="J/K/kg", desc="Heat natural conductivity")
        self.add_inward("h_forced", 200.0, unit="J/K/kg", desc="Heat forced conductivity")
        self.add_inward("h_adder", 0.0, unit="J/K/kg", desc="Heat conductivity adder")
        self.add_inward("max_mass_flow", 1.0, unit="kg/s", desc="Maximum air mass flow")

        # outputs
        self.add_output(Fluid, "fl_out")
        self.add_outward("heat_flow", 0.0, unit="W", desc="Exchanger-to-air heat flow")
        self.add_outward("h", 310.0, unit="W/K/m**2", desc="Heat conductivity")

    def compute(self):
        self.h = (
            self.h_natural
            + self.h_forced * min(self.fl_in.mass_flow / self.max_mass_flow, 1.0)
            + self.h_adder
        )
        self.heat_flow = self.h * (self.T_cpu - self.fl_in.T) * self.surface

        self.fl_out.mass_flow = self.fl_in.mass_flow
        self.fl_out.T = self.fl_in.T + self.heat_flow / self.cp
