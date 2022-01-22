from cosapp.ports import Port


class Fluid(Port):
    def setup(self):

        self.add_variable("mass_flow", desc="Mass flow")
        self.add_variable("p", desc="Pressure")
        self.add_variable("T", desc="Temperature")
        self.add_variable("cp", 1004.0, desc="Heat capacity at constant pressure")
