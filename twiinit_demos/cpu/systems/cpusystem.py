from cosapp.systems import System
from twiinit_demos.cpu.systems import CPU, Fan, FanController, HeatExchanger


class CPUSystem(System):
    def setup(self):

        # children
        self.add_child(FanController("controler"))
        self.add_child(Fan("fan"))
        self.add_child(HeatExchanger("exchanger"))
        self.add_child(CPU("cpu"), pulling={"T": "T_cpu"})

        # connections between parent and children
        self.connect(self.inwards, self.exchanger.inwards, ["T_cpu"])
        self.connect(self.inwards, self.controler.inwards, ["T_cpu"])

        # connections between children
        self.connect(self.fan.fl_out, self.exchanger.fl_in)
        self.connect(self.controler.outwards, self.fan.inwards, ["tension"])
        self.connect(self.exchanger.outwards, self.cpu.inwards, ["heat_flow"])

        # design methods
        self.add_design_method("exchanger_surface").add_equation(
            "cpu.heat_flow == cpu.power"
        ).add_unknown("exchanger.surface")
