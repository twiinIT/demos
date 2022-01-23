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
        self.add_inward("T", 0.0, unit="K", desc="Metal temperature")
        self.add_inward("surface", 0.01, unit="m**2", desc="Exchanger surface")
        self.add_inward("cp", 1004.0, unit="J/K/kg", desc="Heat capacity at constant pressure")

        # outputs
        self.add_output(Fluid, "fl_out")
        self.add_outward("h", 20.0, unit="W/K/m**2", desc="Heat conductivity")
        self.add_outward("heat_flow", 0.0, unit="W", desc="Exchanger-to-air heat flow")

        # transient
        self.add_transient("dH", der="heat_flow", desc="Enthalpy delta")

    def compute(self):
        self.h = 10.0 + 300.0 * max(self.fl_in.mass_flow / 1.0, 1.0)
        self.heat_flow = self.h * (self.T - self.fl_in.T) * self.surface

        self.fl_out.mass_flow = self.fl_in.mass_flow
        self.fl_out.T = self.fl_in.T + self.dH / self.cp