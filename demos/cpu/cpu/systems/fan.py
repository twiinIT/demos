from cosapp.systems import System

from cpu.ports.fluid import Fluid


class Fan(System):
    def setup(self):
        self.add_input(Fluid, "fl_in")
        self.add_inward("tension", 0.0, desc="Input tension")
        self.add_inward("design_tension", 12.0, desc="Fan input tension at design point")
        self.add_inward("cfm", 1.0, desc="Cubic feet per minute")

        self.add_output(Fluid, "fl_out")

    def compute(self):
        self.fl_out.mass_flow = self.cfm * self.tension / self.design_tension
        self.fl_out.T = self.fl_in.T
        self.fl_out.p = self.fl_in.p
