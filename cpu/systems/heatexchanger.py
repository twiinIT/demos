# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

from cosapp.systems import System

from cpu.ports import FluidPort


class HeatExchanger(System):
    """Compute heatflow extracted by air flow."""

    def setup(self):
        # inputs
        self.add_input(FluidPort, "fl_in")
        self.add_inward("T_cpu", 0.0, unit="degC", desc="CPU temperature")
        self.add_inward("surface", 0.01, unit="m**2", desc="Exchanger surface")
        self.add_inward("thickness", 1e-2, unit="m", desc="Exchanger thickness")
        self.add_inward("density", 1.2, unit="kg/m**3", desc="Exchanger thickness")
        self.add_inward(
            "cp", 1004.0, unit="J/(K*kg)", desc="Specific heat capacity of air at constant pressure"
        )
        self.add_inward(
            "h_natural", 10.0, unit="W/(K*m**2)", desc="Natural heat transfer coefficient"
        )
        self.add_inward(
            "h_forced", 100.0, unit="W/(K*m**2)", desc="Forced heat transfer coefficient"
        )
        self.add_inward("h_adder", 0.0, unit="W/(K*m**2)", desc="Adder heat transfer coefficient")
        self.add_inward("max_mass_flow", 1.0, unit="kg/s", desc="Maximum air mass flow")

        # outputs
        self.add_output(FluidPort, "fl_out")
        self.add_outward("heat_flow", 0.0, unit="W", desc="Exchanger-to-air heat flow")
        self.add_outward("h", 100.0, unit="W/(K*m**2)", desc="Total heat transfer coefficient")

        self.add_transient("heat", der="heat_flow")

    def compute(self):
        self.h = (
            self.h_natural
            + self.h_forced * min(self.fl_in.mass_flow / self.max_mass_flow, 1.0)
            + self.h_adder
        )
        self.heat_flow = self.h * (self.T_cpu - self.fl_in.T) * self.surface

        self.fl_out.mass_flow = self.fl_in.mass_flow
        mass = self.density * self.surface * self.thickness
        self.fl_out.T = self.fl_in.T + self.heat / (self.cp * mass)
