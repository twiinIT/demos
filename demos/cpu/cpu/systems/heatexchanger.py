import imp
from cosapp.systems import System

from cpu.ports.fluid import Fluid


class HeatExchanger(System):
    """
    Compute heatflux extracted by air flow
    """

    def setup(self):
        # inputs
        self.add_input(Fluid, "fl_in")
        self.add_inward("T_cpu", 0.0, unit="degC", desc="CPU temperature")
        self.add_inward("surface", 0.01, unit="m**2", desc="Exchanger surface")
        self.add_inward("cp", 1004.0, unit="J/K/kg", desc="Heat capacity of Air at constant pressure")
        self.add_inward("h", 310.0, unit="W/K/m**2", desc="Heat conductivity")

        # outputs
        self.add_output(Fluid, "fl_out")
        self.add_outward("heat_flow", 0.0, unit="W", desc="Exchanger-to-air heat flow")

    def compute(self):
        self.heat_flow = self.h * (self.T_cpu - self.fl_in.T) \
            * self.surface * self.fl_in.mass_flow ** 2

        self.fl_out.mass_flow = self.fl_in.mass_flow
        self.fl_out.T = self.fl_in.T + self.heat_flow / self.cp
